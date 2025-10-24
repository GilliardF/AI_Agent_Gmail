----
# AI Agent para Gmail

!Python
!FastAPI
!PostgreSQL
!Docker
!GitHub Actions

Este projeto é uma API de backend construída com **FastAPI** que cria e gerencia "Agentes de IA". Cada agente pode se conectar de forma segura a uma conta do Gmail para ler e-mails não lidos, resumi-los usando um modelo de linguagem (LLM) como o Google Gemini e encaminhar os resumos para um webhook pré-definido.

---

## 📜 Tabela de Conteúdos

- ✨ Funcionalidades Principais
- 🛠️ Tecnologias Utilizadas
- ⚙️ Guia de Instalação e Execução Local
  - Pré-requisitos
  - Passo 1: Clonar o Repositório
  - Passo 2: Configurar Credenciais da API do Google
  - Passo 3: Configurar Variáveis de Ambiente (.env)
  - Passo 4: Gerar a Chave de Criptografia
  - Passo 5: Instalar Dependências
  - Passo 6: Iniciar o Banco de Dados com Docker
  - Passo 7: Rodar a Aplicação
- 🚀 Como Usar a API
  - 1. Registrar um Novo Agente
  - 2. Acionar o Processamento de E-mails
- ☁️ Deploy (CI/CD com GitHub Actions)

---

## ✨ Funcionalidades Principais

- **🤖 Gestão de Agentes:** Crie e gerencie múltiplos agentes, cada um com suas próprias credenciais e configurações.
- **📧 Automação de E-mail:**
  - **Leitura Inteligente:** Conecta-se a uma conta do Gmail e busca apenas e-mails não lidos para processamento.
  - **Sumarização com IA:** Utiliza a API do Google Gemini para gerar resumos concisos e inteligentes em português.
  - **Encaminhamento via Webhook:** Envia os resumos gerados para uma URL de destino (`POST`), permitindo integração com outros sistemas (Slack, Discord, etc.).
  - **Marcação Automática:** Marca os e-mails como lidos no Gmail após o processamento para evitar duplicidade.
- **🔒 Segurança Robusta:**
  - **Hashing de Senhas:** Senhas de agentes são protegidas com **Argon2**, um algoritmo moderno e seguro.
  - **Autenticação OAuth 2.0:** Utiliza o fluxo de autorização padrão do Google para acessar a API do Gmail, garantindo que as senhas do Google nunca sejam armazenadas.
  - **Criptografia de Credenciais:** Tokens de acesso e refresh do Google são criptografados com **AES (via Fernet)** antes de serem salvos no banco de dados.
- **📦 Containerização e Deploy:**
  - Configuração pronta para rodar o banco de dados PostgreSQL com Docker Compose.
  - Workflow de CI/CD para GitHub Actions que automatiza o build da imagem Docker e o deploy para o Azure App Service.

## 🛠️ Tecnologias Utilizadas

| Categoria | Tecnologia |
| :---------------- | :--------------------------------------- |
| **Backend** | FastAPI, Uvicorn |
| **Banco de Dados**| PostgreSQL |
| **ORM** | SQLAlchemy |
| **Validação** | Pydantic |
| **Segurança** | Argon2 (Hashing), Fernet (Criptografia) |
| **APIs Externas** | Google Gmail API, Google Gemini API |
| **Container** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |

## ⚙️ Guia de Instalação e Execução Local

Siga estes passos detalhados para configurar e executar o projeto em seu ambiente de desenvolvimento.

### Pré-requisitos

Antes de começar, garanta que você tenha as seguintes ferramentas instaladas:

- Python 3.13+
- Docker e Docker Compose
- Git
- Uma Conta Google para os testes.

### Passo 1: Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/AI_Agent_Gmail.git
cd AI_Agent_Gmail
```

### Passo 2: Configurar Credenciais da API do Google

Esta é a etapa mais importante para permitir que a aplicação acesse o Gmail.

1.  Acesse o **Google Cloud Console**.
2.  Crie um novo projeto (ou selecione um existente).
3.  No menu de busca, procure por **"Gmail API"** e ative-a para o seu projeto.
4.  No menu lateral, vá para **"APIs e serviços" > "Tela de permissão OAuth"**:
    -   Selecione **"Externo"** e clique em "Criar".
    -   Preencha as informações obrigatórias (nome do app, e-mail de suporte).
    -   Na tela de **"Escopos"**, clique em "Adicionar ou remover escopos". Procure por `https://www.googleapis.com/auth/gmail.modify` e adicione-o. Este escopo permite ler e modificar e-mails (necessário para marcar como lido).
    -   Salve e continue.
    -   Na tela de **"Usuários de teste"**, adicione o endereço de e-mail da Conta Google que você usará para testar. **Este passo é crucial para que a autenticação funcione durante o desenvolvimento.**
5.  Agora, vá para **"APIs e serviços" > "Credenciais"**:
    -   Clique em **"+ CRIAR CREDENCIAIS"** e selecione **"ID do cliente OAuth"**.
    -   Em "Tipo de aplicativo", escolha **"Aplicativo para computador"**.
    -   Dê um nome para a credencial (ex: "AI Agent Local").
    -   Clique em "Criar".
6.  Uma janela pop-up aparecerá. Clique em **"FAZER O DOWNLOAD DO JSON"**.
7.  **MUITO IMPORTANTE:** Renomeie o arquivo baixado para `credentials.json` e mova-o para a **raiz do seu projeto**.

### Passo 3: Configurar Variáveis de Ambiente (.env)

Crie um arquivo chamado `.env` na raiz do projeto. Copie o conteúdo do exemplo abaixo e substitua os valores conforme indicado.

```ini
# .env - Arquivo de configuração de ambiente

# --- Configurações do Banco de Dados PostgreSQL ---
# Estes valores devem corresponder ao que está em docker-compose.yml
POSTGRES_DB=db_gmail_agent
POSTGRES_USER=gilliard
POSTGRES_PASSWORD=sua_senha_forte_aqui # Use uma senha complexa com letras, números e símbolos
POSTGRES_HOST=localhost # Para rodar a API localmente. Se a API rodar em Docker, mude para 'db'.
POSTGRES_PORT=5130

# --- Chave de Criptografia ---
# Gere uma chave única com o comando no Passo 4 e cole o resultado aqui.
ENCRYPTION_KEY=

# --- Configurações da API do Gmail ---
# Caminho para o arquivo JSON que você baixou do Google Cloud.
GMAIL_CREDENTIALS_PATH=credentials.json
# Escopos de permissão. O 'modify' permite ler e marcar como lido.
GMAIL_API_SCOPES=https://www.googleapis.com/auth/gmail.modify

# --- Configurações do Agente ---
# URL do webhook que receberá os resumos dos e-mails via POST.
# Use um serviço como https://webhook.site para gerar uma URL de teste.
FORWARD_POST_URL="https://webhook.site/seu-uuid-aqui"

# --- Chave da API do Google (Gemini) ---
# Necessária para a funcionalidade de resumo. Obtenha em https://aistudio.google.com/app/apikey
GOOGLE_API_KEY="sua-chave-aqui"
```

### Passo 4: Gerar a Chave de Criptografia

Execute este comando no terminal para gerar uma chave segura. Ela será usada para criptografar os tokens do Google no banco de dados.

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copie a chave gerada e cole-a no campo `ENCRYPTION_KEY` do seu arquivo `.env`.

### Passo 5: Instalar Dependências

É uma boa prática usar um ambiente virtual para isolar as dependências do projeto.

```bash
# Crie um ambiente virtual
python3 -m venv venv

# Ative o ambiente (macOS/Linux)
source venv/bin/activate
# No Windows, use: .\venv\Scripts\activate

# Instale os pacotes necessários
pip install -r requirements.txt
```

### Passo 6: Iniciar o Banco de Dados com Docker

O `docker-compose.yml` está configurado para ler as variáveis do banco de dados do seu arquivo `.env` e iniciar um contêiner PostgreSQL.

```bash
# Inicia o contêiner do PostgreSQL em segundo plano (-d)
docker compose up -d db
```

Para verificar se o contêiner está rodando, use `docker ps`. Você deverá ver um contêiner chamado `ai_agent_gmail-db-1` com o status "Up".

### Passo 7: Rodar a Aplicação

Com o banco de dados rodando e as dependências instaladas, inicie o servidor FastAPI.

```bash
# O comando uvicorn inicia o servidor.
# --reload faz com que ele reinicie automaticamente após salvar alterações no código.
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

A API estará disponível em `http://127.0.0.1:8000`.

Acesse a documentação interativa (Swagger UI) em **http://127.0.0.1:8000/docs** para explorar e testar a API.

---

## 🚀 Como Usar a API

Use a documentação interativa (`/docs`) para testar os endpoints facilmente.

### 1. Registrar um Novo Agente

- **Endpoint:** `POST /agents/register`
- **Descrição:** Cria um novo agente no sistema.
- **Corpo da Requisição:**
  ```json
  {
    "email": "agente007@email.com",
    "password": "uma_senha_bem_forte_123",
    "name": "Agente de Teste 007"
  }
  ```
- **Resposta:** Você receberá os dados do agente criado, incluindo seu `id`. Guarde este `id` para o próximo passo.

### 2. Acionar o Processamento de E-mails

- **Endpoint:** `POST /agents/{agent_id}/process-emails`
- **Descrição:** Inicia o fluxo de leitura, resumo e encaminhamento de e-mails não lidos.
- **Parâmetro de URL:** `agent_id` (o ID do agente registrado no passo anterior).

#### ⚠️ Atenção na Primeira Execução!

Na **primeira vez** que você chamar este endpoint, o fluxo de autorização OAuth 2.0 será iniciado no terminal onde o `uvicorn` está rodando:

1.  Uma mensagem aparecerá no terminal pedindo para você visitar uma URL do Google.
    ```
    Please visit this URL to authorize this application: https://accounts.google.com/o/oauth2/auth?response_type=code&...
    ```
2.  **Copie esta URL** e cole-a em um navegador web.
3.  Faça login com a conta Google que você configurou como **usuário de teste**.
4.  Conceda as permissões que a aplicação está solicitando (para ler e modificar e-mails).
5.  Após a autorização, você será redirecionado para uma página local e o terminal confirmará o sucesso. Um arquivo `token.json` será criado na raiz do projeto.

**As execuções futuras serão automáticas!** O sistema usará o `token.json` para se autenticar sem precisar da sua intervenção.

### Exemplo de Resposta

```json
{
  "message": "Processamento concluído. 2 e-mails processados.",
  "processed_emails": 2,
  "summaries_created": [
    {
      "received_email_id": 1,
      "summary_text": "O e-mail da equipe de marketing informa sobre a nova campanha de primavera, com lançamento previsto para a próxima semana. É solicitado que a equipe de design finalize os criativos até quarta-feira. O sentimento geral é de urgência e otimismo.",
      "forward_url": "https://webhook.site/seu-uuid-aqui",
      "id": 1,
      "forward_status": "success",
      "status_message": "Encaminhado com sucesso. Status: 200",
      "created_at": "2024-10-26T15:30:00Z"
    },
    {
      "received_email_id": 2,
      "summary_text": "...",
      "id": 2
    }
  ]
}
```

## ☁️ Deploy (CI/CD com GitHub Actions)

O repositório contém um workflow em `.github/workflows/login_ai-agent.yml` para automatizar o deploy para o **Azure App Service**.

**Como funciona:**
1.  **Gatilho:** O workflow é acionado a cada `push` na branch `login`.
2.  **Job `build-and-push`:**
    -   Faz o checkout do código.
    -   Loga no Azure e no Azure Container Registry (ACR).
    -   Constrói uma imagem Docker da aplicação.
    -   Envia a imagem para o seu ACR com uma tag única (o hash do commit).
3.  **Job `deploy`:**
    -   Loga no Azure novamente.
    -   Configura as variáveis de ambiente no App Service (puxando de GitHub Secrets).
    -   Implanta a nova imagem Docker do ACR para o App Service.

**Para usar este workflow, você precisa:**
1.  Criar os recursos necessários no Azure (App Service, Azure Container Registry, PostgreSQL).
2.  Configurar os **secrets** no seu repositório do GitHub (`AZUREAPPSERVICE_CLIENTID`, `POSTGRES_USER`, etc.) para que o GitHub Actions possa se autenticar e configurar a aplicação em produção.
