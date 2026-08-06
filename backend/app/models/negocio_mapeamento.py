from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class NegocioDsMapeamento(Base, TimestampMixin):
    """A coluna NEGOCIO da base DS usa valores operacionais (ex: 'FIELD MARKETING',
    'CLT', 'MAO DE OBRA TEMPORARIA') que não são os mesmos do `Negocio` usado no
    cadastro de clientes (TALENTOS/TRADE). Esta tabela guarda esse de/para —
    descoberto empiricamente (ver docs/plano.md) — como configuração editável em vez
    de mapeamento fixo no código, porque é frágil a novos valores aparecendo na DS.
    """

    __tablename__ = "negocio_ds_mapeamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    negocio_ds: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    negocio_cadastro: Mapped[str] = mapped_column(String(50), index=True)
