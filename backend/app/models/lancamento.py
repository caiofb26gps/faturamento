from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class LancamentoVerba(Base, TimestampMixin):
    """Linha normalizada da base DS (`DS_Aberto_Fechado`). Guarda apenas os campos
    usados pelo pipeline de geração de mapa — não todas as 57 colunas originais, já
    que a maioria (ex: dados de pedido/NF, ficha, exceção) não participa das regras
    de de/para nem de segmentação."""

    __tablename__ = "lancamentos_verbas"

    id: Mapped[int] = mapped_column(primary_key=True)
    importacao_id: Mapped[int] = mapped_column(ForeignKey("importacoes.id"), index=True)
    competencia: Mapped[str] = mapped_column(String(6), index=True)

    negocio: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    empresa: Mapped[str | None] = mapped_column(String(20), nullable=True)
    filial: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cc: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cnpj: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    cod_cli: Mapped[str | None] = mapped_column(String(20), nullable=True)
    razao_social: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cod_grupo: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    grupo_cliente: Mapped[str | None] = mapped_column(String(255), nullable=True)

    matricula: Mapped[str | None] = mapped_column(String(20), nullable=True)
    colaborador: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    cargo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    situacao_folha: Mapped[str | None] = mapped_column(String(50), nullable=True)
    dt_admissao: Mapped[date | None] = mapped_column(Date, nullable=True)
    dt_demissao: Mapped[date | None] = mapped_column(Date, nullable=True)

    verba_codigo: Mapped[str] = mapped_column(String(20), index=True)
    descri: Mapped[str | None] = mapped_column(String(255), nullable=True)
    valor: Mapped[float] = mapped_column(Numeric(14, 2))
    origem: Mapped[str | None] = mapped_column(String(20), nullable=True)  # IMPORT / CLOSED / SRC etc.

    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), nullable=True, index=True)

    importacao: Mapped["Importacao"] = relationship(back_populates="lancamentos")
