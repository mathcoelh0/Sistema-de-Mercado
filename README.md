# Sistema de Gestão de Estoque e PDV

Sistema de controle de estoque e ponto de venda desenvolvido para mercado local, com foco em rastreabilidade de saídas, alertas de validade e auditoria de erros.

## Tecnologias

- **Python 3.11+** com **FastAPI**
- **SQLite** (banco local) + **SQLAlchemy 2.0** + **Alembic** (migrações)
- **Pydantic v2** para validação de dados
- **passlib[bcrypt]** + **python-jose** para autenticação

## Funcionalidades

- Cadastro e CRUD completo de produtos (com EAN/código de barras)
- Registro de vendas com **débito automático e atômico de estoque**
- Alerta de produtos próximos ao vencimento (janela de dias configurável)
- Listagem de produtos já vencidos com estoque ativo
- Níveis de acesso: **Admin** e **Operador**
- Log de auditoria exclusivo para erros de saída de estoque

## Estrutura do Projeto

```
app/
├── main.py                   # Entrypoint FastAPI
├── database.py               # Configuração do banco e sessão
├── core/
│   ├── config.py             # Variáveis de ambiente
│   ├── security.py           # Hash de senha e JWT
│   └── logging_config.py     # Logs gerais e de auditoria
├── models/                   # Tabelas: Produto, Venda, ItemVenda, Usuario
├── schemas/                  # Validação Pydantic (entrada e saída)
├── routers/                  # Endpoints HTTP
│   ├── produtos.py
│   └── vendas.py
└── services/
    ├── estoque_service.py    # Lógica de venda e débito de estoque
    └── validade_service.py   # Consultas de validade
alembic/                      # Migrações de banco
logs/                         # Gerado em runtime
```

## Instalação

**Pré-requisitos:** Python 3.11+

```bash
# 1. Clone o repositório
git clone https://github.com/mathcoelh0/Sistema-de-Mercado.git
cd Sistema-de-Mercado

# 2. Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
.venv\Scripts\activate         # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env e troque o SECRET_KEY por uma string segura

# 5. Suba o servidor
uvicorn app.main:app --reload
```

O banco de dados (`mercado.db`) é criado automaticamente na primeira execução.

## Documentação da API

Com o servidor rodando, acesse:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## Principais Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/produtos/` | Lista todos os produtos |
| `POST` | `/produtos/` | Cadastra novo produto |
| `PATCH` | `/produtos/{id}` | Atualiza produto |
| `DELETE` | `/produtos/{id}` | Remove produto |
| `GET` | `/produtos/validade/alerta?dias=30` | Produtos que vencem nos próximos N dias |
| `GET` | `/produtos/validade/vencidos` | Produtos com validade expirada |
| `POST` | `/vendas/` | Registra venda e debita estoque |
| `GET` | `/vendas/` | Lista vendas recentes |

## Migrações com Alembic

```bash
# Gerar nova migration após alterar models
alembic revision --autogenerate -m "descricao_da_mudanca"

# Aplicar migrations pendentes
alembic upgrade head
```

## Logs de Auditoria

Toda tentativa de saída com estoque insuficiente ou produto inexistente é gravada em:

```
logs/estoque_erros.log
```

Formato: `data | hora | nível | produto_id | disponível | solicitado | operador_id`
