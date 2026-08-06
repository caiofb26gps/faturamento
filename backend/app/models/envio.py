from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StatusEnvio
from app.models.mixins import TimestampMixin


class Envio(Base, TimestampMixin):
    """Registro de envio de um mapa gerado — alimenta os indicadores 'E-mails
    Enviados' e 'SLA de Envio' que já existem no painel atual. O envio em si é
    manual (o faturista dispara pelo próprio e-mail); aqui só registramos o
    resultado."""

    __tablename__ = "envios"

    id: Mapped[int] = mapped_column(primary_key=True)
    mapa_gerado_id: Mapped[int] = mapped_column(ForeignKey("mapas_gerados.id"), index=True)
    email_destino: Mapped[str] = mapped_column(String(255))
    data_prevista: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_enviado: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[StatusEnvio] = mapped_column(Enum(StatusEnvio, name="status_envio"), default=StatusEnvio.PENDENTE)
    dentro_do_prazo: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    enviado_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    mapa_gerado: Mapped["MapaGerado"] = relationship(back_populates="envios")
