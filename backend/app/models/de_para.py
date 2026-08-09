from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class DeParaModelo(Base, TimestampMixin):
    """Um De/Para de verbas. Não sabe quem usa ele — a relação é sempre no sentido
    Cliente -> De/Para (`Cliente.de_para_modelo_id`), nunca o contrário. "GERAL" é só
    o nome convencional do modelo padrão; nada aqui o trata como especial."""

    __tablename__ = "de_para_modelos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150))

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
