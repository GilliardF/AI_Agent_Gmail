# Estrutura de arquivos

/AI_Agent_Gmail/
├── app/
│   ├── __init__.py
│   ├── crud.py             # Lógica de interação com o banco de dados
│   ├── database.py         # Configuração da conexão com o banco
│   ├── main.py             # Ponto de entrada da API FastAPI
│   ├── models.py           # Definição das tabelas com SQLAlchemy ORM
│   ├── schemas.py          # Definição dos "contratos" da API com Pydantic
│   ├── security.py         # Lógica de hashing e criptografia (seu arquivo ajustado)
│   ├── config.py           # Carregamento de variáveis de ambiente
│   └── routers/
│       ├── __init__.py     # Torna 'routers' um pacote Python
│       └── agents.py       # Endpoints relacionados aos agentes
│
├── sql/                    # Você pode manter para scripts de referência
│   ├── DDL.sql
│   ├── DML.sql 
│   └── SQL.sql
│
│
├── .env
├── .gitignore
├── docker-compose.yml
├── README.md
└── requirements.txt