# Mapa de Faturamento

Sistema que substitui o fluxo hoje baseado em Power BI + planilhas soltas para
transformar a base de verbas (folha) em mapas de faturamento por cliente.

Ver plano e decisões em [`docs/plano.md`](docs/plano.md).

## Estrutura

- `backend/` — API em FastAPI + SQLAlchemy + Alembic
- `frontend/` — aplicação web em React + TypeScript (Vite)
- `docs/` — plano e decisões de arquitetura

## Rodar localmente

Banco local é SQLite (arquivo `backend/dev.db`) — não precisa de Postgres pra
desenvolver.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python scripts/generate_encryption_key.py   # cole o resultado em CREDENTIALS_ENCRYPTION_KEY
alembic upgrade head
python scripts/create_admin.py seu@email.com "Seu Nome" suasenha
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

## Carregar os cadastros a partir das planilhas atuais

```bash
cd backend
python scripts/migrate_from_excel.py "Regras <mes>.xlsx" "DE PARA GERAL.xlsx"
python scripts/bootstrap_identificadores.py "DS <mes>.xlsx"
```

## Deploy (Railway)

Dois serviços no mesmo repositório, cada um com seu *root directory*, mais um
Postgres gerenciado. Os `railway.json` de cada pasta já definem build e start.

**Postgres**: adicione o plugin Postgres ao projeto. Ele publica a variável
`DATABASE_URL`; referencie ela no serviço do backend.

**Serviço backend** — root directory `backend`:

| Variável | Valor |
|---|---|
| `DATABASE_URL` | referência ao Postgres do projeto |
| `CREDENTIALS_ENCRYPTION_KEY` | saída de `scripts/generate_encryption_key.py` |
| `JWT_SECRET` | string aleatória longa |
| `CORS_ORIGINS` | URL pública do serviço frontend |

As migrations rodam automaticamente no deploy (`preDeployCommand`).

**Serviço frontend** — root directory `frontend`:

| Variável | Valor |
|---|---|
| `VITE_API_URL` | URL pública do serviço backend |

`VITE_API_URL` é lida **no build** (Vite embute no bundle), então mudá-la exige
um novo deploy do frontend — não basta reiniciar.
