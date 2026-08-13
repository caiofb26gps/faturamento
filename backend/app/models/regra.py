from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ComparadorCondicao, LogicaRegra
from app.models.mixins import TimestampMixin


class RegraSegmentacao(Base, TimestampMixin):
    """Uma linha do "grande SE" de segmentação de um cliente: SE as condições
    baterem (ver RegraCondicao), o colaborador cai nesse grupo/destinatário.

    As regras de um cliente são testadas em ordem (`ordem`, definida manualmente
    pelo usuário) — a primeira que bater vence, então um cliente pode misturar
    critérios diferentes regra a regra (uma por CNPJ, outra por CARGO). Um
    colaborador que não bate em nenhuma regra fica fora de qualquer mapa naquela
    competência — só conta no alerta "fora das regras" (ver geracao_mapa.py) para
    o faturista cadastrar a regra que falta.

    `aplica_email` / `aplica_mapa` cobrem o caso em que a segmentação de e-mail e a
    segmentação do mapa divergem — na maioria dos clientes observados elas coincidem,
    então por padrão uma regra vale para as duas.
    """

    __tablename__ = "regras_segmentacao"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True)

    ordem: Mapped[int] = mapped_column(Integer, default=0)
    # Como combinar as condições: todas (E) ou qualquer uma (OU).
    logica: Mapped[LogicaRegra] = mapped_column(Enum(LogicaRegra, name="logica_regra"), default=LogicaRegra.E)

    nome_exibicao: Mapped[str] = mapped_column(String(255))
    email_responsavel: Mapped[str] = mapped_column(String(255))
    dia_envio: Mapped[int | None] = mapped_column(Integer, nullable=True)
    envio_automatico: Mapped[bool] = mapped_column(Boolean, default=False)
    analista_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)

    aplica_email: Mapped[bool] = mapped_column(Boolean, default=True)
    aplica_mapa: Mapped[bool] = mapped_column(Boolean, default=True)

    cliente: Mapped["Cliente"] = relationship(back_populates="regras_segmentacao")
    condicoes: Mapped[list["RegraCondicao"]] = relationship(
        back_populates="regra", cascade="all, delete-orphan", order_by="RegraCondicao.id"
    )


class RegraCondicao(Base, TimestampMixin):
    """Uma condição de uma regra: "<atributo> <comparador> <valor>".

    Ex: CARGO CONTEM "OPERADOR", CNPJ IGUAL "60872306003932".
    O atributo é o código de um AtributoSegmentacao (CNPJ, CARGO, CC,
    COLABORADOR...); quais deles o gerador sabe resolver está em
    ATRIBUTO_PARA_CAMPO_LANCAMENTO (geracao_mapa.py).
    """

    __tablename__ = "regra_condicoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    regra_id: Mapped[int] = mapped_column(ForeignKey("regras_segmentacao.id"), index=True)

    atributo: Mapped[str] = mapped_column(String(50))
    comparador: Mapped[ComparadorCondicao] = mapped_column(
        Enum(ComparadorCondicao, name="comparador_condicao"), default=ComparadorCondicao.IGUAL
    )
    valor: Mapped[str] = mapped_column(String(255))

    regra: Mapped["RegraSegmentacao"] = relationship(back_populates="condicoes")
