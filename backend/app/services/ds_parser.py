"""Parser da base DS (`DS_Aberto_Fechado`) para o formato normalizado de
`LancamentoVerba`. Usa openpyxl em modo `read_only` porque o arquivo real tem
~166 mil linhas e não cabe confortavelmente em memória se carregado normal."""

import re
from collections.abc import Iterator
from datetime import date
from decimal import Decimal, InvalidOperation

import openpyxl

COLUNAS_NECESSARIAS = [
    "EMPRESA",
    "FILIAL",
    "COMPETENCIA",
    "CC",
    "CNPJ",
    "COD CLI",
    "RAZAO SOCIAL",
    "COD GRUPO",
    "GRUPO CLIENTE",
    "MATRICULA",
    "COLABORADOR",
    "VERBA",
    "DESCRI",
    "TOTAL",
    "ORIGEM",
    "DT ADMISSAO",
    "DT DEMISSAO",
    "FUNCAO",
    "SITUACAO FOLHA",
    "NEGOCIO",
]


def _s(valor) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _data(valor) -> date | None:
    """Datas na DS vêm como texto AAAAMMDD (ex: '20260605') ou espaços em branco."""
    texto = _s(valor)
    if texto is None or not re.fullmatch(r"\d{8}", texto):
        return None
    try:
        return date(int(texto[:4]), int(texto[4:6]), int(texto[6:8]))
    except ValueError:
        return None


def _decimal(valor) -> Decimal:
    if valor is None or valor == "":
        return Decimal("0")
    try:
        return Decimal(str(valor))
    except InvalidOperation:
        return Decimal("0")


def ler_linhas_ds(caminho: str, aba: str = "DS_Aberto_Fechado") -> Iterator[dict]:
    """Gera um dict normalizado por linha da DS. Não abre o arquivo inteiro em
    memória — streaming linha a linha via read_only do openpyxl."""
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    try:
        ws = wb[aba]
        linhas = ws.iter_rows(values_only=True)
        cabecalho = next(linhas)
        indice = {str(nome).strip(): i for i, nome in enumerate(cabecalho) if nome is not None}

        faltando = [c for c in COLUNAS_NECESSARIAS if c not in indice]
        if faltando:
            raise ValueError(f"Colunas esperadas não encontradas na aba {aba}: {faltando}")

        def valor(row, nome):
            return row[indice[nome]]

        for row in linhas:
            if all(c is None for c in row):
                continue
            verba_codigo = _s(valor(row, "VERBA"))
            if verba_codigo is None:
                continue
            yield {
                "empresa": _s(valor(row, "EMPRESA")),
                "filial": _s(valor(row, "FILIAL")),
                "competencia": _s(valor(row, "COMPETENCIA")),
                "cc": _s(valor(row, "CC")),
                "cnpj": _s(valor(row, "CNPJ")),
                "cod_cli": _s(valor(row, "COD CLI")),
                "razao_social": _s(valor(row, "RAZAO SOCIAL")),
                "cod_grupo": _s(valor(row, "COD GRUPO")),
                "grupo_cliente": _s(valor(row, "GRUPO CLIENTE")),
                "matricula": _s(valor(row, "MATRICULA")),
                "colaborador": _s(valor(row, "COLABORADOR")),
                "cargo": _s(valor(row, "FUNCAO")),
                "situacao_folha": _s(valor(row, "SITUACAO FOLHA")),
                "dt_admissao": _data(valor(row, "DT ADMISSAO")),
                "dt_demissao": _data(valor(row, "DT DEMISSAO")),
                "verba_codigo": verba_codigo,
                "descri": _s(valor(row, "DESCRI")),
                "valor": _decimal(valor(row, "TOTAL")),
                "origem": _s(valor(row, "ORIGEM")),
                "negocio_ds": _s(valor(row, "NEGOCIO")),
            }
    finally:
        wb.close()
