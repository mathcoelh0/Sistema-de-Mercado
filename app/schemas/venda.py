from datetime import datetime

from pydantic import BaseModel, Field


class ItemVendaCreate(BaseModel):
    produto_id: int
    quantidade: int = Field(..., gt=0)


class VendaCreate(BaseModel):
    operador_id: int
    itens: list[ItemVendaCreate] = Field(..., min_length=1)
    observacao: str | None = None


class ItemVendaResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    produto_id: int
    quantidade: int
    preco_unitario: float
    subtotal: float


class VendaResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    operador_id: int
    total: float
    observacao: str | None
    criado_em: datetime
    itens: list[ItemVendaResponse]
