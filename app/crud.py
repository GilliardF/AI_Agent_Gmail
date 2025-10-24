from sqlalchemy.orm import Session
from app import models, schemas, security

def get_agent_by_email(db: Session, email: str) -> models.Account | None:
    return db.query(models.Account).filter(models.Account.email == email).first()

def get_agent_by_id(db: Session, agent_id: int) -> models.Account | None:
    return db.query(models.Account).filter(models.Account.id == agent_id).first()

def create_agent(db: Session, agent: schemas.AgentCreate) -> models.Account:
    hashed_password = security.hash_password(agent.password)
    db_agent = models.Account(
        email=agent.email,
        name=agent.name,
        password_hash=hashed_password
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

# --- CRUD para E-mails Recebidos ---

def get_received_email_by_gmail_id(db: Session, gmail_message_id: str) -> models.ReceivedEmail | None:
    """
    Busca um e-mail recebido pelo seu ID do Gmail.
    """
    return db.query(models.ReceivedEmail).filter(models.ReceivedEmail.gmail_message_id == gmail_message_id).first()

def create_received_email(db: Session, email_data: schemas.ReceivedEmailCreate) -> models.ReceivedEmail:
    """
    Cria e armazena um novo e-mail recebido no banco de dados.
    """
    db_email = models.ReceivedEmail(**email_data.model_dump())
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    return db_email

def get_or_create_received_email(db: Session, email_data: schemas.ReceivedEmailCreate) -> models.ReceivedEmail:
    """
    Obtém um e-mail do banco de dados se ele existir (com base no gmail_message_id),
    caso contrário, cria um novo.
    """
    db_email = get_received_email_by_gmail_id(db, email_data.gmail_message_id)
    if not db_email:
        db_email = create_received_email(db, email_data)
    return db_email


# --- CRUD para Resumos de E-mail ---

def create_email_summary(db: Session, summary_data: schemas.EmailSummaryCreate) -> models.EmailSummary:
    """
    Cria e armazena um novo resumo de e-mail no banco de dados.
    """
    db_summary = models.EmailSummary(
        received_email_id=summary_data.received_email_id,
        summary_text=summary_data.summary_text,
        forward_url=summary_data.forward_url,
        forward_status=models.ForwardStatusEnum.pending  # Inicia como pendente
    )
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)
    return db_summary

def get_summary_by_id(db: Session, summary_id: int) -> models.EmailSummary | None:
    """
    Busca um resumo de e-mail específico pelo seu ID.
    """
    return db.query(models.EmailSummary).filter(models.EmailSummary.id == summary_id).first()

def update_summary_status(
    db: Session, 
    summary_id: int, 
    status: models.ForwardStatusEnum, 
    status_message: str | None = None
) -> models.EmailSummary | None:
    """
    Atualiza o status de encaminhamento de um resumo de e-mail.
    """
    db_summary = get_summary_by_id(db, summary_id)
    if db_summary:
        db_summary.forward_status = status
        db_summary.status_message = status_message
        db.commit()
        db.refresh(db_summary)
    return db_summary