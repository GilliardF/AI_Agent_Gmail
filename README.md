# AI Agent - Gmail

![Python](https://img.shields.io/badge/Python-3.13+-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-28+-blue?logo=docker&logoColor=white)

Este projeto é uma API construída com FastAPI para criar e gerenciar Agentes de Inteligência Artificial que podem interagir com contas do Gmail. A Fase 1 foca na gestão segura de agentes e no armazenamento criptografado de suas credenciais de API.

## Estrutura de Arquivos

A estrutura do projeto foi projetada para ser escalável e organizada, seguindo o padrão de **Separação de Responsabilidades**.

```
AI_Agent_Gmail/
├── app/
│   ├── __init__.py         # Torna 'app' um pacote Python
│   ├── config.py           # Carrega e valida as variáveis de ambiente
│   ├── crud.py             # Lógica de interação com o banco de dados (CRUD)
│   ├── database.py         # Configuração da conexão com o banco (SQLAlchemy)
│   ├── main.py             # Ponto de entrada da API FastAPI e montagem dos módulos
│   ├── models.py           # Definição das tabelas com SQLAlchemy ORM
│   ├── routers/
│   │   ├── __init__.py
│   │   └── agents.py       # Endpoints (rotas) relacionados aos Agentes
│   ├── schemas.py          # "Contratos" da API com Pydantic (validação de dados)
│   └── security.py         # Lógica de hashing (Argon2) e criptografia (Fernet)
│
├── .env
├── .gitignore              
├── docker-compose.yml      # Configuração para orquestrar os serviços (API e DB) com Docker
└── requirements.txt        
```

## Funcionalidades (Fase 1)

-   **Registro de Agentes:** Endpoint para criar um novo agente com nome, e-mail e senha.
-   **Autenticação de Agentes:** Endpoint de login para verificar as credenciais do agente.
-   **Segurança de Senhas:** As senhas dos agentes são protegidas usando o algoritmo de hashing **Argon2**.
-   **Vinculação Segura de Credenciais:** Endpoint para adicionar credenciais da API do Google (client_id, client_secret, refresh_token) a um agente existente.
-   **Criptografia Forte:** As credenciais do Google são criptografadas usando **AES-128 (via Fernet)** antes de serem salvas no banco de dados, garantindo que nunca sejam armazenadas em texto plano.

## Configuração do Ambiente

Para rodar o projeto, seja localmente ou em deploy, configure corretamente as variáveis de ambiente no arquivo `.env`.

### 1. Criando o Arquivo `.env`

Na raiz do projeto, crie um arquivo chamado `.env`.

### 2. Preenchendo as Variáveis de Ambiente

Copie o conteúdo abaixo para o seu arquivo `.env` e substitua os valores pelos seus.

```ini
# --- Configurações do Banco de Dados ---
# Substitua com suas credenciais do PostgreSQL
POSTGRES_DB=db-gmail
POSTGRES_USER=usuario_123
POSTGRES_PASSWORD=sua_senha_segura_aqui
POSTGRES_HOST=localhost # Mude para o nome do serviço Docker se estiver usando docker-compose (ex: 'db')
POSTGRES_PORT=5130 # Mudança de porta por questões de segurança

# --- Configurações de Segurança ---
# Chave usada para criptografar e descriptografar as credenciais do Gmail.
# IMPORTANTE: Gere uma chave única e segura!
ENCRYPTION_KEY=sua_chave_de_criptografia_aqui

# --- Configurações das APIs do Google (para fases futuras) ---
GEMINI_API_KEY="sua_chave_do_gemini_aqui"
GMAIL_CLIENT_ID="seu_client_id_do_google_cloud_aqui"
GMAIL_CLIENT_SECRET="seu_client_secret_do_google_cloud_aqui"
```

### 3. Como Gerar a `ENCRYPTION_KEY`

Para garantir a máxima segurança, você deve gerar uma chave criptográfica forte. Com seu ambiente virtual ativado, execute o seguinte comando no terminal **uma única vez**:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copie a chave gerada e cole-a no valor de `ENCRYPTION_KEY` no seu arquivo `.env`.

## Como Rodar o Projeto

### Rodando Localmente (Desenvolvimento)

1.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No macOS/Linux
    # venv\Scripts\activate   # No Windows
    ```

2.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Inicie o servidor da API:**
    ```bash
    uvicorn app.main:app --port 5000
    ```
    *   `--port 5000`: Define a porta em que a API irá rodar (ajuste se necessário).

4.  **Acesse a API:**
    *   **Documentação Interativa (Swagger UI):** [http://127.0.0.1:5000/docs](http://127.0.0.1:5000/docs)
    *   **Documentação Alternativa (ReDoc):** [http://127.0.0.1:5000/redoc](http://127.0.0.1:5000/redoc)


### Rodando com Docker

O `docker-compose.yml` está configurado para iniciar a API e o banco de dados PostgreSQL.

1.  **Garanta que o Docker e o Docker Compose estejam instalados.**
2.  **Ajuste o `.env`:** Mude a variável `POSTGRES_HOST` de `localhost` para o nome do serviço do banco de dados no `docker-compose.yml` (geralmente `db`).
3.  **Construa e inicie os contêineres:**
    ```bash
    docker-compose up --build
    ```
    A API estará acessível na mesma porta configurada (ex: `http://localhost:5000`).