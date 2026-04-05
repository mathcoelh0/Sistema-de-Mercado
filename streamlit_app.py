import sqlite3
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Gestão de Mercado",
    page_icon="🛒",
    layout="wide",
)

DB_PATH = Path("mercado.db")
ALERTA_DIAS = 7


# ─────────────────────────────────────────────
# BANCO DE DADOS
# ─────────────────────────────────────────────

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT    NOT NULL,
            ean        TEXT,
            quantidade INTEGER NOT NULL DEFAULT 0,
            preco      REAL    NOT NULL,
            validade   TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saidas (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id    INTEGER NOT NULL,
            produto_nome  TEXT    NOT NULL,
            quantidade    INTEGER NOT NULL,
            preco_unit    REAL    NOT NULL,
            total         REAL    NOT NULL,
            registrado_em TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def db_listar() -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM produtos ORDER BY validade ASC, nome ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def db_inserir(nome, ean, quantidade, preco, validade) -> None:
    conn = get_conn()
    conn.execute(
        "INSERT INTO produtos (nome, ean, quantidade, preco, validade) VALUES (?,?,?,?,?)",
        (nome, ean or None, quantidade, preco, str(validade) if validade else None),
    )
    conn.commit()
    conn.close()


def db_excluir(pid: int) -> None:
    conn = get_conn()
    conn.execute("DELETE FROM produtos WHERE id=?", (pid,))
    conn.commit()
    conn.close()


def db_baixa(pid: int, qtd: int) -> str:
    conn = get_conn()
    row = conn.execute(
        "SELECT nome, quantidade, preco FROM produtos WHERE id=?", (pid,)
    ).fetchone()
    if not row:
        conn.close()
        return "erro:Produto não encontrado."
    if row["quantidade"] < qtd:
        conn.close()
        return f"erro:Estoque insuficiente. Disponível: {row['quantidade']} un."
    conn.execute(
        "UPDATE produtos SET quantidade = quantidade - ? WHERE id=?", (qtd, pid)
    )
    conn.execute(
        """INSERT INTO saidas (produto_id, produto_nome, quantidade, preco_unit, total, registrado_em)
           VALUES (?,?,?,?,?,datetime('now','localtime'))""",
        (pid, row["nome"], qtd, row["preco"], round(qtd * row["preco"], 2)),
    )
    conn.commit()
    conn.close()
    return f"ok:{qtd}x {row['nome']} baixados. Total: R$ {qtd * row['preco']:.2f}"


def db_saidas() -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM saidas ORDER BY registrado_em DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def status_validade(val_str: str | None) -> tuple[str, str]:
    """Retorna (emoji_badge, css_cor) com base na data de validade."""
    if not val_str:
        return "⚪ Sem validade", ""
    val = date.fromisoformat(val_str)
    hoje = date.today()
    if val < hoje:
        return "🔴 VENCIDO", "background:#fee2e2;border-left:4px solid #ef4444;"
    if val <= hoje + timedelta(days=ALERTA_DIAS):
        return "🟡 Atenção", "background:#fef9c3;border-left:4px solid #f59e0b;"
    return "🟢 OK", "background:#f0fdf4;border-left:4px solid #22c55e;"


def fmt_data(val_str: str | None) -> str:
    if not val_str:
        return "—"
    d = date.fromisoformat(val_str)
    return d.strftime("%d/%m/%Y")


# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────

st.markdown("""
<style>
[data-testid="stSidebar"] { background:#14532d; }
[data-testid="stSidebar"] * { color:#dcfce7 !important; }

.card {
    border-radius:12px; padding:16px 18px; margin-bottom:10px;
    border:1px solid #e5e7eb;
}
.kpi {
    background:white; border-radius:12px; padding:18px 20px;
    border:1px solid #e5e7eb; text-align:center;
    box-shadow:0 1px 4px rgba(0,0,0,.06);
}
.kpi .num { font-size:2rem; font-weight:700; line-height:1.1; }
.kpi .lbl { font-size:.75rem; color:#6b7280; margin-top:4px; }
.tag {
    display:inline-block; padding:2px 10px; border-radius:9999px;
    font-size:.72rem; font-weight:600;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────

init_db()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🛒 Mercado")
    st.markdown("---")
    pagina = st.radio(
        "Menu",
        ["📊 Dashboard", "➕ Adicionar Produto", "🛍️ Baixa de Caixa", "📋 Histórico"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption(f"Hoje: {date.today().strftime('%d/%m/%Y')}")


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

if pagina == "📊 Dashboard":
    st.title("📊 Dashboard")

    produtos = db_listar()
    hoje = date.today()
    limite = hoje + timedelta(days=ALERTA_DIAS)

    vencidos  = [p for p in produtos if p["validade"] and date.fromisoformat(p["validade"]) < hoje and p["quantidade"] > 0]
    alertas   = [p for p in produtos if p["validade"] and hoje <= date.fromisoformat(p["validade"]) <= limite]
    sem_stock = [p for p in produtos if p["quantidade"] == 0]
    total_itens = sum(p["quantidade"] for p in produtos)

    # ── KPIs ──
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="kpi"><div class="num">{len(produtos)}</div><div class="lbl">📦 Produtos</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="kpi"><div class="num">{total_itens}</div><div class="lbl">🔢 Itens em Estoque</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="kpi" style="border-top:3px solid #ef4444"><div class="num" style="color:#ef4444">{len(vencidos)}</div><div class="lbl">🔴 Vencidos</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="kpi" style="border-top:3px solid #f59e0b"><div class="num" style="color:#f59e0b">{len(alertas)}</div><div class="lbl">🟡 Vencem em {ALERTA_DIAS}d</div></div>', unsafe_allow_html=True)

    # ── Alertas em destaque ──
    if vencidos:
        st.error(f"**{len(vencidos)} produto(s) VENCIDO(S) ainda em estoque — retirar imediatamente!**")
    if alertas:
        st.warning(f"**{len(alertas)} produto(s) vencem nos próximos {ALERTA_DIAS} dias.**")

    st.markdown("---")
    st.subheader("📦 Todos os Produtos")

    if not produtos:
        st.info("Nenhum produto cadastrado. Vá em **Adicionar Produto**.")
    else:
        # Cabeçalho da tabela
        h = st.columns([3, 1, 1, 1, 2, 1])
        for col, label in zip(h, ["Produto", "EAN", "Qtd", "Preço", "Validade", "Status"]):
            col.markdown(f"**{label}**")
        st.divider()

        for p in produtos:
            badge, estilo = status_validade(p["validade"])
            with st.container():
                st.markdown(f'<div class="card" style="{estilo}">', unsafe_allow_html=True)
                cols = st.columns([3, 1, 1, 1, 2, 1])
                cols[0].write(f"**{p['nome']}**")
                cols[1].write(p["ean"] or "—")
                cols[2].write(str(p["quantidade"]))
                cols[3].write(f"R$ {p['preco']:.2f}")
                cols[4].write(fmt_data(p["validade"]))
                cols[5].write(badge)

                with st.expander("⋯ ações"):
                    st.caption(f"ID: {p['id']}")
                    if st.button("🗑️ Excluir produto", key=f"del_{p['id']}", type="primary"):
                        db_excluir(p["id"])
                        st.success(f"**{p['nome']}** removido.")
                        st.rerun()

                st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# ADICIONAR PRODUTO
# ─────────────────────────────────────────────

elif pagina == "➕ Adicionar Produto":
    st.title("➕ Adicionar Produto")

    with st.form("form_add", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nome       = c1.text_input("Nome do Produto *", placeholder="Ex: Leite Integral 1L")
        ean        = c2.text_input("Código EAN (opcional)", placeholder="Ex: 7891234567890")

        c3, c4, c5 = st.columns(3)
        quantidade = c3.number_input("Quantidade *", min_value=0, step=1, value=1)
        preco      = c4.number_input("Preço de Venda (R$) *", min_value=0.01, step=0.10, format="%.2f", value=1.00)
        validade   = c5.date_input("Data de Validade", value=None)

        ok = st.form_submit_button("💾 Cadastrar", type="primary", use_container_width=True)

    if ok:
        if not nome.strip():
            st.error("O nome do produto é obrigatório.")
        else:
            db_inserir(nome.strip(), ean.strip(), quantidade, preco, validade)
            st.success(f"✅ **{nome.strip()}** cadastrado com sucesso!")
            st.balloons()


# ─────────────────────────────────────────────
# BAIXA DE CAIXA
# ─────────────────────────────────────────────

elif pagina == "🛍️ Baixa de Caixa":
    st.title("🛍️ Baixa de Caixa")
    st.caption("Selecione o produto vendido e informe a quantidade. O estoque é debitado automaticamente.")

    produtos = db_listar()
    com_estoque = [p for p in produtos if p["quantidade"] > 0]

    if not com_estoque:
        st.warning("Nenhum produto com estoque disponível.")
        st.stop()

    opcoes = {f"{p['nome']} (estoque: {p['quantidade']} un)": p for p in com_estoque}

    with st.form("form_baixa", clear_on_submit=True):
        escolha = st.selectbox("Produto *", list(opcoes.keys()))
        prod    = opcoes[escolha]

        c1, c2 = st.columns(2)
        qtd = c1.number_input("Quantidade a baixar *", min_value=1,
                               max_value=prod["quantidade"], step=1, value=1)
        c2.metric("Total previsto", f"R$ {qtd * prod['preco']:.2f}")

        ok = st.form_submit_button("✅ Registrar Baixa", type="primary", use_container_width=True)

    if ok:
        resultado = db_baixa(prod["id"], qtd)
        tipo, msg = resultado.split(":", 1)
        if tipo == "ok":
            st.success(f"✅ {msg}")
            st.rerun()
        else:
            st.error(f"❌ {msg}")

    st.markdown("---")
    st.subheader("Estoque disponível")

    hd = st.columns([3, 1, 1, 2])
    for col, lbl in zip(hd, ["Produto", "Qtd", "Preço", "Validade"]):
        col.markdown(f"**{lbl}**")
    st.divider()

    for p in com_estoque:
        badge, estilo = status_validade(p["validade"])
        row = st.columns([3, 1, 1, 2])
        row[0].write(p["nome"])
        row[1].write(str(p["quantidade"]))
        row[2].write(f"R$ {p['preco']:.2f}")
        row[3].write(f"{fmt_data(p['validade'])}  {badge}")


# ─────────────────────────────────────────────
# HISTÓRICO
# ─────────────────────────────────────────────

elif pagina == "📋 Histórico":
    st.title("📋 Histórico de Saídas")

    saidas = db_saidas()

    if not saidas:
        st.info("Nenhuma saída registrada ainda.")
        st.stop()

    hoje_str = str(date.today())
    saidas_hoje = [s for s in saidas if s["registrado_em"].startswith(hoje_str)]
    total_hoje  = sum(s["total"] for s in saidas_hoje)
    total_geral = sum(s["total"] for s in saidas)

    c1, c2, c3 = st.columns(3)
    c1.metric("💵 Vendas Hoje", f"R$ {total_hoje:.2f}")
    c2.metric("📦 Baixas Hoje", len(saidas_hoje))
    c3.metric("💰 Total Histórico", f"R$ {total_geral:.2f}")

    st.markdown("---")

    hd = st.columns([2, 3, 1, 1, 1])
    for col, lbl in zip(hd, ["Data/Hora", "Produto", "Qtd", "Preço Unit.", "Total"]):
        col.markdown(f"**{lbl}**")
    st.divider()

    for s in saidas:
        row = st.columns([2, 3, 1, 1, 1])
        row[0].write(s["registrado_em"])
        row[1].write(s["produto_nome"])
        row[2].write(str(s["quantidade"]))
        row[3].write(f"R$ {s['preco_unit']:.2f}")
        row[4].write(f"R$ {s['total']:.2f}")
