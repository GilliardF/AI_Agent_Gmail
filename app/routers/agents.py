from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud, schemas, security
from app.database import get_db
from app.services import email_service

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


@router.post(
    "/{agent_id}/process-emails",
    response_model=schemas.SummarizeAndForwardResponse,
    summary="Processar e Resumir E-mails",
    description="Inicia o processo de leitura de e-mails não lidos, geração de resumos e encaminhamento via POST."
)
async def trigger_email_processing(agent_id: int, db: Session = Depends(get_db)):
    """
    Endpoint para acionar o processo de sumarização de e-mails para um agente específico.

    - **agent_id**: O ID do agente para o qual os e-mails serão processados.
    """
    db_agent = crud.get_agent_by_id(db, agent_id=agent_id)
    if db_agent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agente não encontrado")

    try:
        processed_summaries = await email_service.process_and_summarize_emails(db=db, account_id=agent_id)
        
        return schemas.SummarizeAndForwardResponse(
            message=f"Processamento concluído. {len(processed_summaries)} e-mails processados.",
            processed_emails=len(processed_summaries),
            summaries_created=processed_summaries
        )
    except ConnectionError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        # Captura outras exceções inesperadas do serviço
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ocorreu um erro interno: {e}")