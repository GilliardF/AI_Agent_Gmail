import json
import os
from pathlib import Path

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

# --- SEÇÃO 3: AUTENTICAÇÃO COM API DO GOOGLE (GMAIL) ---
TOKEN_FILE = Path("token.json")

def get_gmail_service():
    """
    Realiza o fluxo de autenticação OAuth2 para a API do Gmail e retorna
    um objeto de serviço para interagir com a API.

    Gerencia um arquivo 'token.json' para armazenar as credenciais do usuário.
    """
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), settings.GMAIL_API_SCOPES.split(','))

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(settings.GMAIL_CREDENTIALS_PATH).exists():
                raise FileNotFoundError(
                    f"Arquivo de credenciais do Google não encontrado em: '{settings.GMAIL_CREDENTIALS_PATH}'. "
                    "Faça o download do seu 'credentials.json' no Google Cloud Console e "
                    "coloque-o no diretório raiz do projeto."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                settings.GMAIL_CREDENTIALS_PATH, settings.GMAIL_API_SCOPES.split(',')
            )
            # Verifica se as credenciais são do tipo correto
            if not flow.client_config.get("installed"):
                raise TypeError(
                    "Tipo de credencial inválido. O arquivo 'credentials.json' parece ser para um 'Aplicativo Web'. "
                    "Para esta aplicação, gere credenciais para um 'Aplicativo para computador' no Google Cloud Console."
                )

            creds = flow.run_local_server(port=0, open_browser=False)
        
        with TOKEN_FILE.open("w") as token:
             token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except HttpError as error:
        print(f"Ocorreu um erro ao construir o serviço do Gmail: {error}")
        return None
