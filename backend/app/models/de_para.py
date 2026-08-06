from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class DeParaModelo(Base, TimestampMixin):
    """Um De/Para de verbas. `cliente_id` nulo = modelo padrão GERAL, usado por
    qualquer cliente que não tenha um De/Para próprio."""

    __tablename__ = "de_para_modelos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), nullable=True)

    itens: Mapped[list["DeParaVerba"]] = relationship(back_populates="modelo", cascade="all, delete-orphan")


class DeParaVerba(Base, TimestampMixin):
    __tablename__ = "de_para_verbas"

    id: Mapped[int] = mapped_column(primary_key=True)
    de_para_modelo_id: Mapped[int] = mapped_column(ForeignKey("de_para_modelos.id"), index=True)
    verba_codigo: Mapped[str] = mapped_column(String(20), index=True)
    descricao_original: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evento_exibicao: Mapped[str] = mapped_column(String(150))
    grupo: Mapped[str] = mapped_column(String(100))
    ordem_grupo: Mapped[int] = mapped_column(Integer)
    ordem_item: Mapped[int] = mapped_column(Integer)

    modelo: Mapped["DeParaModelo"] = relationship(back_populates="itens")


class CampoCadastralMapa(Base, TimestampMixin):
    """Equivalente à aba CADASTRAIS: quais campos do colaborador aparecem no mapa e
    em que ordem. Hoje é uma lista global (não por cliente)."""

    __tablename__ = "campos_cadastrais_mapa"

    id: Mapped[int] = mapped_column(primary_key=True)
    campo: Mapped[str] = mapped_column(String(100))
    ordem: Mapped[int] = mapped_column(Integer)
