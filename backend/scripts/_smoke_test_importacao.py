"""Smoke test da API de upload de importações (rodar contra o banco de teste já
populado, com DATABASE_URL apontando para SQLite descartável)."""

import time

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.main import app
from app.models.usuario import Usuario

db = SessionLocal()
usuario = db.query(Usuario).filter(Usuario.ativo.is_(True)).first()
if usuario is None:
    from app.core.security import hash_password
    from app.models.enums import PapelUsuario

    usuario = Usuario(nome="Teste", email="teste-importacao@gpssa.com.br", senha_hash=hash_password("senha123"), papel=PapelUsuario.ADMIN)
    db.add(usuario)
    db.commit()
    email, senha = usuario.email, "senha123"
else:
    email, senha = usuario.email, None
db.close()

client = TestClient(app)

if senha is None:
    print("Usando usuário existente sem senha conhecida — pulando teste de upload (rode em banco isolado).")
else:
    r = client.post("/auth/login", data={"username": email, "password": senha})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    with open("_ds_sintetica.xlsx", "rb") as f:
        r = client.post(
            "/importacoes",
            headers=headers,
            data={"competencia": "202607", "tipo": "CLOSED_INICIAL"},
            files={"arquivo": ("_ds_sintetica.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
    assert r.status_code == 201, r.text
    importacao_id = r.json()["id"]
    print("importacao criada:", r.json())

    for _ in range(20):
        r = client.get(f"/importacoes/{importacao_id}", headers=headers)
        status = r.json()["status"]
        if status != "PROCESSANDO":
            break
        time.sleep(0.5)

    print("resultado final:", r.json())
    assert r.json()["status"] == "CONCLUIDA", r.json()
    assert r.json()["resumo"]["total_linhas"] == 2
    print("\nSMOKE TEST IMPORTACAO OK")
