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

def link_gmail_credentials(db: Session, agent: models.Account, credentials: schemas.GmailCredentials) -> models.Account:
    credentials_to_encrypt = {
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "refresh_token": credentials.refresh_token,
    }
    encrypted_creds = security.encrypt_data(credentials_to_encrypt)
    agent.encrypted_credentials = encrypted_creds
    db.commit()
    db.refresh(agent)
    return agent