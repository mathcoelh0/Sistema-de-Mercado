from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.venda import Venda
from app.schemas.venda import VendaCreate, VendaResponse
from app.services.estoque_service import (
    EstoqueInsuficienteError,
    ProdutoNaoEncontradoError,
    registrar_venda,
)

router = APIRouter(prefix="/vendas", tags=["Vendas"])


@router.post("/", response_model=VendaResponse, status_code=status.HTTP_201_CREATED)
def criar_venda(dados: VendaCreate, db: Session = Depends(get_db)):
    try:
        return registrar_venda(db, dados)
    except ProdutoNaoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EstoqueInsuficienteError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "erro": "estoque_insuficiente",
                "produto_id": e.produto_id,
                "disponivel": e.disponivel,
                "solicitado": e.solicitado,
            },
        )


@router.get("/", response_model=list[VendaResponse])
def listar_vendas(db: Session = Depends(get_db)):
    return db.query(Venda).order_by(Venda.criado_em.desc()).limit(100).all()


@router.get("/{venda_id}", response_model=VendaResponse)
def obter_venda(venda_id: int, db: Session = Depends(get_db)):
    venda = db.get(Venda, venda_id)
    if not venda:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada")
    return venda
