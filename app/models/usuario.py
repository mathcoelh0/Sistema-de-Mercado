from enum import Enum as PyEnum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NivelAcesso(str, PyEnum):
    admin = "admin"
    operador = "operador"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nivel: Mapped[NivelAcesso] = mapped_column(
        Enum(NivelAcesso), default=NivelAcesso.operador, nullable=False
    )
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    vendas: Mapped[list["Venda"]] = relationship(back_populates="operador")  # noqa: F821
