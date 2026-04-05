from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logging_config import setup_logging
from app.database import Base, engine
from app.routers import produtos, vendas


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    # Cria as tabelas ao subir (use Alembic em produção)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Sistema de Gestão de Estoque e PDV",
    description="Controle de estoque, validade e ponto de venda para mercado local.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(produtos.router)
app.include_router(vendas.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "versao": app.version}
