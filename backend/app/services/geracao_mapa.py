"""Geração do mapa de faturamento por cliente/competência: aplica De/Para,
segmenta, casa com as regras de segmentação e monta o `.xlsx` final (abas MENSAL
+ MAPA, sem macro), equivalente ao `MODELO MAPA.xlsm` de hoje.

Fórmula validada linha a linha contra a base real (ver docs/plano.md):
  - cada verba real (código numérico/alfanumérico da DS) soma no evento/grupo do
    seu De/Para (Salario, Beneficios, Despesas Extras, Insumos, Outros,
    Backoffice, Taxa de antecipação, ...)
  - Encargos, FEE e Impostos NÃO vêm de um código de verba — são a soma das
    colunas ENCARGOS/TAXA/TRIBUTOS da DS por colaborador (por isso têm um
    "verba_codigo" sintético como 'Encargos'/'FEE'/'Impostos' no De/Para, que
    nunca bate com um código real e é tratado à parte aqui)
  - Subtotal = soma de todos os grupos "normais" (inclui Encargos)
  - Total = Subtotal + FEE + Impostos

Limitação conhecida: REEMBOLSO é armazenado mas não usado na fórmula (nenhum
exemplo observado com valor != 0 para validar seu papel); CPF e CC Cliente das
`campos_cadastrais_mapa` ainda não têm campo correspondente no lançamento
normalizado — ficam de fora do mapa até serem adicionados à ingestão.
"""

import os
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

import openpyxl
from openpyxl.styles import Font
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.cliente import Cliente
from app.models.de_para import CampoCadastralMapa, DeParaVerba
from app.models.enums import ComparadorCondicao, LogicaRegra, StatusMapaGerado
from app.models.lancamento import LancamentoVerba
from app.models.mapa import MapaGerado
from app.models.regra import RegraCondicao, RegraSegmentacao

CAMPO_CADASTRAL_ATRIBUTO = {
    "Filial": "filial",
    "Matricula": "matricula",
    "Colaborador": "colaborador",
    "CNPJ": "cnpj",
    "Cargo": "cargo",
    "Dt Admissão": "dt_admissao",
    "Dt Demissão": "dt_demissao",
    "Situação": "situacao_folha",
}

ATRIBUTO_PARA_CAMPO_LANCAMENTO = {
    "COLABORADOR": "colaborador",
    "CNPJ": "cnpj",
    "CC": "cc",
    "CARGO": "cargo",
}

GRUPOS_SINTETICOS = {"Encargos", "FEE", "Impostos", "Subtotal", "Total"}

ORDEM_ENCARGOS = (2, 2001, "Encargos")
ORDEM_SUBTOTAL = (99, 99001, "Subtotal")
ORDEM_FEE = (100, 100001, "FEE")
ORDEM_IMPOSTOS = (101, 101001, "Impostos")
ORDEM_TOTAL = (102, 102001, "Total")


@dataclass
class ResultadoSegmento:
    regra: RegraSegmentacao | None  # None = bucket GERAL (cliente sem nenhuma regra)
    linhas_colaborador: dict  # matricula -> {campo_cadastral: valor}
    valores_por_colaborador: dict  # matricula -> {evento: Decimal}
    eventos_ordenados: list  # [(ordem_grupo, ordem_item, grupo, evento)]
    totais_por_grupo: dict  # grupo -> Decimal (somado entre colaboradores)
    verbas_fora_de_para: set
    grand_total: dict  # evento -> Decimal (linha de totais no fim da planilha)


class SegmentacaoNaoSuportada(Exception):
    pass


def _resolver_atributo(linha: LancamentoVerba, atributo: str) -> str | None:
    campo = ATRIBUTO_PARA_CAMPO_LANCAMENTO.get(atributo)
    if campo is None:
        raise SegmentacaoNaoSuportada(
            f"Atributo de segmentação '{atributo}' ainda não é suportado pelo gerador "
            "(hoje só COLABORADOR, CNPJ, CC, CARGO — SRA/CTT ainda não estão integrados)."
        )
    valor = getattr(linha, campo)
    return valor.strip() if isinstance(valor, str) else valor


def _condicao_bate(linha: LancamentoVerba, condicao: RegraCondicao) -> bool:
    """Avalia uma condição contra os dados do colaborador.

    Comparação sempre normalizada (maiúsculas e sem espaços nas pontas), porque os
    valores vêm digitados à mão no cadastro e da folha com padding. Atributo nulo
    no lançamento vira "" — então DIFERENTE bate (um cargo vazio é de fato
    diferente de "OPERADOR") e IGUAL/CONTEM não batem.
    """
    valor_linha = (_resolver_atributo(linha, condicao.atributo) or "").strip().upper()
    valor_regra = (condicao.valor or "").strip().upper()

    if condicao.comparador == ComparadorCondicao.IGUAL:
        return valor_linha == valor_regra
    if condicao.comparador == ComparadorCondicao.CONTEM:
        return valor_regra in valor_linha
    if condicao.comparador == ComparadorCondicao.DIFERENTE:
        return valor_linha != valor_regra
    raise SegmentacaoNaoSuportada(f"Comparador '{condicao.comparador}' não implementado")


def _regra_bate(linha: LancamentoVerba, regra: RegraSegmentacao) -> bool:
    if not regra.condicoes:
        # A API exige ao menos uma condição; se chegou aqui sem nenhuma, é dado
        # legado/inconsistente — não bater é mais seguro que virar um "pega tudo".
        return False
    resultados = (_condicao_bate(linha, c) for c in regra.condicoes)
    return all(resultados) if regra.logica == LogicaRegra.E else any(resultados)


def _decimal(v) -> Decimal:
    return v if isinstance(v, Decimal) else Decimal(str(v or 0))


def _montar_segmento(
    linhas: list[LancamentoVerba],
    de_para_por_codigo: dict[str, DeParaVerba],
    regra: RegraSegmentacao | None,
) -> ResultadoSegmento:
    valores_por_colaborador: dict[str, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    cadastro_por_colaborador: dict[str, dict] = {}
    ordem_por_evento: dict[str, tuple] = {}
    verbas_fora_de_para: set[str] = set()

    for linha in linhas:
        chave_colaborador = linha.matricula or linha.colaborador or "SEM_MATRICULA"
        if chave_colaborador not in cadastro_por_colaborador:
            cadastro_por_colaborador[chave_colaborador] = {
                campo: getattr(linha, atributo) for campo, atributo in CAMPO_CADASTRAL_ATRIBUTO.items()
            }

        item_de_para = de_para_por_codigo.get(linha.verba_codigo)
        if item_de_para is None:
            verbas_fora_de_para.add(linha.verba_codigo)
        else:
            valores_por_colaborador[chave_colaborador][item_de_para.evento_exibicao] += _decimal(linha.valor)
            ordem_por_evento[item_de_para.evento_exibicao] = (
                item_de_para.ordem_grupo,
                item_de_para.ordem_item,
                item_de_para.grupo,
                item_de_para.evento_exibicao,
            )

        if _decimal(linha.encargos):
            valores_por_colaborador[chave_colaborador]["Encargos"] += _decimal(linha.encargos)
            ordem_por_evento["Encargos"] = (*ORDEM_ENCARGOS, "Encargos")
        if _decimal(linha.taxa):
            valores_por_colaborador[chave_colaborador]["Fee"] += _decimal(linha.taxa)
            ordem_por_evento["Fee"] = (*ORDEM_FEE, "Fee")
        if _decimal(linha.tributos):
            valores_por_colaborador[chave_colaborador]["Impostos"] += _decimal(linha.tributos)
            ordem_por_evento["Impostos"] = (*ORDEM_IMPOSTOS, "Impostos")

    eventos_ordenados = sorted(ordem_por_evento.values())

    totais_por_grupo: dict[str, Decimal] = defaultdict(Decimal)
    for eventos_colaborador in valores_por_colaborador.values():
        subtotal_colaborador = Decimal("0")
        for evento, valor in eventos_colaborador.items():
            grupo = next(g for (_, _, g, e) in eventos_ordenados if e == evento)
            if grupo not in ("FEE", "Impostos"):
                subtotal_colaborador += valor
            totais_por_grupo[grupo] += valor
        eventos_colaborador["Subtotal"] = subtotal_colaborador
        eventos_colaborador["Total"] = (
            subtotal_colaborador + eventos_colaborador.get("Fee", Decimal("0")) + eventos_colaborador.get("Impostos", Decimal("0"))
        )

    totais_por_grupo["Subtotal"] = sum(
        (v for k, v in totais_por_grupo.items() if k not in ("FEE", "Impostos")), Decimal("0")
    )
    totais_por_grupo["Total"] = (
        totais_por_grupo["Subtotal"] + totais_por_grupo.get("FEE", Decimal("0")) + totais_por_grupo.get("Impostos", Decimal("0"))
    )

    grand_total: dict[str, Decimal] = defaultdict(Decimal)
    for eventos_colaborador in valores_por_colaborador.values():
        for evento, valor in eventos_colaborador.items():
            grand_total[evento] += valor

    return ResultadoSegmento(
        regra=regra,
        linhas_colaborador=cadastro_por_colaborador,
        valores_por_colaborador=dict(valores_por_colaborador),
        eventos_ordenados=eventos_ordenados,
        totais_por_grupo=dict(totais_por_grupo),
        verbas_fora_de_para=verbas_fora_de_para,
        grand_total=dict(grand_total),
    )


@dataclass
class ForaDasRegras:
    quantidade: int = 0
    colaboradores: list[dict] = field(default_factory=list)  # [{matricula, colaborador}]


def gerar_mapas(db: Session, cliente_id: int, competencia: str) -> tuple[list[MapaGerado], ForaDasRegras]:
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).one()

    lancamentos = (
        db.query(LancamentoVerba)
        .filter(LancamentoVerba.cliente_id == cliente_id, LancamentoVerba.competencia == competencia)
        .all()
    )
    if not lancamentos:
        return [], ForaDasRegras()

    de_para_por_codigo = {
        item.verba_codigo: item
        for item in db.query(DeParaVerba).filter(DeParaVerba.de_para_modelo_id == cliente.de_para_modelo_id)
        if item.grupo not in GRUPOS_SINTETICOS
    }

    regras = (
        db.query(RegraSegmentacao)
        .filter(RegraSegmentacao.cliente_id == cliente_id, RegraSegmentacao.aplica_mapa.is_(True))
        .order_by(RegraSegmentacao.ordem, RegraSegmentacao.id)
        .all()
    )

    campos_cadastrais_ordenados = [
        c.campo for c in db.query(CampoCadastralMapa).order_by(CampoCadastralMapa.ordem).all() if c.campo in CAMPO_CADASTRAL_ATRIBUTO
    ] or list(CAMPO_CADASTRAL_ATRIBUTO.keys())

    mapas_gerados: list[MapaGerado] = []
    fora_das_regras = ForaDasRegras()

    if not regras:
        # Cliente sem nenhuma regra cadastrada -> um único mapa GERAL com todo mundo.
        segmento = _montar_segmento(lancamentos, de_para_por_codigo, None)
        mapas_gerados.append(_criar_mapa(db, cliente, competencia, None, segmento, campos_cadastrais_ordenados))
        db.commit()
        return mapas_gerados, fora_das_regras

    # "Grande SE": agrupa por colaborador primeiro (é a unidade do mapa final), e
    # testa as regras em ordem contra os atributos DESSE colaborador — cada regra
    # pode olhar um atributo diferente (uma por CNPJ, outra por CARGO...), a
    # primeira que bater vence.
    linhas_por_colaborador: dict[str, list[LancamentoVerba]] = defaultdict(list)
    for linha in lancamentos:
        chave_colaborador = linha.matricula or linha.colaborador or "SEM_MATRICULA"
        linhas_por_colaborador[chave_colaborador].append(linha)

    linhas_por_regra: dict[int, list[LancamentoVerba]] = defaultdict(list)
    for chave_colaborador, linhas_colaborador in linhas_por_colaborador.items():
        primeira_linha = linhas_colaborador[0]
        regra_vencedora = next((regra for regra in regras if _regra_bate(primeira_linha, regra)), None)

        if regra_vencedora is None:
            fora_das_regras.quantidade += 1
            fora_das_regras.colaboradores.append(
                {"matricula": primeira_linha.matricula, "colaborador": primeira_linha.colaborador}
            )
            continue

        linhas_por_regra[regra_vencedora.id].extend(linhas_colaborador)

    regras_por_id = {r.id: r for r in regras}
    for regra_id, linhas_regra in linhas_por_regra.items():
        regra = regras_por_id[regra_id]
        segmento = _montar_segmento(linhas_regra, de_para_por_codigo, regra)
        mapas_gerados.append(_criar_mapa(db, cliente, competencia, regra, segmento, campos_cadastrais_ordenados))

    db.commit()
    return mapas_gerados, fora_das_regras


def _criar_mapa(
    db: Session,
    cliente: Cliente,
    competencia: str,
    regra: RegraSegmentacao | None,
    segmento: ResultadoSegmento,
    campos_cadastrais: list[str],
) -> MapaGerado:
    alertas = {"verbas_fora_de_para": sorted(segmento.verbas_fora_de_para)}
    valores_iniciais = {grupo: str(valor) for grupo, valor in segmento.totais_por_grupo.items()}

    mapa = MapaGerado(
        cliente_id=cliente.id,
        regra_segmentacao_id=regra.id if regra else None,
        competencia=competencia,
        status=StatusMapaGerado.RASCUNHO,
        valores_iniciais=valores_iniciais,
        alertas=alertas,
    )
    db.add(mapa)
    db.flush()
    mapa.arquivo_path = _gerar_arquivo_xlsx(cliente, mapa, segmento, campos_cadastrais)
    return mapa


def _gerar_arquivo_xlsx(cliente: Cliente, mapa: MapaGerado, segmento: ResultadoSegmento, campos_cadastrais: list[str]) -> str:
    wb = openpyxl.Workbook()
    negrito = Font(bold=True)

    ws_mensal = wb.active
    ws_mensal.title = "MENSAL"
    # Fee/Impostos/Subtotal/Total só aparecem no rodapé fixo — sem isso duplicariam
    # como coluna normal, já que também entram em `eventos_ordenados` (ver _montar_segmento).
    eventos = [e for (_, _, _, e) in segmento.eventos_ordenados if e not in ("Subtotal", "Total", "Fee", "Impostos")]
    cabecalho = campos_cadastrais + eventos + ["Subtotal", "Fee", "Impostos", "Total"]
    ws_mensal.append(cabecalho)
    for cel in ws_mensal[1]:
        cel.font = negrito

    for matricula, cadastro in segmento.linhas_colaborador.items():
        valores_evento = segmento.valores_por_colaborador.get(matricula, {})
        linha = [cadastro.get(campo) for campo in campos_cadastrais]
        linha += [float(valores_evento.get(evento, 0)) or None for evento in eventos]
        linha += [
            float(valores_evento.get("Subtotal", 0)),
            float(valores_evento.get("Fee", 0)),
            float(valores_evento.get("Impostos", 0)),
            float(valores_evento.get("Total", 0)),
        ]
        ws_mensal.append(linha)

    linha_totais = [None] * (len(campos_cadastrais) - 1) + ["TOTAL"]
    linha_totais += [float(segmento.grand_total.get(evento, 0)) or None for evento in eventos]
    linha_totais += [
        float(segmento.totais_por_grupo.get("Subtotal", 0)),
        float(segmento.totais_por_grupo.get("FEE", 0)),
        float(segmento.totais_por_grupo.get("Impostos", 0)),
        float(segmento.totais_por_grupo.get("Total", 0)),
    ]
    ws_mensal.append(linha_totais)
    for cel in ws_mensal[ws_mensal.max_row]:
        cel.font = negrito

    ws_mapa = wb.create_sheet("MAPA")
    ws_mapa.append(["ORDEM GRUPO", "GRUPO", "SOMA"])
    for cel in ws_mapa[1]:
        cel.font = negrito
    grupos_unicos = sorted({(og, g) for (og, _, g, _) in segmento.eventos_ordenados} | {(99, "Subtotal"), (100, "FEE"), (101, "Impostos"), (102, "Total")})
    for ordem_grupo, grupo in grupos_unicos:
        ws_mapa.append([ordem_grupo, grupo, float(segmento.totais_por_grupo.get(grupo, 0))])

    settings = get_settings()
    pasta = os.path.join(settings.generated_dir, str(cliente.id))
    os.makedirs(pasta, exist_ok=True)
    nome_arquivo = f"mapa_{mapa.competencia}_{mapa.id}.xlsx"
    caminho = os.path.join(pasta, nome_arquivo)
    wb.save(caminho)
    return caminho
