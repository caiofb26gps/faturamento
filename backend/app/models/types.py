from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB

# JSONB em Postgres (produção), JSON genérico em outros dialetos — permite testar o
# schema localmente em SQLite sem abrir mão de JSONB (indexável) em produção.
JSONVariant = JSON().with_variant(JSONB, "postgresql")
