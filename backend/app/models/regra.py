from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class RegraSegmentacao(Base, TimestampMixin):
    """Equivalente à aba REGRAS: quando a segmentação do cliente não é GERAL, define
    para qual destinatário vai cada valor de segmentação (ex: cada colaborador, cada
    CNPJ, cada UF...).

    `aplica_email` / `aplica_mapa` cobrem o caso em que a segmentação de e-mail e a
    segmentação do mapa divergem — na maioria dos clientes observados elas coincidem,
    então por padrão uma regra vale para as duas.
    """

    __tablename__ = "regras_segmentacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True)

    valor_segmentacao: Mapped[str] = mapped_column(String(255), index=True)
    nome_exibicao: Mapped[str] = mapped_column(String(255))
    email_responsavel: Mapped[str] = mapped_column(String(255))
    dia_envio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    envio_automatico: Mapped[bool] = mapped_column(Boolean, default=False)
    analista_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)

    aplica_email: Mapped[bool] = mapped_column(Boolean, default=True)
    aplica_mapa: Mapped[bool] = mapped_column(Boolean, default=True)

    cliente: Mapped["Cliente"] = relationship(back_populates="regras_segmentacao")
