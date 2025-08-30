from pydantic import BaseModel, EmailStr


# --- Schema para a entrada de dados ---
class AgentBase(BaseModel):
    email: EmailStr


class AgentCreate(AgentBase):
    password: str
    name: str


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

    class Config:
        from_attributes = True