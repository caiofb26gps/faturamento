"""Smoke test do upload da DS pela API HTTP — exatamente a rota multipart que a
tela de Importação usa (POST /importacoes com arquivo + competencia + tipo),
incluindo o polling de status que a tela faz enquanto está PROCESSANDO.

Usa a DS sintética pequena (scripts/_criar_ds_sintetica.py) pra não duplicar os
166k lançamentos do arquivo real no banco de desenvolvimento.

Uso (com o backend rodando em :8000):
    python scripts/_criar_ds_sintetica.py && python scripts/_smoke_upload.py
"""

import sys
import time

import httpx

BASE = "http://127.0.0.1:8000"
ARQUIVO = "_ds_sintetica.xlsx"

token = httpx.post(
    f"{BASE}/auth/login",
    data={"username": "caio.batista@gpssa.com.br", "password": "faturamento123"},
).json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

with open(ARQUIVO, "rb") as f:
    resposta = httpx.post(
        f"{BASE}/importacoes",
        headers=headers,
        files={"arquivo": (ARQUIVO, f)},
        data={"competencia": "202699", "tipo": "CLOSED_INICIAL"},
        timeout=60,
    )

print(f"POST /importacoes -> {resposta.status_code}")
if resposta.status_code != 201:
    print(resposta.text)
    sys.exit(1)

importacao = resposta.json()
print(f"  id={importacao['id']} status={importacao['status']}")

for _ in range(12):
    time.sleep(1.5)
    atual = httpx.get(f"{BASE}/importacoes/{importacao['id']}", headers=headers).json()
    if atual["status"] != "PROCESSANDO":
        print(f"  status final: {atual['status']}")
        print(f"  resumo: {atual['resumo']}")
        print(f"  erro: {atual['mensagem_erro']}")
        break
else:
    print("  ainda PROCESSANDO depois de 18s — verificar log do backend")
