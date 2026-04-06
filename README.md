# 🛒 Sistema de Gestão de Mercado

Sistema de controle de estoque e ponto de venda desenvolvido para mercado local. Resolve os principais problemas operacionais: saídas não registradas, prejuízo com produtos vencidos e falta de visibilidade do caixa.

---

## Demonstração

> Execute localmente em 30 segundos — sem banco externo, sem configuração.

```bash
pip install streamlit
streamlit run streamlit_app.py
```

Ou acesse o deploy online no Streamlit Cloud:
**[Sistema de Mercado — Streamlit Cloud](https://share.streamlit.io)**

---

## Funcionalidades

| Tela | O que faz |
|---|---|
| **Dashboard** | KPIs de estoque, alertas visuais de produtos vencidos (🔴) e próximos do vencimento (🟡) |
| **Adicionar Produto** | Formulário com nome, EAN, quantidade, preço e data de validade |
| **Baixa de Caixa** | Debita estoque automaticamente ao registrar uma venda, com histórico auditável |
| **Histórico** | Total de vendas do dia, quantidade de baixas e tabela completa de saídas |

---

## Stack

### MVP — Interface (deploy imediato)

| Camada | Tecnologia |
|---|---|
| Interface | [Streamlit](https://streamlit.io) |
| Banco de dados | SQLite via `sqlite3` nativo do Python |
| Dependências | **apenas** `streamlit` |

### Backend API (boilerplate para expansão)

| Camada | Tecnologia |
|---|---|
| API | FastAPI + Uvicorn |
| ORM | SQLAlchemy 2.0 |
| Migrações | Alembic |
| Validação | Pydantic v2 |
| Autenticação | passlib[bcrypt] + python-jose (JWT) |

---

## Estrutura do Projeto

```
├── streamlit_app.py        # MVP funcional — rode direto com Streamlit
├── requirements.txt        # Apenas: streamlit
│
├── app/                    # Backend FastAPI (boilerplate para expansão)
│   ├── main.py
│   ├── database.py
│   ├── core/
│   │   ├── config.py       # Variáveis de ambiente (.env)
│   │   ├── security.py     # Hash bcrypt + geração de JWT
│   │   └── logging_config.py
│   ├── models/             # Produto, Venda, ItemVenda, Usuario
│   ├── schemas/            # Validação Pydantic (entrada e saída)
│   ├── routers/            # Endpoints HTTP (produtos, vendas)
│   └── services/
│       ├── estoque_service.py   # Débito atômico de estoque
│       └── validade_service.py  # Consultas por janela de dias
│
├── alembic/                # Migrações de banco
├── index.html              # Dashboard estático (Tailwind CSS)
└── logs/                   # Gerado em runtime (auditoria de erros)
```

---

## Como Rodar

### MVP Streamlit (recomendado para início rápido)

```bash
# 1. Clone o repositório
git clone https://github.com/mathcoelh0/Sistema-de-Mercado.git
cd Sistema-de-Mercado

# 2. Instale a dependência
pip install streamlit

# 3. Execute
streamlit run streamlit_app.py
```

O banco `mercado.db` é criado automaticamente na primeira execução.

### Backend FastAPI (para integração com outros sistemas)

```bash
# 1. Instale todas as dependências
pip install fastapi uvicorn sqlalchemy alembic passlib[bcrypt] python-jose pydantic pydantic-settings python-dotenv

# 2. Configure o ambiente
cp .env.example .env
# Edite o .env e defina um SECRET_KEY seguro

# 3. Execute
uvicorn app.main:app --reload
```

Documentação interativa disponível em `http://localhost:8000/docs`.

---

## Endpoints da API

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/produtos/` | Lista todos os produtos |
| `POST` | `/produtos/` | Cadastra novo produto |
| `PATCH` | `/produtos/{id}` | Atualiza produto |
| `DELETE` | `/produtos/{id}` | Remove produto |
| `GET` | `/produtos/validade/alerta?dias=7` | Produtos que vencem nos próximos N dias |
| `GET` | `/produtos/validade/vencidos` | Produtos com validade expirada |
| `POST` | `/vendas/` | Registra venda e debita estoque |
| `GET` | `/vendas/` | Lista vendas recentes |

---

## Níveis de Acesso

| Perfil | Permissões |
|---|---|
| **Admin** | Acesso total — cadastro, edição, exclusão, relatórios |
| **Operador** | Registro de vendas e baixa de estoque |

---

## Logs de Auditoria

Toda tentativa de saída com estoque insuficiente ou produto inexistente é gravada em:

```
logs/estoque_erros.log
```

---

## Deploy no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io) e conecte sua conta GitHub
2. **New app** → repositório `mathcoelh0/Sistema-de-Mercado`
3. Branch: `master` · Main file: `streamlit_app.py`
4. Clique em **Deploy**

Nenhuma variável de ambiente necessária — o banco SQLite é criado automaticamente na nuvem.
