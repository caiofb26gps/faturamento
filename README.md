# Mapa de Faturamento

Sistema que substitui o fluxo hoje baseado em Power BI + planilhas soltas para
transformar a base de verbas (folha) em mapas de faturamento por cliente.

Ver plano completo em [`docs/plano.md`](docs/plano.md).

## Estrutura

- `backend/` — API em FastAPI + SQLAlchemy + Alembic (PostgreSQL)
- `frontend/` — aplicação web em React + TypeScript (Vite)
- `docs/` — plano e decisões de arquitetura

## Backend — como rodar localmente

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```
