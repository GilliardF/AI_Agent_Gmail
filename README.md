# AI Agent para Gmail

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.13+">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/GitHub%20Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white" alt="GitHub Actions">
</p>

Este projeto é uma API de backend construída com **FastAPI** que cria e gerencia "Agentes de IA" multi-usuário. Cada agente pode autorizar o acesso à sua própria conta do Gmail de forma segura via OAuth 2.0. A aplicação lê os e-mails não lidos de cada agente, **utiliza um modelo de linguagem (LLM) como o Google Gemini para gerar uma resposta coerente** e, em seguida, **envia essa resposta de volta ao remetente original**, automatizando a comunicação.

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

- **🤖 Gestão Multi-Agente:** Crie e gerencie múltiplos agentes, cada um com seu próprio login e **conexão independente a uma conta do Gmail**.
- **📧 Automação de Resposta por Agente:**
  - **Conexão Segura e Individual:** Cada agente autoriza o acesso à sua própria caixa de entrada via OAuth 2.0. As credenciais nunca são compartilhadas.
  - **Leitura Inteligente:** Busca apenas e-mails não lidos para processamento.
  - **Geração de Respostas com IA:** Usa a API do Google Gemini para gerar respostas contextuais e coerentes em português.
  - **Envio Automático:** Envia a resposta gerada diretamente para o remetente original, mantendo a conversa na mesma *thread* do e-mail.
  - **Marcação Automática:** Marca os e-mails como lidos no Gmail após o processamento para evitar duplicidade.
- **🔒 Segurança Robusta:**
  - **Hashing de Senhas:** Senhas de agentes são protegidas com **Argon2**, um algoritmo moderno e seguro.
  - **Autenticação OAuth 2.0 por Agente:** Utiliza o fluxo de autorização padrão do Google, e as credenciais de cada agente são **criptografadas com Fernet (AES)** e armazenadas individualmente no banco de dados.
- **📦 Ambiente de Desenvolvimento e Testes:**
  - Banco de dados PostgreSQL gerenciado com Docker Compose para desenvolvimento.
  - Testes automatizados com `pytest` que rodam em um banco de dados SQLite em memória para isolamento e velocidade.
- **☁️ CI/CD (Exemplo):**
  - Workflow de exemplo para GitHub Actions que automatiza o build da imagem Docker e o deploy para o Azure App Service.

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

Esta é a etapa mais importante.

1.  Acesse o **Google Cloud Console**.
2.  Crie um novo projeto ou selecione um existente.
3.  Ative a **Gmail API** e a **Generative Language API** para o seu projeto.
4.  Vá para **"APIs e serviços" > "Tela de permissão OAuth"**:
    -   Selecione **"Externo"** e preencha as informações obrigatórias.
    -   Na tela de **"Escopos"**, adicione o escopo `https://mail.google.com/`. **Este escopo é essencial**, pois permite ler, modificar e **enviar** e-mails.
    -   Na tela de **"Usuários de teste"**, adicione o e-mail da Conta Google que você usará para os testes.
5.  Vá para **"APIs e serviços" > "Credenciais"**:
    -   Clique em **"+ CRIAR CREDENCIAIS"** e selecione **"ID do cliente OAuth"**.
    -   Tipo de aplicativo: **"Aplicativo da Web"**.
    -   Em **"URIs de redirecionamento autorizados"**, adicione `http://127.0.0.1:9000/agents/auth/google/callback`.
    -   Clique em "Criar" e **"FAZER O DOWNLOAD DO JSON"**.
6.  **MUITO IMPORTANTE:** Renomeie o arquivo baixado para `credentials.json` e mova-o para a **raiz do seu projeto**.
    
    > **⚠️ Aviso de Segurança:** O arquivo `credentials.json` contém segredos. Ele já está listado no `.gitignore` para impedir que seja enviado ao repositório. **Nunca remova esta linha do `.gitignore` e nunca compartilhe este arquivo.**
 
### 4. Configurar Variáveis de Ambiente (`.env`)

Primeiro, crie uma cópia do arquivo de exemplo:

```bash
cp .env.example .env
```

Agora, edite o arquivo `.env` e preencha os valores:

-   `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`: Credenciais para o banco de dados.
-   `GEMINI_API_KEY`: Sua chave de API para o Google Gemini (pode ser obtida no [Google AI Studio](https://aistudio.google.com/app/apikey)).
-   `ENCRYPTION_KEY`: Execute o comando abaixo para gerar uma chave segura e cole o resultado aqui.
    ```bash
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    ```

### 5. Instalar Dependências

Use um ambiente virtual para isolar os pacotes do projeto.

```bash
# Crie e ative um ambiente virtual
python3 -m venv venv
source venv/bin/activate
# No Windows: .\venv\Scripts\activate

# Instale os pacotes
pip install -r requirements.txt
```

### 6. Iniciar o Banco de Dados com Docker

```bash
docker compose up -d db
```

### 7. Rodar a Aplicação

```bash
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```

A API estará disponível em `http://127.0.0.1:9000`.
Acesse a documentação interativa (Swagger UI) em **http://127.0.0.1:9000/docs**.

---

## 🚀 Como Usar a API

O fluxo de uso envolve 3 etapas: **Registrar**, **Autorizar** e **Processar**.

### Etapa 1: Registrar um Novo Agente (`POST /agents/register`)

Crie um agente no sistema.

-   **Endpoint:** `POST /agents/register`
-   **Corpo da Requisição:**
    ```json
    {
      "email": "meu.agente@email.com",
      "password": "uma_senha_bem_forte_123",
      "name": "Agente de Teste"
    }
    ```
-   **Resposta:** Você receberá os dados do agente, incluindo seu `id`. Guarde este `id`.

### Etapa 2: Autorizar o Acesso ao Gmail (`GET /agents/{agent_id}/authorize/google`)

Esta etapa conecta a conta do agente à sua conta do Gmail. **Ela só precisa ser feita uma vez (ou novamente se a permissão for revogada).**

1.  Use `curl` no seu terminal para obter a URL de autorização. Substitua `{agent_id}` pelo ID obtido na etapa anterior.

    ```bash
    # Exemplo para o agente com ID = 1
    curl -X GET "http://127.0.0.1:9000/agents/1/authorize/google"
    ```

2.  A resposta será um JSON contendo a URL:

    ```json
    {
      "authorization_url": "https://accounts.google.com/o/oauth2/auth?response_type=code&client_id=..."
    }
    ```

3.  **Copie a URL completa** da resposta e cole-a em um navegador.
4.  Faça login com a conta Google que você configurou como **usuário de teste**.
5.  Conceda as permissões que a aplicação está solicitando.
6.  Após a autorização, você será redirecionado para uma página de sucesso, e as credenciais seguras serão salvas no banco de dados para este agente.

### Etapa 3: Acionar o Processamento de E-mails (`POST /agents/{agent_id}/process-emails`)

-   **Endpoint:** `POST /agents/{agent_id}/process-emails`
-   **Descrição:** Inicia o fluxo de leitura, geração de resposta e envio de e-mails não lidos.
-   **Exemplo de Resposta:**
    ```json
    {
      "message": "Processamento concluído. 2 e-mails foram processados e respondidos."
    }
    ```

---

## 🧪 Como Rodar os Testes Automatizados (Executando o Projeto em Modo de Teste)

O projeto possui uma suíte de testes completa que utiliza `pytest`. Ao executar os testes, você está, na prática, **executando uma versão de teste da sua aplicação** em um ambiente controlado e seguro.

**O que acontece durante os testes:**
-   A aplicação FastAPI é carregada em memória.
-   Um **banco de dados SQLite em memória** é criado e destruído para cada teste, garantindo total isolamento e não afetando seu banco de dados de desenvolvimento (PostgreSQL).
-   Chamadas para APIs externas (como Google Gmail e Gemini) são **simuladas (mocked)**, permitindo testar a lógica da sua API sem depender de serviços externos ou de uma conexão com a internet.

### Como Executar

1.  Certifique-se de que seu ambiente virtual (`venv`) está ativado.
2.  Verifique se todas as dependências, incluindo as de teste, estão instaladas:
    ```bash
    pip install -r requirements.txt
    ```
3.  Execute o Pytest na raiz do projeto. Use a flag `-v` para um output mais detalhado:

```bash
python -m pytest -v
```

---

## ☁️ Deploy (CI/CD com GitHub Actions)

O repositório contém um workflow em `.github/workflows/login_ai-agent.yml` para automatizar o deploy para o **Azure App Service**.

**Como funciona:**
1.  **Gatilho:** O workflow é acionado a cada `push` na branch `login`.
2.  **Job `build-and-push`:** Constrói uma imagem Docker e a envia para um Azure Container Registry (ACR).
3.  **Job `deploy`:** Implanta a nova imagem Docker do ACR para o Azure App Service.

**Para usar este workflow, você precisa:**
1.  Criar os recursos no Azure (App Service, ACR, PostgreSQL).
2.  Configurar os **secrets** no seu repositório do GitHub (`AZUREAPPSERVICE_CLIENTID`, `POSTGRES_USER`, etc.).