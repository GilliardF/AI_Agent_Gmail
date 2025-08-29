import psycopg2
from psycopg2.errors import UniqueViolation
from config import settings


def get_connection():
    """Cria e retorna uma nova conexão com o banco de dados."""
    return psycopg2.connect(settings.database_url)


def create_user(email: str, password_hash: str):
    """
    Insere um novo usuário na tabela accounts de forma segura.
    Levanta um ValueError se o email já estiver em uso (conflito de unicidade).
    """
    sql = "INSERT INTO accounts (email, password_hash) VALUES (%s, %s)"
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (email, password_hash))
    except UniqueViolation:
        raise ValueError("O email já está cadastrado.")
    except psycopg2.Error as e:
        raise RuntimeError(f"Erro inesperado no banco de dados: {e}")


def get_password_hash_for_user(email: str) -> str | None:
    """Busca o hash da senha de um usuário pelo email."""
    sql = "SELECT password_hash FROM accounts WHERE email = %s"
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (email,))
                result = cur.fetchone()
                return result[0] if result else None
    except psycopg2.Error as e:
        return None # Não registra erros de log
