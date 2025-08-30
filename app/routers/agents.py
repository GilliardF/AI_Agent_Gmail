from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas, security
from app.database import get_db

router = APIRouter(
    prefix="/agents",
    tags=["Agents"]
)


@router.post("/register", response_model=schemas.AgentResponse, status_code=status.HTTP_201_CREATED)
def register_agent(agent: schemas.AgentCreate, db: Session = Depends(get_db)):
    db_agent = crud.get_agent_by_email(db, email=agent.email)
    if db_agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já registrado."
        )
    return crud.create_agent(db=db, agent=agent)


@router.post("/login")
def login_agent(form_data: schemas.AgentLogin, db: Session = Depends(get_db)):
    agent = crud.get_agent_by_email(db, email=form_data.email)
    if not agent or not security.verify_password(agent.password_hash, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"message": f"Login bem-sucedido para o agente {agent.email}!"}


@router.put("/{agent_id}/gmail-credentials", response_model=schemas.AgentResponse)
def add_agent_gmail_credentials(
        agent_id: int,
        credentials: schemas.GmailCredentials,
        db: Session = Depends(get_db)
):
    db_agent = crud.get_agent_by_id(db, agent_id=agent_id)
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agente não encontrado")

    updated_agent = crud.link_gmail_credentials(db=db, agent=db_agent, credentials=credentials)
    return updated_agent