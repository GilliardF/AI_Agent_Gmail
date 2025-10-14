from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus

class Settings(BaseSettings):
    """
    Gerencia as configurações da aplicação usando Pydantic.
    Lê automaticamente a partir de variáveis de ambiente e do arquivo .env.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra='ignore')

    # --- Variáveis do Banco de Dados ---
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5130  # Porta customizada

    # --- Variável de Segurança ---
    ENCRYPTION_KEY: str

    # --- Configurações da API do Gmail ---
    GMAIL_CREDENTIALS_PATH: str = "credentials.json"
    GMAIL_API_SCOPES: str = "https://www.googleapis.com/auth/gmail.modify"

    # --- Configurações do Agente ---
    FORWARD_POST_URL: str | None = None

    # --- Chave da API do Google (Gemini) ---
    GOOGLE_API_KEY: str

    @property
    def database_url(self) -> str:
        """Gera a URL de conexão para o SQLAlchemy."""
        encoded_password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql://{self.POSTGRES_USER}:{encoded_password}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()