def test_register_agent_success(test_client): # A fixture 'test_client' vem de conftest.py
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
    assert "password_hash" not in data # Garante que o hash da senha não é retornado

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