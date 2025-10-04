from pydantic_settings import BaseSettings, SettingsConfigDict

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
    POSTGRES_PORT: int = 5130  # Sua porta customizada

    # --- Variável de Segurança ---
    ENCRYPTION_KEY: str

    @property
    def database_url(self) -> str:
        """Gera a URL de conexão para o SQLAlchemy."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

settings = Settings()