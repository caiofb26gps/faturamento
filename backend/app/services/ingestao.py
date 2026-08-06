"""Orquestra a ingestão de um upload da base DS (closed inicial do mês ou ajuste
pontual): parse -> resolução de cliente -> gravação em lote de `lancamentos_verbas`.

A resolução de cliente usa NEGOCIO(ds) -> Negocio(cadastro) via
`negocio_ds_mapeamento`, e então (negocio_cadastro, COD GRUPO) -> cliente_id via
`cliente_identificadores` — essa é a chave validada com dados reais (ver
docs/plano.md); CNPJ não é usado como chave porque um cliente pode ter dezenas
deles (matriz + filiais).
"""

from collections import Counter
from dataclasses import dataclass, field

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.models.cliente import ClienteIdentificador
from app.models.enums import StatusImportacao, TipoImportacao, TipoIdentificadorCliente
from app.models.importacao import Importacao
from app.models.lancamento import LancamentoVerba
from app.models.negocio_mapeamento import NegocioDsMapeamento
from app.services.ds_parser import ler_linhas_ds

TAMANHO_LOTE = 2000


@dataclass
class ResumoImportacao:
    importacao_id: int
    total_linhas: int = 0
    linhas_resolvidas: int = 0
    linhas_nao_resolvidas: int = 0
    principais_nao_resolvidos: list[dict] = field(default_factory=list)


class ResolvedorCliente:
    """Pré-carrega os de/paras necessários uma única vez (não faz 1 query por linha
    em uma base de ~166k linhas)."""

    def __init__(self, db: Session):
        self._negocio_map = {
            m.negocio_ds.upper(): m.negocio_cadastro
            for m in db.query(NegocioDsMapeamento).all()
        }
        self._identificadores = {
            (ident.negocio, ident.valor): ident.cliente_id
            for ident in db.query(ClienteIdentificador)
            .filter(ClienteIdentificador.tipo == TipoIdentificadorCliente.COD_GRUPO)
            .all()
        }

    def negocio_cadastro(self, negocio_ds: str | None) -> str | None:
        if negocio_ds is None:
            return None
        return self._negocio_map.get(negocio_ds.upper())

    def resolver(self, negocio_ds: str | None, cod_grupo: str | None) -> int | None:
        negocio_cadastro = self.negocio_cadastro(negocio_ds)
        if negocio_cadastro is None or cod_grupo is None:
            return None
        return self._identificadores.get((negocio_cadastro, cod_grupo))


def criar_importacao(
    db: Session,
    *,
    competencia: str,
    tipo: TipoImportacao,
    usuario_id: int,
    arquivo_original_path: str,
    cliente_id: int | None = None,
    regra_segmentacao_id: int | None = None,
) -> Importacao:
    """Passo rápido e síncrono: só grava o registro da importação. O processamento
    pesado (parse + resolução + insert de até ~166k linhas) roda depois via
    `processar_importacao`, chamado em background pela API — subir o arquivo não
    pode deixar a requisição HTTP pendurada por minutos."""
    importacao = Importacao(
        competencia=competencia,
        tipo=tipo,
        cliente_id=cliente_id,
        regra_segmentacao_id=regra_segmentacao_id,
        arquivo_original_path=arquivo_original_path,
        usuario_upload_id=usuario_id,
        status=StatusImportacao.PROCESSANDO,
    )
    db.add(importacao)
    db.commit()
    db.refresh(importacao)
    return importacao


def processar_importacao(db: Session, importacao_id: int) -> ResumoImportacao:
    importacao = db.query(Importacao).filter(Importacao.id == importacao_id).one()
    caminho_arquivo = importacao.arquivo_original_path
    competencia = importacao.competencia

    resolvedor = ResolvedorCliente(db)
    resumo = ResumoImportacao(importacao_id=importacao.id)
    nao_resolvidos: Counter[tuple[str | None, str | None, str | None]] = Counter()
    lote: list[dict] = []

    try:
        for linha in ler_linhas_ds(caminho_arquivo):
            resumo.total_linhas += 1
            cliente_resolvido_id = resolvedor.resolver(linha["negocio_ds"], linha["cod_grupo"])
            if cliente_resolvido_id is not None:
                resumo.linhas_resolvidas += 1
            else:
                resumo.linhas_nao_resolvidas += 1
                nao_resolvidos[(linha["negocio_ds"], linha["cod_grupo"], linha["grupo_cliente"])] += 1

            lote.append(
                {
                    "importacao_id": importacao.id,
                    "competencia": linha["competencia"] or competencia,
                    "negocio": resolvedor.negocio_cadastro(linha["negocio_ds"]),
                    "empresa": linha["empresa"],
                    "filial": linha["filial"],
                    "cc": linha["cc"],
                    "cnpj": linha["cnpj"],
                    "cod_cli": linha["cod_cli"],
                    "razao_social": linha["razao_social"],
                    "cod_grupo": linha["cod_grupo"],
                    "grupo_cliente": linha["grupo_cliente"],
                    "matricula": linha["matricula"],
                    "colaborador": linha["colaborador"],
                    "cargo": linha["cargo"],
                    "situacao_folha": linha["situacao_folha"],
                    "dt_admissao": linha["dt_admissao"],
                    "dt_demissao": linha["dt_demissao"],
                    "verba_codigo": linha["verba_codigo"],
                    "descri": linha["descri"],
                    "valor": linha["valor"],
                    "origem": linha["origem"],
                    "cliente_id": cliente_resolvido_id,
                }
            )

            if len(lote) >= TAMANHO_LOTE:
                db.execute(insert(LancamentoVerba.__table__), lote)
                lote.clear()

        if lote:
            db.execute(insert(LancamentoVerba.__table__), lote)

        resumo.principais_nao_resolvidos = [
            {"negocio_ds": neg, "cod_grupo": cod, "grupo_cliente": grp, "linhas": qtd}
            for (neg, cod, grp), qtd in nao_resolvidos.most_common(20)
        ]
        importacao.status = StatusImportacao.CONCLUIDA
        importacao.resumo = {
            "total_linhas": resumo.total_linhas,
            "linhas_resolvidas": resumo.linhas_resolvidas,
            "linhas_nao_resolvidas": resumo.linhas_nao_resolvidas,
            "principais_nao_resolvidos": resumo.principais_nao_resolvidos,
        }
        db.commit()
    except Exception as exc:
        db.rollback()
        importacao = db.query(Importacao).filter(Importacao.id == importacao_id).one()
        importacao.status = StatusImportacao.ERRO
        importacao.mensagem_erro = str(exc)[:2000]
        db.commit()
        raise

    return resumo
