from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, HttpUrl
from app.models import ForwardStatusEnum


# --- Schema para a entrada de dados ---
class AgentBase(BaseModel):
    email: EmailStr


class AgentCreate(AgentBase):
    password: str
    name: str
    forward_url: HttpUrl | None = None


class AgentLogin(AgentBase):
    password: str


class GmailCredentials(BaseModel):
    client_id: str
    client_secret: str
    refresh_token: str


# --- Schema para a saída de dados (respostas da API) ---
class AgentResponse(AgentBase):
    id: int
    name: str
    forward_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


# --- Schemas para E-mail Recebido ---

class ReceivedEmailBase(BaseModel):
    gmail_message_id: str
    account_id: int
    sender: str
    subject: str
    body: str | None = None
    received_at: datetime

class ReceivedEmailCreate(ReceivedEmailBase):
    pass

class ReceivedEmail(ReceivedEmailBase):
    id: int
    is_read: bool

    model_config = ConfigDict(from_attributes=True)


# --- Schemas para Resumo de E-mail ---

class EmailSummaryBase(BaseModel):
    received_email_id: int
    summary_text: str
    forward_url: str

class EmailSummaryCreate(EmailSummaryBase):
    pass

class EmailSummary(EmailSummaryBase):
    id: int
    forward_status: ForwardStatusEnum
    status_message: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SummarizeAndForwardResponse(BaseModel):
    message: str
    processed_emails: int
    summaries_created: list[EmailSummary]


# 1. Schema para a resposta do endpoint de LEITURA de e-mails
class EmailDetails(BaseModel):
    id: str
    thread_id: str
    sender: str
    subject: str
    body: str
    received_at: datetime

    # Usa a nova sintaxe do Pydantic v2 que você já está utilizando
    model_config = ConfigDict(from_attributes=True)


# 2. Schema para a requisição do endpoint de ENVIO de e-mail
class SendEmailRequest(BaseModel):
    receiver: EmailStr  # Valida automaticamente se o e-mail é válido
    subject: str
    body: str