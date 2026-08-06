"""Gera um DS_Aberto_Fechado sintético pequeno (mesmo header real) para testes
rápidos da API de upload, sem precisar do arquivo de 166k linhas."""

import openpyxl

HEADER = [
    "EMPRESA", "FILIAL", "COMPETENCIA", "CC", "CNPJ", "COD CLI", "RAZAO SOCIAL",
    "COD GRUPO", "GRUPO CLIENTE", "MATRICULA", "COLABORADOR", "LOTE", "DS", "PREVIA",
    "VERBA", "DESCRI", "REEMBOLSO", "TRIBUTOS", "TAXA", "ENCARGOS", "TOTAL", "PEDIDO",
    "FILIAL PEDIDO", "RPS", "ORIGEM", "REGRA FATURAMENTO", "DT ADMISSAO", "DT DEMISSAO",
    "DT ATUALIZACAO", "DT CANCELAMENTO", "TIPO VERBA", "MSG NF", "DT EMISSAO DS",
    "DETALHES", "TP NOTA", "EXCECAO", "SERVICO", "TIPO CANCELAMENTO", "PROCESSO",
    "LOCAL ENTREGA", "CR", "FICHA", "TIPO ELIMINACAO", "CTT CLIENTE", "FILIAL CR",
    "DATABLOQ", "CC CLIENTE", "SRA SALARIO", "LOJACLI", "GERENTE", "NEGOCIO",
    "RECNO ZBK", "FUNCAO", "SITUACAO FOLHA", "CPF SRA", "HORAS MENSAIS", "LOGZBK",
]

LINHAS = [
    ("1T", "VY", "202607", "10001", "33163908000175", "008399", "BARRY CALLEBAUT", "004144", "BARRY CALLEBAUT",
     "000188310", "FULANO DA SILVA", None, "1", "1", "020", "SALARIO", 0, 0, 0, 0, 3000.00, "", "", "", "IMPORT", "",
     "", "", "", "", "EVENTO FIXO", "", "20260605", "", "Normal", "", "", "", "", "", "", "", "", "", "", "",
     "004144", "", "ATIVO", "02", "FULANO DA SILVA", "MAO DE OBRA INTERMITENTE", "1", "AUXILIAR", "FECHADA", "", 0, ""),
    ("1T", "VY", "202607", "10002", "99999999000199", "999999", "CLIENTE INEXISTENTE", "999999", "CLIENTE FANTASMA",
     "000199999", "CICLANO SOUZA", None, "2", "2", "535", "DESC. DIVERSOS", 0, 0, 0, 0, -500.00, "", "", "", "IMPORT",
     "", "", "", "", "", "OUTROS BENEFICIOS", "", "20260716", "", "Normal", "", "", "", "", "", "", "", "", "", "",
     "", "999999", "", "ATIVO", "02", "CICLANO SOUZA", "FIELD MARKETING", "2", "PROMOTOR", "FECHADA", "", 0, ""),
]

if __name__ == "__main__":
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "DS_Aberto_Fechado"
    ws.append(HEADER)
    for linha in LINHAS:
        ws.append(linha)
    wb.save("_ds_sintetica.xlsx")
    print("Gerado _ds_sintetica.xlsx")
