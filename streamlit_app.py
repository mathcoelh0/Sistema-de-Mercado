import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Gestão de Mercado",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = Path("mercado.db")
ALERTA_DIAS = 7

# ─────────────────────────────────────────────
# BANCO DE DADOS
# ─────────────────────────────────────────────

def init_db() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nome      TEXT    NOT NULL,
                ean       TEXT,
                preco     REAL    NOT NULL,
                quantidade INTEGER NOT NULL DEFAULT 0,
                validade  TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saidas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id  INTEGER NOT NULL,
                produto_nome TEXT   NOT NULL,
                quantidade  INTEGER NOT NULL,
                preco_unit  REAL    NOT NULL,
                total       REAL    NOT NULL,
                registrado_em TEXT  NOT NULL,
                FOREIGN KEY (produto_id) REFERENCES produtos(id)
            )
        """)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ─────────────────────────────────────────────
# QUERIES
# ─────────────────────────────────────────────

def listar_produtos() -> pd.DataFrame:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM produtos ORDER BY nome").fetchall()
    if not rows:
        return pd.DataFrame(columns=["id","nome","ean","preco","quantidade","validade"])
    df = pd.DataFrame([dict(r) for r in rows])
    df["validade"] = pd.to_datetime(df["validade"], errors="coerce").dt.date
    return df


def inserir_produto(nome, ean, preco, quantidade, validade) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO produtos (nome, ean, preco, quantidade, validade) VALUES (?,?,?,?,?)",
            (nome, ean or None, preco, quantidade, str(validade) if validade else None),
        )


def atualizar_produto(pid, nome, ean, preco, quantidade, validade) -> None:
    with get_conn() as conn:
        conn.execute(
            """UPDATE produtos
               SET nome=?, ean=?, preco=?, quantidade=?, validade=?
               WHERE id=?""",
            (nome, ean or None, preco, quantidade,
             str(validade) if validade else None, pid),
        )


def deletar_produto(pid: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM produtos WHERE id=?", (pid,))


def registrar_saida(pid: int, nome: str, qtd: int, preco: float) -> str:
    """Debita estoque e grava histórico. Retorna mensagem de resultado."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT quantidade FROM produtos WHERE id=?", (pid,)
        ).fetchone()
        if row is None:
            return "❌ Produto não encontrado."
        disponivel = row["quantidade"]
        if disponivel < qtd:
            return f"❌ Estoque insuficiente. Disponível: **{disponivel}**"
        conn.execute(
            "UPDATE produtos SET quantidade = quantidade - ? WHERE id=?",
            (qtd, pid),
        )
        conn.execute(
            """INSERT INTO saidas
               (produto_id, produto_nome, quantidade, preco_unit, total, registrado_em)
               VALUES (?,?,?,?,?,?)""",
            (pid, nome, qtd, preco, round(qtd * preco, 2),
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
    return f"✅ Baixa registrada: **{qtd}x {nome}** — Total: R$ {qtd*preco:.2f}"


def listar_saidas() -> pd.DataFrame:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM saidas ORDER BY registrado_em DESC LIMIT 100"
        ).fetchall()
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame([dict(r) for r in rows])


# ─────────────────────────────────────────────
# HELPERS DE VALIDADE
# ─────────────────────────────────────────────

def classificar_validade(val) -> str:
    if pd.isna(val) or val is None:
        return "ok"
    hoje = date.today()
    if val < hoje:
        return "vencido"
    if val <= hoje + timedelta(days=ALERTA_DIAS):
        return "alerta"
    return "ok"


def badge_validade(val) -> str:
    cls = classificar_validade(val)
    if cls == "vencido":
        return "🔴 VENCIDO"
    if cls == "alerta":
        return "🟡 Atenção"
    return "🟢 OK"


# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────

st.markdown("""
<style>
[data-testid="stSidebar"] { background: #14532d; }
[data-testid="stSidebar"] * { color: #dcfce7 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] h1 { color: #ffffff !important; }

div[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
}
.kpi-vencido  { border-left: 4px solid #ef4444 !important; }
.kpi-alerta   { border-left: 4px solid #f59e0b !important; }
.kpi-ok       { border-left: 4px solid #22c55e !important; }

.tag-vencido { background:#fee2e2; color:#b91c1c; padding:2px 8px;
               border-radius:9999px; font-size:.75rem; font-weight:600; }
.tag-alerta  { background:#fef3c7; color:#92400e; padding:2px 8px;
               border-radius:9999px; font-size:.75rem; font-weight:600; }
.tag-ok      { background:#dcfce7; color:#166534; padding:2px 8px;
               border-radius:9999px; font-size:.75rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# INICIALIZAÇÃO
# ─────────────────────────────────────────────

init_db()

# ─────────────────────────────────────────────
# SIDEBAR — NAVEGAÇÃO
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🛒 Mercado")
    st.markdown("---")
    pagina = st.radio(
        "Navegação",
        ["📊 Dashboard", "➕ Cadastrar Produto", "✏️ Gerenciar Estoque", "🛍️ Baixa de Caixa", "📋 Histórico de Saídas"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption(f"Hoje: {date.today().strftime('%d/%m/%Y')}")


# ─────────────────────────────────────────────
# PÁGINA: DASHBOARD
# ─────────────────────────────────────────────

if pagina == "📊 Dashboard":
    st.title("📊 Dashboard")
    df = listar_produtos()

    hoje = date.today()
    limite = hoje + timedelta(days=ALERTA_DIAS)

    total_produtos = len(df)
    total_itens    = int(df["quantidade"].sum()) if not df.empty else 0

    vencidos = df[df["validade"].apply(lambda v: pd.notna(v) and v < hoje)] if not df.empty else pd.DataFrame()
    alertas  = df[df["validade"].apply(lambda v: pd.notna(v) and hoje <= v <= limite)] if not df.empty else pd.DataFrame()
    sem_estoque = df[df["quantidade"] == 0] if not df.empty else pd.DataFrame()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Produtos Cadastrados", total_produtos)
    c2.metric("🔢 Total de Itens", total_itens)
    c3.metric("🔴 Vencidos com Estoque", len(vencidos[vencidos["quantidade"] > 0]) if not vencidos.empty else 0)
    c4.metric("🟡 Vencem em 7 dias", len(alertas))

    st.markdown("---")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🔴 Produtos Vencidos")
        df_v = vencidos[vencidos["quantidade"] > 0][["nome","quantidade","validade","preco"]] if not vencidos.empty else pd.DataFrame()
        if df_v.empty:
            st.success("Nenhum produto vencido com estoque.")
        else:
            st.error(f"{len(df_v)} produto(s) vencido(s) ainda em estoque!")
            st.dataframe(df_v, use_container_width=True, hide_index=True,
                column_config={"validade": st.column_config.DateColumn("Validade", format="DD/MM/YYYY"),
                               "preco": st.column_config.NumberColumn("Preço", format="R$ %.2f")})

    with col_b:
        st.subheader("🟡 Vencem nos Próximos 7 Dias")
        df_a = alertas[["nome","quantidade","validade","preco"]] if not alertas.empty else pd.DataFrame()
        if df_a.empty:
            st.success("Nenhum produto em alerta de vencimento.")
        else:
            st.warning(f"{len(df_a)} produto(s) próximos do vencimento!")
            st.dataframe(df_a, use_container_width=True, hide_index=True,
                column_config={"validade": st.column_config.DateColumn("Validade", format="DD/MM/YYYY"),
                               "preco": st.column_config.NumberColumn("Preço", format="R$ %.2f")})

    st.markdown("---")
    st.subheader("📦 Todos os Produtos")

    if df.empty:
        st.info("Nenhum produto cadastrado ainda.")
    else:
        df_view = df.copy()
        df_view["status"] = df_view["validade"].apply(badge_validade)
        st.dataframe(
            df_view[["id","nome","ean","quantidade","preco","validade","status"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id":       st.column_config.NumberColumn("ID", width="small"),
                "nome":     st.column_config.TextColumn("Produto"),
                "ean":      st.column_config.TextColumn("EAN"),
                "quantidade": st.column_config.NumberColumn("Qtd", width="small"),
                "preco":    st.column_config.NumberColumn("Preço", format="R$ %.2f"),
                "validade": st.column_config.DateColumn("Validade", format="DD/MM/YYYY"),
                "status":   st.column_config.TextColumn("Status"),
            },
        )


# ─────────────────────────────────────────────
# PÁGINA: CADASTRAR PRODUTO
# ─────────────────────────────────────────────

elif pagina == "➕ Cadastrar Produto":
    st.title("➕ Cadastrar Produto")

    with st.form("form_cadastro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        nome       = c1.text_input("Nome do Produto *", placeholder="Ex: Leite Integral 1L")
        ean        = c2.text_input("Código EAN (opcional)", placeholder="Ex: 7891234567890")

        c3, c4, c5 = st.columns(3)
        preco      = c3.number_input("Preço de Venda (R$) *", min_value=0.01, step=0.10, format="%.2f")
        quantidade = c4.number_input("Quantidade *", min_value=0, step=1)
        validade   = c5.date_input("Data de Validade", value=None, min_value=date(2000, 1, 1))

        submitted = st.form_submit_button("💾 Cadastrar Produto", use_container_width=True, type="primary")

    if submitted:
        if not nome.strip():
            st.error("O nome do produto é obrigatório.")
        elif preco <= 0:
            st.error("O preço deve ser maior que zero.")
        else:
            inserir_produto(nome.strip(), ean.strip(), preco, quantidade, validade)
            st.success(f"✅ **{nome}** cadastrado com sucesso!")
            st.balloons()


# ─────────────────────────────────────────────
# PÁGINA: GERENCIAR ESTOQUE
# ─────────────────────────────────────────────

elif pagina == "✏️ Gerenciar Estoque":
    st.title("✏️ Gerenciar Estoque")
    df = listar_produtos()

    if df.empty:
        st.info("Nenhum produto cadastrado ainda. Vá em **Cadastrar Produto**.")
        st.stop()

    produto_nomes = df["nome"].tolist()
    nome_sel = st.selectbox("Selecione o produto para editar ou excluir", produto_nomes)
    row = df[df["nome"] == nome_sel].iloc[0]

    st.markdown("---")
    tab_editar, tab_excluir = st.tabs(["✏️ Editar", "🗑️ Excluir"])

    with tab_editar:
        with st.form("form_editar"):
            c1, c2 = st.columns(2)
            novo_nome = c1.text_input("Nome", value=row["nome"])
            novo_ean  = c2.text_input("EAN", value=row["ean"] or "")

            c3, c4, c5 = st.columns(3)
            novo_preco = c3.number_input("Preço (R$)", value=float(row["preco"]), min_value=0.01, step=0.10, format="%.2f")
            nova_qtd   = c4.number_input("Quantidade", value=int(row["quantidade"]), min_value=0, step=1)

            val_atual = row["validade"] if pd.notna(row["validade"]) else None
            nova_val  = c5.date_input("Validade", value=val_atual)

            salvar = st.form_submit_button("💾 Salvar Alterações", type="primary", use_container_width=True)

        if salvar:
            atualizar_produto(int(row["id"]), novo_nome.strip(), novo_ean.strip(),
                              novo_preco, nova_qtd, nova_val)
            st.success(f"✅ **{novo_nome}** atualizado com sucesso!")
            st.rerun()

    with tab_excluir:
        st.warning(f"Tem certeza que deseja excluir **{nome_sel}**? Esta ação não pode ser desfeita.")
        if st.button("🗑️ Confirmar Exclusão", type="primary", use_container_width=True):
            deletar_produto(int(row["id"]))
            st.success(f"✅ **{nome_sel}** removido do estoque.")
            st.rerun()


# ─────────────────────────────────────────────
# PÁGINA: BAIXA DE CAIXA
# ─────────────────────────────────────────────

elif pagina == "🛍️ Baixa de Caixa":
    st.title("🛍️ Baixa de Caixa")
    st.caption("Registre a saída de itens vendidos. O estoque é debitado automaticamente.")

    df = listar_produtos()
    df_com_estoque = df[df["quantidade"] > 0] if not df.empty else pd.DataFrame()

    if df_com_estoque.empty:
        st.warning("Nenhum produto com estoque disponível.")
        st.stop()

    # Monta mapa nome → row para lookup rápido
    opcoes = df_com_estoque["nome"].tolist()

    with st.form("form_baixa", clear_on_submit=True):
        c1, c2 = st.columns([3, 1])
        nome_prod = c1.selectbox("Produto", opcoes)
        row_prod  = df_com_estoque[df_com_estoque["nome"] == nome_prod].iloc[0]

        c1.caption(f"Estoque atual: **{int(row_prod['quantidade'])} un** · Preço: **R$ {row_prod['preco']:.2f}**")

        qtd_baixa = c2.number_input("Quantidade", min_value=1,
                                    max_value=int(row_prod["quantidade"]), step=1, value=1)
        total_prev = qtd_baixa * float(row_prod["preco"])
        st.info(f"💰 Total previsto: **R$ {total_prev:.2f}**")

        registrar = st.form_submit_button("✅ Registrar Baixa", type="primary", use_container_width=True)

    if registrar:
        msg = registrar_saida(
            int(row_prod["id"]),
            row_prod["nome"],
            qtd_baixa,
            float(row_prod["preco"]),
        )
        if msg.startswith("✅"):
            st.success(msg)
            st.rerun()
        else:
            st.error(msg)

    st.markdown("---")
    st.subheader("Estoque Disponível")
    st.dataframe(
        df_com_estoque[["nome","quantidade","preco","validade"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "nome":       st.column_config.TextColumn("Produto"),
            "quantidade": st.column_config.NumberColumn("Qtd", width="small"),
            "preco":      st.column_config.NumberColumn("Preço", format="R$ %.2f"),
            "validade":   st.column_config.DateColumn("Validade", format="DD/MM/YYYY"),
        },
    )


# ─────────────────────────────────────────────
# PÁGINA: HISTÓRICO DE SAÍDAS
# ─────────────────────────────────────────────

elif pagina == "📋 Histórico de Saídas":
    st.title("📋 Histórico de Saídas")

    df_s = listar_saidas()

    if df_s.empty:
        st.info("Nenhuma saída registrada ainda.")
        st.stop()

    total_dia   = df_s[df_s["registrado_em"].str.startswith(str(date.today()))]["total"].sum()
    total_geral = df_s["total"].sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("💵 Vendas Hoje (R$)", f"R$ {total_dia:.2f}")
    c2.metric("📦 Baixas Hoje", len(df_s[df_s["registrado_em"].str.startswith(str(date.today()))]))
    c3.metric("💰 Total Histórico (R$)", f"R$ {total_geral:.2f}")

    st.markdown("---")
    st.dataframe(
        df_s[["registrado_em","produto_nome","quantidade","preco_unit","total"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "registrado_em":  st.column_config.TextColumn("Data/Hora"),
            "produto_nome":   st.column_config.TextColumn("Produto"),
            "quantidade":     st.column_config.NumberColumn("Qtd", width="small"),
            "preco_unit":     st.column_config.NumberColumn("Preço Unit.", format="R$ %.2f"),
            "total":          st.column_config.NumberColumn("Total", format="R$ %.2f"),
        },
    )
