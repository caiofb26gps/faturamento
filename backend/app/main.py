from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import atributos, auth, clientes, de_para, importacoes, mapas, regras, usuarios

app = FastAPI(title="Mapa de Faturamento", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    # regex (não lista fixa) porque em dev o Vite muda de porta quando a padrão
    # (5173) já está em uso, e em produção o front do Render é *.onrender.com.
    allow_origin_regex=r"http://localhost:\d+|https://faturamento-frontend[\w-]*\.onrender\.com",
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
