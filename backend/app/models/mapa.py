from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StatusMapaGerado
from app.models.mixins import TimestampMixin
from app.models.types import JSONVariant


class MapaGerado(Base, TimestampMixin):
    """Uma instância de mapa gerada para um cliente (e, se segmentado, para um
    destinatário/regra específico) em uma competência.

    `valores_iniciais` é o snapshot logo após o upload "closed"; se depois entrar um
    ajuste, `valores_finais` e `diferenca` são recalculados — equivalente à tabela
    Inicial/Final/Diferença que já existe no painel do Power BI hoje.

    `alertas` guarda os mesmos avisos do painel atual (verbas fora do De-Para, valores
    fora das regras, colaboradores fora do De-Para auxiliar) para a tela de revisão.
    """

    __tablename__ = "mapas_gerados"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True)
    regra_segmentacao_id: Mapped[int | None] = mapped_column(ForeignKey("regras_segmentacao.id"), nullable=True)
    competencia: Mapped[str] = mapped_column(String(6), index=True)

    status: Mapped[StatusMapaGerado] = mapped_column(
        Enum(StatusMapaGerado, name="status_mapa_gerado"), default=StatusMapaGerado.RASCUNHO
    )
    arquivo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    valores_iniciais: Mapped[dict | None] = mapped_column(JSONVariant, nullable=True)
    valores_finais: Mapped[dict | None] = mapped_column(JSONVariant, nullable=True)
    diferenca: Mapped[dict | None] = mapped_column(JSONVariant, nullable=True)
    alertas: Mapped[dict | None] = mapped_column(JSONVariant, nullable=True)

    gerado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)

    envios: Mapped[list["Envio"]] = relationship(back_populates="mapa_gerado", cascade="all, delete-orphan")
