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

## Deploy

**Situação atual: não há ambiente publicado funcionando.** O histórico até aqui:

- **Render + Turso** — primeiro ambiente, chegou a rodar. Abandonado porque o
  plano free hiberna quando fica sem requisição, e a ingestão da DS roda em
  segundo plano *depois* da resposta HTTP: o serviço era derrubado no meio do
  processamento. O Turso também é má escolha pra inserir 166 mil linhas por mês
  (tudo via HTTP, sem conexão persistente).
- **Railway** — descartado: bloqueado pelo antivírus da máquina de trabalho.
- **Decisão atual**: Postgres no **Supabase** (free não expira) + backend no
  **Render Starter** (plano pago não hiberna) + frontend estático no Render.
  Ainda não configurado.

Os `railway.json` de cada pasta ficaram no repositório e **não estão em uso** —
servem só de referência de build/start caso o Railway volte a ser opção.

Ao configurar o Supabase: use a connection string do **pooler**, não a direta.
A conexão direta costuma ser só IPv6 e vários hosts não fazem saída por IPv6.

**Serviço backend** — root directory `backend`:

| Variável | Valor |
|---|---|
| `DATABASE_URL` | connection string do pooler do Supabase |
| `CREDENTIALS_ENCRYPTION_KEY` | saída de `scripts/generate_encryption_key.py` |
| `JWT_SECRET` | string aleatória longa |
| `CORS_ORIGINS` | URL pública do serviço frontend |

No Render, rode as migrations no *build command*
(`pip install -r requirements.txt && alembic upgrade head`) — o
`preDeployCommand` do `railway.json` não é lido por lá.

**Serviço frontend** — root directory `frontend`:

| Variável | Valor |
|---|---|
| `VITE_API_URL` | URL pública do serviço backend |

`VITE_API_URL` é lida **no build** (Vite embute no bundle), então mudá-la exige
um novo deploy do frontend — não basta reiniciar.
