from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


ph = PasswordHasher()

def hash_password(password: str) -> str:
    """Gera o hash de uma senha usando Argon2id."""
    return ph.hash(password)

def verify_password(hashed_password: str, password: str) -> bool:
    """Verifica se a senha corresponde ao hash armazenado."""
    try:
        ph.verify(hashed_password, password)
        return True
    except VerifyMismatchError:
        return False
