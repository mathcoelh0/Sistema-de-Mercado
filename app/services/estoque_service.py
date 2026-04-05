import logging

from sqlalchemy.orm import Session

from app.core.logging_config import estoque_log
from app.models.produto import Produto
from app.models.venda import ItemVenda, Venda
from app.schemas.venda import VendaCreate

logger = logging.getLogger(__name__)


class EstoqueInsuficienteError(Exception):
    def __init__(self, produto_id: int, disponivel: int, solicitado: int):
        self.produto_id = produto_id
        self.disponivel = disponivel
        self.solicitado = solicitado
        super().__init__(
            f"Produto id={produto_id}: estoque insuficiente "
            f"(disponível={disponivel}, solicitado={solicitado})"
        )


class ProdutoNaoEncontradoError(Exception):
    def __init__(self, produto_id: int):
        self.produto_id = produto_id
        super().__init__(f"Produto id={produto_id} não encontrado")


def registrar_venda(db: Session, dados: VendaCreate) -> Venda:
    """
    Registra uma venda e debita automaticamente o estoque.
    Lança EstoqueInsuficienteError ou ProdutoNaoEncontradoError em caso de falha,
    garantindo que nenhum item seja debitado parcialmente (transação atômica).
    """
    # --- Fase 1: validar todos os itens antes de alterar qualquer estoque ---
    produtos_cache: dict[int, Produto] = {}

    for item in dados.itens:
        produto = db.get(Produto, item.produto_id)

        if produto is None:
            estoque_log.warning(
                "Tentativa de venda com produto inexistente | produto_id=%s | operador_id=%s",
                item.produto_id,
                dados.operador_id,
            )
            raise ProdutoNaoEncontradoError(item.produto_id)

        if produto.quantidade < item.quantidade:
            estoque_log.warning(
                "Estoque insuficiente | produto_id=%s | nome='%s' | "
                "disponivel=%s | solicitado=%s | operador_id=%s",
                produto.id,
                produto.nome,
                produto.quantidade,
                item.quantidade,
                dados.operador_id,
            )
            raise EstoqueInsuficienteError(produto.id, produto.quantidade, item.quantidade)

        produtos_cache[item.produto_id] = produto

    # --- Fase 2: debitar estoque e criar registros ---
    venda = Venda(operador_id=dados.operador_id, observacao=dados.observacao, total=0)
    db.add(venda)
    db.flush()  # obtém venda.id sem commitar

    total = 0.0
    for item in dados.itens:
        produto = produtos_cache[item.produto_id]
        produto.quantidade -= item.quantidade

        item_venda = ItemVenda(
            venda_id=venda.id,
            produto_id=produto.id,
            quantidade=item.quantidade,
            preco_unitario=float(produto.preco),
        )
        db.add(item_venda)
        total += item.quantidade * float(produto.preco)

    venda.total = round(total, 2)
    db.commit()
    db.refresh(venda)

    logger.info(
        "Venda registrada | venda_id=%s | total=%.2f | operador_id=%s",
        venda.id,
        venda.total,
        dados.operador_id,
    )
    return venda
