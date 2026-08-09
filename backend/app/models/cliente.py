from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import StatusCliente, StatusFolha, TipoIdentificadorCliente
from app.models.mixins import TimestampMixin


class Cliente(Base, TimestampMixin):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(primary_key=True)
    negocio: Mapped[str] = mapped_column(String(50), index=True)
    nome: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[StatusCliente] = mapped_column(Enum(StatusCliente, name="status_cliente"), default=StatusCliente.PENDENTE)

    # Não existe mais um "tipo de segmentação" único do cliente — cada
    # RegraSegmentacao carrega seu próprio atributo (CNPJ, CARGO, COLABORADOR...) e
    # é testada em ordem (ver `RegraSegmentacao.ordem`), como um grande SE/SENÃO.
    # Cliente sem nenhuma regra = um único mapa (GERAL). Ver geracao_mapa.py.

    # use_alter=True quebra o ciclo de FK com de_para_modelos.cliente_id (um cliente
    # aponta para o seu de/para; um de/para aponta para o cliente dono) para que o
    # banco consiga criar/dropar as tabelas em qualquer ordem.
    de_para_modelo_id: Mapped[int | None] = mapped_column(
        ForeignKey("de_para_modelos.id", use_alter=True, name="fk_clientes_de_para_modelo"), nullable=True
    )
    # Layout do mapa final. Hoje só existe o layout "GERAL" observado nos dados reais;
    # mantido como código simples em vez de tabela relacional até haver um segundo layout.
    modelo_mapa_codigo: Mapped[str] = mapped_column(String(50), default="GERAL")

    analista_responsavel_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    folha: Mapped[StatusFolha] = mapped_column(Enum(StatusFolha, name="status_folha"), default=StatusFolha.FECHADA)
    aguardo_po: Mapped[bool] = mapped_column(Boolean, default=False)

    portal_site: Mapped[str | None] = mapped_column(String(500), nullable=True)
    portal_login_cifrado: Mapped[str | None] = mapped_column(Text, nullable=True)
    portal_senha_cifrada: Mapped[str | None] = mapped_column(Text, nullable=True)

    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    analista_responsavel: Mapped["Usuario"] = relationship(back_populates="clientes")
    de_para_modelo: Mapped["DeParaModelo | None"] = relationship(foreign_keys=[de_para_modelo_id])
    identificadores: Mapped[list["ClienteIdentificador"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )
    regras_segmentacao: Mapped[list["RegraSegmentacao"]] = relationship(
        back_populates="cliente", cascade="all, delete-orphan"
    )


class ClienteIdentificador(Base, TimestampMixin):
    """Liga linhas da base DS a um cliente cadastrado.

    A DS não traz um `cliente_id` direto — a resolução hoje é feita visualmente pelo
    faturista. Este é o ponto de risco descrito no plano ("Chave de ligação DS →
    Cliente"): o tipo mais provável é COD_GRUPO ou CNPJ por negócio, mas precisa ser
    validado com o faturista antes de confiar 100% na resolução automática.
    """

    __tablename__ = "cliente_identificadores"

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"), index=True)
    negocio: Mapped[str] = mapped_column(String(50), index=True)
    tipo: Mapped[TipoIdentificadorCliente] = mapped_column(
        Enum(TipoIdentificadorCliente, name="tipo_identificador_cliente")
    )
    valor: Mapped[str] = mapped_column(String(255), index=True)

    cliente: Mapped["Cliente"] = relationship(back_populates="identificadores")
