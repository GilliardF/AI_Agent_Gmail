import json
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings

# --- SEÇÃO 1: HASHING DE SENHAS (Argon2) ---
ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(hashed_password: str, password: str) -> bool:
    try:
        ph.verify(hashed_password, password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False

# --- SEÇÃO 2: CRIPTOGRAFIA DE DADOS (Fernet) ---
ENCRYPTION_KEY_BYTES = settings.ENCRYPTION_KEY.encode('utf-8')
fernet = Fernet(ENCRYPTION_KEY_BYTES)

def encrypt_data(data: dict) -> bytes:
    json_string = json.dumps(data)
    data_bytes = json_string.encode('utf-8')
    return fernet.encrypt(data_bytes)

def decrypt_data(encrypted_data: bytes) -> dict:
    try:
        decrypted_bytes = fernet.decrypt(encrypted_data)
        json_string = decrypted_bytes.decode('utf-8')
        return json.loads(json_string)
    except InvalidToken:
        raise ValueError("Token de criptografia inválido. Verifique sua chave ou os dados.")
    except Exception as e:
        raise ValueError(f"Erro ao descriptografar dados: {e}")