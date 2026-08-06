"""schema inicial

Cria todas as tabelas do sistema a partir do metadata dos modelos SQLAlchemy
(`app.models`). Não há Postgres disponível neste ambiente de desenvolvimento para
gerar a migration via autogenerate, então o schema é criado diretamente do
metadata — garante que a migration corresponda exatamente aos modelos.

Isso só é seguro porque este projeto nunca foi implantado em um Postgres real
(nenhum dado de produção existe) — é a única migration até agora, então
"refletir todo o metadata atual" é equivalente a "refletir o schema desta
versão". A PARTIR DE QUANDO HOUVER UMA SEGUNDA MIGRATION (0002+), este padrão
NÃO pode se repetir: mudanças futuras devem usar `alembic revision --autogenerate`
contra um Postgres real, ou `op.create_table`/`op.add_column` explícitos —
nunca `Base.metadata.create_all()` de novo, senão a migration mais nova volta a
"vazar" para dentro desta.

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
