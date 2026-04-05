from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Venda(Base):
    __tablename__ = "vendas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    operador_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    observacao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    operador: Mapped["Usuario"] = relationship(back_populates="vendas")  # noqa: F821
    itens: Mapped[list["ItemVenda"]] = relationship(
        back_populates="venda", cascade="all, delete-orphan"
    )


class ItemVenda(Base):
    __tablename__ = "itens_venda"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    venda_id: Mapped[int] = mapped_column(ForeignKey("vendas.id"), nullable=False)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"), nullable=False)
    quantidade: Mapped[int] = mapped_column(nullable=False)
    preco_unitario: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    venda: Mapped["Venda"] = relationship(back_populates="itens")
    produto: Mapped["Produto"] = relationship(back_populates="itens_venda")  # noqa: F821

    @property
    def subtotal(self) -> float:
        return self.quantidade * float(self.preco_unitario)
