import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db

# Usa um banco de dados SQLite em memória para os testes
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Necessário para SQLite
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Fixture para criar e limpar o banco de dados para cada teste."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_client(db_session):
    """
    Fixture para criar um cliente de teste com o banco de dados de teste.
    Usa a fixture db_session para garantir que o banco de dados é criado e limpo.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass # A sessão é fechada pelo fixture db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    # Limpa o override após o teste
    app.dependency_overrides.clear()