from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import atributos, auth, clientes, de_para, importacoes, regras, usuarios

app = FastAPI(title="Mapa de Faturamento", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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


@app.get("/health")
def health():
    return {"status": "ok"}
