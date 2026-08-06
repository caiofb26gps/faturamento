"""schema inicial

Cria as 13 tabelas do plano (cadastro + operacional). Como não há um Postgres
disponível neste ambiente de desenvolvimento para gerar a migration via
autogenerate, o schema é criado diretamente a partir do metadata dos modelos
SQLAlchemy (`app.models`) — garante que a migration corresponda exatamente aos
modelos. Migrations futuras devem usar `alembic revision --autogenerate` normalmente
contra um Postgres real.

Revision ID: 0001
Revises:
Create Date: 2026-08-05

"""
from typing import Sequence, Union

from alembic import op

from app.core.database import Base
from app.models import *  # noqa: F401,F403

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
