from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StatusImportacao, TipoImportacao
from app.models.mixins import TimestampMixin
from app.models.types import JSONVariant


class Importacao(Base, TimestampMixin):
    """Um upload de base (closed inicial do mês ou ajuste pontual)."""

    __tablename__ = "importacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    competencia: Mapped[str] = mapped_column(String(6), index=True)  # formato AAAAMM
    tipo: Mapped[TipoImportacao] = mapped_column(Enum(TipoImportacao, name="tipo_importacao"))

    # Ajustes são escopados a um cliente (e opcionalmente a uma regra específica).
    # O upload "closed" inicial cobre todos os clientes, por isso fica nulo.
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"), nullable=True)
    regra_segmentacao_id: Mapped[int | None] = mapped_column(ForeignKey("regras_segmentacao.id"), nullable=True)

    arquivo_original_path: Mapped[str] = mapped_column(String(500))
    usuario_upload_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    status: Mapped[StatusImportacao] = mapped_column(
        Enum(StatusImportacao, name="status_importacao"), default=StatusImportacao.PROCESSANDO
    )
    mensagem_erro: Mapped[str | None] = mapped_column(Text, nullable=True)
    # {total_linhas, linhas_resolvidas, linhas_nao_resolvidas, principais_nao_resolvidos}
    # preenchido quando o processamento em background termina (ver app/services/ingestao.py)
    resumo: Mapped[dict | None] = mapped_column(JSONVariant, nullable=True)

    lancamentos: Mapped[list["LancamentoVerba"]] = relationship(back_populates="importacao")
