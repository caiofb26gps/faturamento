from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin


class RegraSegmentacao(Base, TimestampMixin):
    """Uma linha do "grande SE" de segmentação de um cliente: SE `atributo_segmentacao`
    (CNPJ, CARGO, COLABORADOR...) do colaborador for `valor_segmentacao`, ele cai
    nesse grupo/destinatário. As regras de um cliente são testadas em ordem
    (`ordem`, definida manualmente pelo usuário) — a primeira que bater vence, então
    um cliente pode misturar atributos diferentes regra a regra (ex: uma regra por
    CNPJ, outra por CARGO). Colaborador que não bate em nenhuma regra fica fora de
    qualquer mapa naquela competência — só conta no alerta "fora das regras"
    (ver geracao_mapa.py) para o faturista cadastrar a regra que falta.

    `aplica_email` / `aplica_mapa` cobrem o caso em que a segmentação de e-mail e a
    segmentação do mapa divergem — na maioria dos clientes observados elas coincidem,
    então por padrão uma regra vale para as duas.
    """

    __tablename__ = "regras_segmentacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True)

    ordem: Mapped[int] = mapped_column(Integer, default=0)
    atributo_segmentacao: Mapped[str] = mapped_column(String(50))
    valor_segmentacao: Mapped[str] = mapped_column(String(255), index=True)
    nome_exibicao: Mapped[str] = mapped_column(String(255))
    email_responsavel: Mapped[str] = mapped_column(String(255))
    dia_envio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    envio_automatico: Mapped[bool] = mapped_column(Boolean, default=False)
    analista_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)

    aplica_email: Mapped[bool] = mapped_column(Boolean, default=True)
    aplica_mapa: Mapped[bool] = mapped_column(Boolean, default=True)

    cliente: Mapped["Cliente"] = relationship(back_populates="regras_segmentacao")
