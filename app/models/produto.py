from datetime import date

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    ean: Mapped[str | None] = mapped_column(String(14), unique=True, index=True, nullable=True)
    preco: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantidade: Mapped[int] = mapped_column(default=0, nullable=False)
    validade: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    itens_venda: Mapped[list["ItemVenda"]] = relationship(back_populates="produto")  # noqa: F821

    @property
    def dias_para_vencer(self) -> int | None:
        if self.validade is None:
            return None
        return (self.validade - date.today()).days

    @property
    def vencido(self) -> bool:
        if self.validade is None:
            return False
        return self.validade < date.today()
