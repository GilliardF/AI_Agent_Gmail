# Em routers/agents.py

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app import crud, schemas, security
from app.database import get_db
from app.services.email_service import process_and_reply_to_emails, send_new_email

router = APIRouter(
    prefix="/agents",
    tags=["Agents"]
)

# --- Endpoint de registro (sem alterações) ---
@router.post("/register", response_model=schemas.AgentResponse, status_code=status.HTTP_201_CREATED)
def register_agent(agent: schemas.AgentCreate, db: Session = Depends(get_db)):
    # ... (código original sem alterações)
    db_agent = crud.get_agent_by_email(db, email=agent.email)
    if db_agent:
        raise HTTPException(status_code=400, detail="E-mail já registrado.")
    return crud.create_agent(db=db, agent=agent)


# --- Endpoint de login (sem alterações) ---
@router.post("/login")
def login_agent(agent_data: schemas.AgentLogin, db: Session = Depends(get_db)):
    # ... (código original sem alterações)
    db_agent = crud.get_agent_by_email(db, email=agent_data.email)
    if not db_agent or not security.verify_password(db_agent.password_hash, agent_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"message": f"Login bem-sucedido para o agente {db_agent.email}!"}


# 2. --- ALTERADO: Endpoint de processamento de e-mails ---
@router.post("/{agent_id}/process-emails") # Removido o response_model obsoleto
async def trigger_email_processing(agent_id: int, db: Session = Depends(get_db)):
    """
    Inicia o processo de leitura de e-mails não lidos, geração de resposta com IA e envio.
    """
    agent = crud.get_agent_by_id(db, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")

    try:
        # Chama a nova função refatorada
        processed_count = await process_and_reply_to_emails(db=db, agent=agent)
        
        # Retorna uma resposta simples e direta
        return {
            "message": f"Processamento concluído. {processed_count} e-mails foram processados e respondidos."
        }
    except ConnectionError as e:
        if "não autorizou o acesso" in str(e) or "Credenciais inválidas" in str(e):
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Erro de conexão com o serviço do Google: {e}")
    except Exception as e:
        # Um bloco de captura genérico para outros erros inesperados
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ocorreu um erro inesperado: {str(e)}")


# --- Endpoints de autorização OAuth2 (sem alterações) ---
@router.get("/{agent_id}/authorize/google", summary="Gerar URL de autorização do Google")
def authorize_google_for_agent(agent_id: int, db: Session = Depends(get_db)) -> dict:
    # ... (código original sem alterações)
    agent = crud.get_agent_by_id(db, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")

    try:
        flow = security.create_google_auth_flow()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Falha ao criar o fluxo de autorização do Google: {e}")
    
    authorization_url, state = flow.authorization_url(
        access_type='offline', 
        prompt='consent',
        state=str(agent_id)
    )
    
    return {"authorization_url": authorization_url}


@router.get("/auth/google/callback", summary="Callback da autorização do Google", response_class=HTMLResponse)
def google_auth_callback(request: Request, db: Session = Depends(get_db)) -> str:
    # ... (código original sem alterações)
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    error = request.query_params.get('error')

    if error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail=f"A autorização foi negada pelo usuário: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Parâmetros 'code' ou 'state' ausentes no callback.")

    agent_id = int(state)
    agent = crud.get_agent_by_id(db, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agente com ID {agent_id} não encontrado.")

    flow = security.create_google_auth_flow()
    flow.fetch_token(code=code)
    
    crud.update_agent_credentials(db, agent=agent, creds=flow.credentials)
    
    html_content = f"""
    <html>
        <body>
            <h1>Autorização Concluída com Sucesso!</h1>
            <p>O agente <strong>{agent.email}</strong> foi autorizado com sucesso.</p>
        </body>
    </html>
    """
    return html_content


@router.post("/{agent_id}/emails/send", status_code=status.HTTP_202_ACCEPTED, summary="Enviar um e-mail simples")
def send_simple_email(agent_id: int, email_data: schemas.SendEmailRequest, db: Session = Depends(get_db)):
    """
    Envia um novo e-mail a partir da conta do agente para um destinatário específico.
    """
    agent = crud.get_agent_by_id(db, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")
    
    try:
        service = security.get_agent_gmail_service(agent=agent, db=db)
        send_new_email(
            service=service,
            to=email_data.receiver,
            subject=email_data.subject,
            body_text=email_data.body
        )
        return {"message": f"E-mail para {email_data.receiver} foi enviado para a fila de envio."}
    except ConnectionError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ocorreu um erro inesperado: {str(e)}")
