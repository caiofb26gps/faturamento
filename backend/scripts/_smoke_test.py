"""Smoke test manual da API contra SQLite (rodar só com DATABASE_URL=sqlite apontado
para um arquivo descartável). Não é um teste automatizado permanente do projeto."""

from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.main import app
from app.models.enums import PapelUsuario
from app.models.usuario import Usuario

db = SessionLocal()
db.add(Usuario(nome="Admin", email="admin@gpssa.com.br", senha_hash=hash_password("senha123"), papel=PapelUsuario.ADMIN))
db.add(
    Usuario(
        nome="Analista Um", email="analista@gpssa.com.br", senha_hash=hash_password("senha123"), papel=PapelUsuario.ANALISTA
    )
)
db.commit()
db.close()

client = TestClient(app)

r = client.post("/auth/login", data={"username": "admin@gpssa.com.br", "password": "senha123"})
assert r.status_code == 200, r.text
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print("login admin ok")

r = client.get("/auth/me", headers=headers)
assert r.status_code == 200 and r.json()["papel"] == "ADMIN", r.text
print("me ok:", r.json())

r = client.post(
    "/clientes",
    headers=headers,
    json={
        "negocio": "TALENTOS",
        "nome": "3M",
        "segmentacao_email": "COLABORADOR",
        "segmentacao_mapa": "COLABORADOR",
        "portal_login": "03.528.670/0001-73",
        "portal_senha": "Tr@de2024",
    },
)
assert r.status_code == 201, r.text
cliente = r.json()
assert cliente["portal_credenciais_configuradas"] is True
assert "portal_login" not in cliente and "portal_senha" not in cliente
print("cliente criado ok:", cliente)

r = client.post(
    f"/clientes/{cliente['id']}/regras",
    headers=headers,
    json={
        "valor_segmentacao": "MARIANGELA DA SILVA REIS PONCA",
        "nome_exibicao": "CAROLINA DINIZ",
        "email_responsavel": "cpdiniz2@mmm.com",
        "dia_envio": 11,
        "envio_automatico": False,
    },
)
assert r.status_code == 201, r.text
print("regra criada ok:", r.json())

r = client.post("/de-para/modelos", headers=headers, json={"nome": "GERAL", "cliente_id": None})
assert r.status_code == 201, r.text
modelo = r.json()

r = client.post(
    f"/de-para/modelos/{modelo['id']}/itens",
    headers=headers,
    json={
        "verba_codigo": "020",
        "evento_exibicao": "Salário",
        "grupo": "Salario",
        "ordem_grupo": 1,
        "ordem_item": 1001,
    },
)
assert r.status_code == 201, r.text
print("de/para item criado ok:", r.json())

r = client.post("/atributos-segmentacao", headers=headers, json={"codigo": "COLABORADOR"})
assert r.status_code == 201, r.text
print("atributo criado ok:", r.json())

# analista sem clientes não deve ver o cliente acima
r = client.post("/auth/login", data={"username": "analista@gpssa.com.br", "password": "senha123"})
token_analista = r.json()["access_token"]
r = client.get("/clientes", headers={"Authorization": f"Bearer {token_analista}"})
assert r.status_code == 200 and r.json() == [], r.text
print("RBAC ok: analista sem clientes não vê o cliente do admin")

# admin não autenticado não pode criar cliente
r = client.post("/clientes", json={"negocio": "X", "nome": "Y"})
assert r.status_code == 401, r.text
print("auth obrigatória ok")

print("\nSMOKE TEST OK")
