from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.produto import Produto
from app.schemas.produto import (
    ProdutoCreate,
    ProdutoResponse,
    ProdutoUpdate,
    ProdutoValidadeAlerta,
)
from app.services.validade_service import listar_proximos_a_vencer, listar_vencidos

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.post("/", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED)
def criar_produto(dados: ProdutoCreate, db: Session = Depends(get_db)):
    if dados.ean:
        existente = db.query(Produto).filter(Produto.ean == dados.ean).first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe um produto com EAN '{dados.ean}'",
            )

    produto = Produto(**dados.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return produto


@router.get("/", response_model=list[ProdutoResponse])
def listar_produtos(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return db.query(Produto).offset(skip).limit(limit).all()


@router.get("/validade/alerta", response_model=list[ProdutoValidadeAlerta])
def alertas_validade(
    dias: int = Query(30, ge=1, le=365, description="Janela de dias para o alerta"),
    db: Session = Depends(get_db),
):
    """Retorna produtos que vencem nos próximos X dias (inclui já vencidos)."""
    return listar_proximos_a_vencer(db, dias)


@router.get("/validade/vencidos", response_model=list[ProdutoValidadeAlerta])
def produtos_vencidos(db: Session = Depends(get_db)):
    """Retorna apenas produtos com validade expirada que ainda têm estoque."""
    return listar_vencidos(db)


@router.get("/{produto_id}", response_model=ProdutoResponse)
def obter_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.get(Produto, produto_id)
    if not produto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    return produto


@router.patch("/{produto_id}", response_model=ProdutoResponse)
def atualizar_produto(produto_id: int, dados: ProdutoUpdate, db: Session = Depends(get_db)):
    produto = db.get(Produto, produto_id)
    if not produto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")

    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(produto, campo, valor)

    db.commit()
    db.refresh(produto)
    return produto


@router.delete("/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.get(Produto, produto_id)
    if not produto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
    db.delete(produto)
    db.commit()
