from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import logging # <--- ADICIONADO: Para ver logs no Azure
from app import crud, schemas, security
from app.database import get_db
from app.config import settings
from app.services.email_service import process_and_reply_to_emails, send_new_email

# Configura o logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agents",
    tags=["Agents"]
)

# --- Endpoint de registro ---
@router.post("/register", response_model=schemas.AgentResponse, status_code=status.HTTP_201_CREATED)
def register_agent(agent: schemas.AgentCreate, db: Session = Depends(get_db)):
    # Verifique se o logger funciona
    logger.info(f"Tentativa de registro para: {agent.email}")
    
    db_agent = crud.get_agent_by_email(db, email=agent.email)
    if db_agent:
        logger.warning(f"Email duplicado: {agent.email}")
        raise HTTPException(status_code=400, detail="E-mail já registrado.")
    return crud.create_agent(db=db, agent=agent)


# --- Endpoint de login ---
@router.post("/login")
def login_agent(agent_data: schemas.AgentLogin, db: Session = Depends(get_db)):
    db_agent = crud.get_agent_by_email(db, email=agent_data.email)
    if not db_agent or not security.verify_password(db_agent.password_hash, agent_data.password):
        logger.warning(f"Falha de login para: {agent_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"Login bem-sucedido para: {agent_data.email}")
    return {"message": f"Login bem-sucedido para o agente {db_agent.email}!"}


# 2. --- Endpoint de processamento de e-mails ---
@router.post("/{agent_id}/process-emails")
async def trigger_email_processing(agent_id: int, db: Session = Depends(get_db)):
    """
    Inicia o processo de leitura de e-mails não lidos, geração de resposta com IA e envio.
    """
    agent = crud.get_agent_by_id(db, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")

    try:
        logger.info(f"Iniciando processamento de emails para Agente ID: {agent_id}")
        processed_count = await process_and_reply_to_emails(db=db, agent=agent)
        logger.info(f"Sucesso. Emails processados: {processed_count}")
        
        return {
            "message": f"Processamento concluído. {processed_count} e-mails foram processados e respondidos."
        }
    except ConnectionError as e:
        logger.error(f"Erro de Conexão/Auth (Agente {agent_id}): {str(e)}")
        if "não autorizou o acesso" in str(e) or "Credenciais inválidas" in str(e):
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Erro de conexão com o serviço do Google: {e}")
    except Exception as e:
        logger.error(f"Erro Inesperado (Agente {agent_id}): {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ocorreu um erro inesperado: {str(e)}")


# --- Endpoints de autorização OAuth2 (CORRIGIDO REDIRECIONAMENTO) ---

@router.get("/{agent_id}/authorize/google", summary="Gerar URL de autorização do Google")
def authorize_google_for_agent(agent_id: int, db: Session = Depends(get_db)) -> dict:
    agent = crud.get_agent_by_id(db, agent_id=agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")

    try:
        # Cria o fluxo base
        flow = security.create_google_auth_flow()
        
        # --- CORREÇÃO PRINCIPAL ---
        # Sobrescreve o redirect_uri com o valor das configurações (Ambiente Azure ou Local)
        # Se GOOGLE_REDIRECT_URI for uma @property no config, use settings.google_redirect_uri
        # Se for uma variável direta, use settings.GOOGLE_REDIRECT_URI
        # Vou assumir que você definiu como variável direta no último passo.
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI 

        logger.info(f"Iniciando OAuth. Redirect URI configurada: {flow.redirect_uri}")

    except Exception as e:
        logger.error(f"Erro ao criar fluxo OAuth: {e}")
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
    code = request.query_params.get('code')
    state = request.query_params.get('state')
    error = request.query_params.get('error')

    if error:
        logger.warning(f"OAuth negado pelo usuário: {error}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail=f"A autorização foi negada pelo usuário: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Parâmetros 'code' ou 'state' ausentes no callback.")

    try:
        agent_id = int(state)
        agent = crud.get_agent_by_id(db, agent_id=agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agente com ID {agent_id} não encontrado.")

        flow = security.create_google_auth_flow()
        
        # --- CORREÇÃO PRINCIPAL ---
        # O redirect_uri AQUI precisa ser IDÊNTICO ao do endpoint anterior
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        
        # Troca o código pelos tokens
        flow.fetch_token(code=code)
        
        # Salva no banco
        crud.update_agent_credentials(db, agent=agent, creds=flow.credentials)
        logger.info(f"OAuth concluído com sucesso para agente: {agent.email}")
        
        html_content = f"""
        <html>
            <head>
                <title>Sucesso</title>
                <style>body {{ font-family: sans-serif; text-align: center; padding: 50px; }}</style>
            </head>
            <body>
                <h1 style="color:green;">Autorização Concluída!</h1>
                <p>O agente <strong>{agent.email}</strong> está conectado.</p>
                <p>Você pode fechar esta janela.</p>
            </body>
        </html>
        """
        return html_content
    
    except ValueError:
        logger.error(f"Erro no state do callback (não é int): {state}")
        raise HTTPException(status_code=400, detail="Parâmetro 'state' inválido.")
    except Exception as e:
        # Esse log é crucial para debug de 'redirect_uri_mismatch'
        logger.error(f"Erro fatal no callback: {str(e)}", exc_info=True)
        
        error_detail = f"Erro ao processar autenticação: {str(e)}"
        if "redirect_uri_mismatch" in str(e):
             error_detail += f" | Esperado: {settings.GOOGLE_REDIRECT_URI}"
             
        raise HTTPException(status_code=400, detail=error_detail)


@router.post("/{agent_id}/emails/send", status_code=status.HTTP_202_ACCEPTED, summary="Enviar um e-mail simples")
def send_simple_email(agent_id: int, email_data: schemas.SendEmailRequest, db: Session = Depends(get_db)):
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
        logger.error(f"Erro envio e-mail (Auth): {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Erro envio e-mail: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ocorreu um erro inesperado: {str(e)}")
