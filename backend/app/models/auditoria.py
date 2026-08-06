from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.enums import AcaoAuditoria
from app.models.mixins import TimestampMixin
from app.models.types import JSONVariant


class AuditoriaAlteracao(Base, TimestampMixin):
    """Changelog simples de edições em cadastros sensíveis (clientes, regras de
    segmentação, de/para de verbas) — trilha que hoje não existe em planilha."""

    __tablename__ = "auditoria_alteracoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    entidade: Mapped[str] = mapped_column(String(100), index=True)
    entidade_id: Mapped[int] = mapped_column(Integer, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    acao: Mapped[AcaoAuditoria] = mapped_column(Enum(AcaoAuditoria, name="acao_auditoria"))
    dados_antes: Mapped[dict | None] = mapped_column(JSONVariant, nullable=True)
    dados_depois: Mapped[dict | None] = mapped_column(JSONVariant, nullable=True)
