from datetime import date, timedelta

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.produto import Produto


def listar_proximos_a_vencer(db: Session, dias: int = 30) -> list[Produto]:
    """
    Retorna produtos que vencem nos próximos `dias` dias,
    incluindo os já vencidos (dias_para_vencer < 0).
    """
    hoje = date.today()
    limite = hoje + timedelta(days=dias)

    return (
        db.query(Produto)
        .filter(
            and_(
                Produto.validade.isnot(None),
                Produto.validade <= limite,
                Produto.quantidade > 0,
            )
        )
        .order_by(Produto.validade.asc())
        .all()
    )


def listar_vencidos(db: Session) -> list[Produto]:
    """Retorna produtos com data de validade anterior a hoje."""
    return (
        db.query(Produto)
        .filter(
            and_(
                Produto.validade.isnot(None),
                Produto.validade < date.today(),
                Produto.quantidade > 0,
            )
        )
        .order_by(Produto.validade.asc())
        .all()
    )
