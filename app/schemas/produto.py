from datetime import date

from pydantic import BaseModel, Field, field_validator


class ProdutoBase(BaseModel):
    nome: str = Field(..., min_length=1, max_length=200)
    ean: str | None = Field(None, max_length=14, description="Código de barras EAN-8/EAN-13")
    preco: float = Field(..., gt=0)
    quantidade: int = Field(0, ge=0)
    validade: date | None = None

    @field_validator("ean")
    @classmethod
    def validar_ean(cls, v: str | None) -> str | None:
        if v is not None and not v.isdigit():
            raise ValueError("EAN deve conter apenas dígitos")
        return v


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoUpdate(BaseModel):
    nome: str | None = Field(None, min_length=1, max_length=200)
    ean: str | None = Field(None, max_length=14)
    preco: float | None = Field(None, gt=0)
    quantidade: int | None = Field(None, ge=0)
    validade: date | None = None


class ProdutoResponse(ProdutoBase):
    model_config = {"from_attributes": True}

    id: int
    dias_para_vencer: int | None
    vencido: bool


class ProdutoValidadeAlerta(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nome: str
    ean: str | None
    quantidade: int
    validade: date
    dias_para_vencer: int
    vencido: bool
