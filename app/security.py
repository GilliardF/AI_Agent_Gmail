import json
import os
from pathlib import Path
from sqlalchemy.orm import Session

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.config import settings
from app import models, crud

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
def create_google_auth_flow() -> Flow:
    """Cria uma instância do fluxo de autorização do Google."""
    credentials_path = Path(settings.GMAIL_CREDENTIALS_PATH).resolve()
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Arquivo de credenciais do Google não encontrado em: '{credentials_path}'."
        )
    
    flow = Flow.from_client_secrets_file(
        client_secrets_file=credentials_path,
        scopes=settings.GMAIL_API_SCOPES.split(','),
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    return flow

def get_agent_gmail_service(agent: models.Account, db: Session):
    """
    Constrói um serviço da API do Gmail para um agente específico usando as
    credenciais criptografadas armazenadas no banco de dados.
    Gerencia a renovação do token de acesso, se necessário.
    """
    if not agent.encrypted_credentials:
        raise ConnectionError(f"O agente '{agent.email}' não autorizou o acesso ao Gmail.")

    # Descriptografa as credenciais do banco
    creds_dict = decrypt_data(agent.encrypted_credentials)
    creds = Credentials.from_authorized_user_info(creds_dict, settings.GMAIL_API_SCOPES.split(','))

    # Se as credenciais expiraram e um refresh_token existe, renova.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # CRUCIAL: Se o token foi renovado, salve as novas credenciais no banco
                new_creds_dict = {
                    'token': creds.token,
                    'refresh_token': creds.refresh_token,
                    'token_uri': creds.token_uri,
                    'client_id': creds.client_id,
                    'client_secret': creds.client_secret,
                    'scopes': creds.scopes
                }
                agent.encrypted_credentials = encrypt_data(new_creds_dict)
                db.commit()
                db.refresh(agent)
                print(f"Token para o agente {agent.email} foi renovado com sucesso.")
            except Exception as e:
                # Se a renovação falhar (ex: token revogado), limpe as credenciais
                agent.encrypted_credentials = None
                db.commit()
                raise ConnectionError(f"Não foi possível renovar o token para o agente {agent.email}. Por favor, autorize novamente. Erro: {e}")
        else:
            # Não há credenciais válidas ou refresh_token
            raise ConnectionError(f"Credenciais inválidas para o agente {agent.email}. Por favor, autorize o acesso.")

    try:
        service = build("gmail", "v1", credentials=creds)
        return service
    except HttpError as error:
        print(f"Ocorreu um erro ao construir o serviço do Gmail: {error}")
        return None
