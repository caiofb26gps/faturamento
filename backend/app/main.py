from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import atributos, auth, clientes, de_para, importacoes, mapas, regras, usuarios
from app.core.config import get_settings

app = FastAPI(title="Mapa de Faturamento", version="0.1.0")

# A URL do frontend em produção vem por variável de ambiente (CORS_ORIGINS) em
# vez de hardcoded: o domínio muda a cada troca de hospedagem, e esquecer de
# atualizar aqui derruba o login inteiro sem erro óbvio no frontend.
origens_extras = [o.strip() for o in get_settings().cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_extras,
    # Regex e não lista fixa para o dev: o Vite troca de porta quando a padrão
    # (5173) já está ocupada por outra sessão.
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(regras.router)
app.include_router(de_para.router)
app.include_router(atributos.router)
app.include_router(importacoes.router)
app.include_router(mapas.router)


@app.get("/health")
def health():
    return {"status": "ok"}
