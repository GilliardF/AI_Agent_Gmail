# AI Agent para Gestão de Gmail

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/GitHub%20Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white" alt="GitHub Actions">
</p>

Este projeto é uma API de backend construída com **FastAPI** que cria e gerencia "Agentes de IA" multi-usuário. Cada agente pode autorizar o acesso à sua própria conta do Gmail de forma segura via OAuth 2.0. A aplicação permite **ler e listar e-mails recebidos**, **enviar novos e-mails para qualquer destinatário** e também possui um modo de **resposta automática com IA** para e-mails não lidos, utilizando um modelo de linguagem (LLM) como o Google Gemini.

---

## 📜 Tabela de Conteúdos

- ✨ Funcionalidades Principais
- 🛠️ Pilha de Tecnologias
- ⚙️ Guia de Instalação e Execução Local
- 🚀 Como Usar a API
- 🧪 Como Rodar os Testes Automatizados
- ☁️ Deploy (CI/CD com GitHub Actions)

---

## ✨ Funcionalidades Principais

- **🤖 Gestão Multi-Agente:** Crie e gerencie múltiplos agentes, cada um com seu próprio login e conexão independente a uma conta do Gmail.
- **📧 Gestão Completa de E-mail:**
  - **Leitura de Caixa de Entrada:** Obtenha uma lista dos e-mails mais recentes da caixa de entrada de um agente via API.
  - **Envio de E-mails:** Envie e-mails para qualquer destinatário diretamente da conta do agente através de um endpoint seguro.
  - **Resposta Automática com IA:** Um modo especializado que lê e-mails não lidos, gera respostas contextuais com o Google Gemini e as envia ao remetente original.
  - **Conexão Segura:** Cada agente autoriza o acesso via OAuth 2.0, e as credenciais são criptografadas e armazenadas individualmente.
- **🔒 Segurança Robusta:**
  - **Hashing de Senhas:** Senhas de agentes são protegidas com **Argon2**.
  - **Autenticação OAuth 2.0 por Agente:** As credenciais de cada agente são **criptografadas com Fernet (AES)** e salvas no banco de dados.
- **📦 Ambiente de Desenvolvimento e Testes:**
  - Banco de dados PostgreSQL gerenciado com Docker Compose.
  - Testes automatizados com `pytest` em um banco de dados SQLite em memória.
- **☁️ CI/CD (Exemplo):**
  - Workflow de exemplo para GitHub Actions para automatizar o deploy.

## 🛠️ Pilha de Tecnologias

| Categoria             | Tecnologia                                   |
| :-------------------- | :------------------------------------------- |
| **Backend**           | FastAPI, Uvicorn                             |
| **Banco de Dados**    | PostgreSQL                                   |
| **ORM**               | SQLAlchemy                                   |
| **Validação**         | Pydantic, Pydantic-Settings                  |
| **Segurança**         | Argon2 (Hashing), Cryptography (Fernet)      |
| **APIs Externas**     | Google Gmail API, Google Gemini API          |
| **Container**         | Docker, Docker Compose                       |
| **Testes**            | Pytest, Pytest-Asyncio, HTTPX                |
| **CI/CD (Exemplo)**   | GitHub Actions                               |

## ⚙️ Guia de Instalação e Execução Local

Siga estes passos detalhados para configurar e executar o projeto.

### 1. Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- Git
- Uma Conta Google para testes.

### 2. Clonar o Repositório

```bash
git clone https://github.com/GilliardF/AI_Agent_Gmail.git
cd AI_Agent_Gmail
```

### 3. Configurar Credenciais da API do Google

1.  Acesse o **Google Cloud Console**.
2.  Ative a **Gmail API** e a **Generative Language API**.
3.  Configure a **Tela de permissão OAuth** com o escopo `https://mail.google.com/` e adicione seu e-mail de teste.
4.  Crie um **ID do cliente OAuth** do tipo "Aplicativo da Web".
5.  Em **"URIs de redirecionamento autorizados"**, adicione `http://127.0.0.1:9000/agents/auth/google/callback`.
6.  Faça o **Download do JSON** das credenciais, renomeie o arquivo para `credentials.json` e mova-o para a raiz do projeto.

### 4. Configurar Variáveis de Ambiente (`.env`)

```bash
cp .env.example .env
```
Edite o arquivo `.env` e preencha `GEMINI_API_KEY` e `ENCRYPTION_KEY`.

### 5. Instalar Dependências e Rodar

```bash
# Instalar dependências (dentro de um venv)
pip install -r requirements.txt

# Iniciar o banco de dados
docker compose up -d db

# Rodar a aplicação
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```Acesse a documentação em **http://127.0.0.1:9000/docs**.

---

## 🚀 Como Usar a API

A interação segue um fluxo simples: primeiro, **registre** e **autorize** um agente. Depois, você pode usar os endpoints de gerenciamento de e-mail.

### Etapa 1: Registrar um Novo Agente (`POST /agents/register`)

-   **Descrição:** Cria um novo agente no sistema.
-   **Corpo da Requisição:**
    ```json
    { "email": "meu.agente@email.com", "password": "senha_forte_123", "name": "Agente Teste" }
    ```
-   **Resposta:** Você receberá o `id` do agente. Guarde-o.

### Etapa 2: Autorizar o Acesso ao Gmail (`GET /agents/{agent_id}/authorize/google`)

-   **Descrição:** Conecta a conta do agente à sua conta do Gmail (só precisa ser feito uma vez).
-   **Exemplo com `curl`:**
    ```bash
    curl -X GET "http://127.0.0.1:9000/agents/1/authorize/google"
    ```
-   **Ação:** Copie a `authorization_url` da resposta, cole em um navegador e conceda as permissões.

### Etapa 3: Gerenciar E-mails

Uma vez que o agente está autorizado, você pode usar os seguintes endpoints:

#### Ler E-mails Recebidos (`GET /agents/{agent_id}/emails`)
-   **Descrição:** Recupera uma lista dos e-mails mais recentes da caixa de entrada.
-   **Exemplo com `curl`:**
    ```bash
    curl -X GET "http://127.0.0.1:9000/agents/1/emails" | jq
    ```
-   **Exemplo de Resposta:** Uma lista de objetos JSON, cada um contendo `id`, `sender`, `subject`, `body`, etc.

#### Enviar um Novo E-mail (`POST /agents/{agent_id}/emails/send`)
-   **Descrição:** Envia um e-mail para um destinatário específico a partir da conta do agente.
-   **Exemplo com `curl`:**
    ```bash
    curl -X POST "http://127.0.0.1:9000/agents/1/emails/send" \
         -H "Content-Type: application/json" \
         -d '{
               "receiver": "destinatario@example.com",
               "subject": "Olá do Agente IA",
               "body": "Este e-mail foi enviado pela API."
             }'
    ```
-   **Exemplo de Resposta:** `{"message": "E-mail para ... foi colocado na fila de envio."}`

#### Processar e Responder E-mails com IA (`POST /agents/{agent_id}/process-emails`)
-   **Descrição:** Inicia o fluxo de leitura de e-mails **não lidos**, geração de resposta com IA e envio automático.
-   **Exemplo com `curl`:**
    ```
    curl -X POST "http://127.0.0.1:9000/agents/1/process-emails"
    ```
-   **Exemplo de Resposta:** `{"message": "Processamento concluído. X e-mails foram processados..."}`

---

## 🧪 Como Rodar os Testes Automatizados

```
pytest
```

---

## ☁️ Deploy (CI/CD com GitHub Actions)

O repositório contém um workflow em `.github/workflows/login_ai-agent.yml` para automatizar o deploy para o **Azure App Service**, que é acionado por pushes na branch `login`. Para usá-lo, configure os secrets do Azure no seu repositório do GitHub.