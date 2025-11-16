import pytest
from unittest.mock import MagicMock, AsyncMock

# --- Testes para POST /agents/register ---


def test_register_agent_success(test_client):
    """Testa o registro bem-sucedido de um novo agente."""
    response = test_client.post(
        "/agents/register",
        json={
            "email": "test@example.com",
            "password": "a_strong_password",
            "name": "Test Agent",
            "forward_url": "https://webhook.site/test"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["forward_url"] == "https://webhook.site/test"
    assert "id" in data
    assert "password" not in data


def test_register_agent_duplicate_email(test_client):
    """Testa a falha ao registrar um agente com e-mail duplicado."""
    # Primeiro registro (deve funcionar)
    test_client.post(
        "/agents/register",
        json={"email": "duplicate@example.com", "password": "password123", "name": "First Agent"}
    )
    # Segunda tentativa com o mesmo e-mail (deve falhar)
    response = test_client.post(
        "/agents/register",
        json={"email": "duplicate@example.com", "password": "another_password", "name": "Second Agent"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "E-mail já registrado."


def test_register_agent_invalid_email(test_client):
    """Testa a falha ao registrar com um e-mail inválido."""
    response = test_client.post(
        "/agents/register",
        json={"email": "not-an-email", "password": "password123", "name": "Invalid Agent"},
    )
    assert response.status_code == 422  # Unprocessable Entity


# --- Testes para POST /agents/login ---


def test_login_agent_success(test_client):
    """Testa o login bem-sucedido de um agente."""
    # 1. Criar o agente primeiro
    test_client.post(
        "/agents/register",
        json={"email": "login@example.com", "password": "correct_password", "name": "Login Agent"}
    )
    # 2. Tentar fazer login
    response = test_client.post(
        "/agents/login",
        json={"email": "login@example.com", "password": "correct_password"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Login bem-sucedido para o agente login@example.com!"}


def test_login_agent_wrong_password(test_client):
    """Testa a falha de login com senha incorreta."""
    test_client.post(
        "/agents/register",
        json={"email": "login@example.com", "password": "correct_password", "name": "Login Agent"}
    )
    response = test_client.post(
        "/agents/login",
        json={"email": "login@example.com", "password": "wrong_password"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou senha incorretos"


def test_login_agent_nonexistent_user(test_client):
    """Testa a falha de login com um usuário que não existe."""
    response = test_client.post(
        "/agents/login",
        json={"email": "ghost@example.com", "password": "any_password"}
    )
    assert response.status_code == 401


# --- Testes para Endpoints com Dependências Externas (usando Mocks) ---

@pytest.fixture
def registered_agent(test_client):
    """Fixture para criar um agente e retornar seus dados."""
    response = test_client.post(
        "/agents/register",
        json={"email": "agent@example.com", "password": "password", "name": "Mock Agent"}
    )
    return response.json()


def test_authorize_google_success(test_client, mocker, registered_agent):
    """Testa se a URL de autorização do Google é gerada corretamente."""
    agent_id = registered_agent["id"]

    # Simula o fluxo de autorização do Google
    mock_flow = MagicMock()
    mock_flow.authorization_url.return_value = ("https://fake.google.com/auth", "fake_state")
    mocker.patch("app.routers.agents.security.create_google_auth_flow", return_value=mock_flow)

    response = test_client.get(f"/agents/{agent_id}/authorize/google")

    assert response.status_code == 200
    data = response.json()
    assert data["authorization_url"] == "https://fake.google.com/auth"
    # Verifica se o state correto foi passado para a função do Google
    mock_flow.authorization_url.assert_called_once_with(
        access_type='offline', prompt='consent', state=str(agent_id)
    )


def test_google_auth_callback_success(test_client, mocker, registered_agent):
    """Testa o callback bem-sucedido da autorização do Google."""
    agent_id = registered_agent["id"]

    # Simula as funções do fluxo e do CRUD
    mock_flow = MagicMock()
    mocker.patch("app.routers.agents.security.create_google_auth_flow", return_value=mock_flow)
    mock_update_creds = mocker.patch("app.routers.agents.crud.update_agent_credentials")

    response = test_client.get(f"/agents/auth/google/callback?code=fake_code&state={agent_id}")

    assert response.status_code == 200
    assert "Autorização Concluída com Sucesso!" in response.text
    # Verifica se o token foi "trocado" e as credenciais foram salvas
    mock_flow.fetch_token.assert_called_once_with(code="fake_code")
    mock_update_creds.assert_called_once()


def test_trigger_email_processing_success(test_client, mocker, registered_agent):
    """Testa o acionamento do processamento de e-mails."""
    agent_id = registered_agent["id"]

    # Simula a função de processamento para não executar a lógica real
    mock_process = mocker.patch(
        "app.routers.agents.process_and_reply_to_emails",
        new_callable=AsyncMock, # Usa AsyncMock para funções async
        return_value=3 # Simula que 3 e-mails foram processados
    )

    response = test_client.post(f"/agents/{agent_id}/process-emails")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Processamento concluído. 3 e-mails foram processados e respondidos."
    }
    mock_process.assert_awaited_once() # Verifica se a função async foi chamada


def test_trigger_email_processing_agent_not_found(test_client):
    """Testa o acionamento para um agente que não existe."""
    response = test_client.post("/agents/999/process-emails")
    assert response.status_code == 404
    assert response.json()["detail"] == "Agente não encontrado."


def test_send_simple_email_success(test_client, mocker, registered_agent):
    """Testa o envio de um e-mail simples."""
    agent_id = registered_agent["id"]

    # Simula os serviços de segurança e e-mail
    mock_get_service = mocker.patch("app.routers.agents.security.get_agent_gmail_service")
    mock_send_email = mocker.patch("app.routers.agents.send_new_email")

    email_data = {
        "receiver": "destinatario@example.com",
        "subject": "Teste de Envio",
        "body": "Este é um corpo de e-mail de teste."
    }
    response = test_client.post(f"/agents/{agent_id}/emails/send", json=email_data)

    assert response.status_code == 202
    assert response.json() == {"message": f"E-mail para {email_data['receiver']} foi enviado para a fila de envio."}

    # Verifica se os mocks foram chamados corretamente
    mock_get_service.assert_called_once()
    mock_send_email.assert_called_once_with(
        service=mock_get_service.return_value,
        to=email_data["receiver"],
        subject=email_data["subject"],
        body_text=email_data["body"]
    )