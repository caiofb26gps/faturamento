from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PapelUsuario
from app.models.mixins import TimestampMixin


class Usuario(Base, TimestampMixin):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    papel: Mapped[PapelUsuario] = mapped_column(Enum(PapelUsuario, name="papel_usuario"), default=PapelUsuario.ANALISTA)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)

    clientes: Mapped[list["Cliente"]] = relationship(back_populates="analista_responsavel")
