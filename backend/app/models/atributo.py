from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin


class AtributoSegmentacao(Base, TimestampMixin):
    """Lookup dos tipos válidos de segmentação (equivalente à aba LISTAS):
    CNPJ, CARGO, CR, UF, COLABORADOR, GERAL, etc."""

    __tablename__ = "atributos_segmentacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)
