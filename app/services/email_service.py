import base64
import email
import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from googleapiclient.errors import HttpError
import google.generativeai as genai

from app import crud, schemas, models
from app.config import settings
from app.security import get_gmail_service

# --- Configuração do Cliente Google Gemini ---
if not settings.GOOGLE_API_KEY:
    raise ValueError(
        "A chave da API do Google (GOOGLE_API_KEY) não foi encontrada. "
        "Verifique seu arquivo .env e garanta que a chave para o Gemini está configurada."
    )
genai.configure(api_key=settings.GOOGLE_API_KEY)

def _decode_email_body(parts: list) -> str:
    """Decodifica o corpo do e-mail a partir das partes da mensagem."""
    body = ""
    if not parts:
        return body

    for part in parts:
        mime_type = part.get("mimeType", "")
        if mime_type == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                body += base64.urlsafe_b64decode(data).decode("utf-8")
        elif mime_type == "multipart/alternative":
            # Recursivamente chama para as partes aninhadas
            return _decode_email_body(part.get("parts", []))
    return body

async def _summarize_text_with_ai(text: str) -> str:
    """Gera um resumo conciso de um texto usando a API do Google Gemini."""
    if not text:
        return ""
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = (
            "Você é um assistente eficiente que resume e-mails. "
            "Resuma o seguinte conteúdo de e-mail em português, focando nos pontos principais, "
            "ações necessárias e no sentimento geral. O resumo deve ter no máximo 3 sentenças.\n\n"
            f"E-mail: {text}"
        )
        response = await model.generate_content_async(prompt)
        summary = response.text.strip()
        return summary
    except Exception as e:
        print(f"Erro ao chamar a API do Gemini: {e}")
        return f"Não foi possível gerar o resumo. Erro: {e}"

async def _forward_summary(summary: schemas.EmailSummaryCreate, db_summary: models.EmailSummary, db: Session):
    """Envia o resumo para a URL de destino e atualiza o status no banco."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                summary.forward_url,
                json=summary.model_dump(mode="json"),
                timeout=30.0
            )
            response.raise_for_status()
            
            # Atualiza o status para sucesso
            crud.update_summary_status(
                db, summary_id=db_summary.id, status=models.ForwardStatusEnum.success,
                status_message=f"Encaminhado com sucesso. Status: {response.status_code}"
            )
        except httpx.HTTPStatusError as e:
            # Atualiza o status para falha
            crud.update_summary_status(
                db, summary_id=db_summary.id, status=models.ForwardStatusEnum.failed,
                status_message=f"Falha no encaminhamento: {e.response.status_code} - {e.response.text}"
            )
        except Exception as e:
            # Atualiza o status para falha em caso de outros erros
            crud.update_summary_status(
                db, summary_id=db_summary.id, status=models.ForwardStatusEnum.failed,
                status_message=f"Ocorreu um erro inesperado: {e}"
            )

async def process_and_summarize_emails(db: Session, account_id: int):
    """
    Processo principal para ler e-mails não lidos, resumi-los e encaminhar.
    """
    service = get_gmail_service()
    if not service:
        raise ConnectionError("Não foi possível conectar ao serviço do Gmail.")

    try:
        results = service.users().messages().list(userId='me', q='is:unread').execute()
        messages = results.get('messages', [])

        if not messages:
            print("Nenhum e-mail não lido encontrado.")
            return []

        created_summaries = []
        for message_info in messages:
            msg = service.users().messages().get(userId='me', id=message_info['id'], format='full').execute()
            
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sem Assunto')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Desconhecido')
            
            body = _decode_email_body(payload.get('parts', []))
            if not body and payload.get('body', {}).get('data'): # Para e-mails simples sem 'parts'
                 body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

            # 1. Salva o e-mail no banco de dados
            email_data = schemas.ReceivedEmailCreate(
                gmail_message_id=msg['id'],
                account_id=account_id,
                sender=sender,
                subject=subject,
                body=body,
                received_at=datetime.fromtimestamp(int(msg['internalDate']) / 1000)
            )
            db_email = crud.get_or_create_received_email(db, email_data)

            # 2. Gera o resumo
            summary_text = await _summarize_text_with_ai(f"De: {sender}\nAssunto: {subject}\n\n{body}")

            # 3. Salva o resumo no banco de dados
            summary_data = schemas.EmailSummaryCreate(
                received_email_id=db_email.id,
                summary_text=summary_text,
                # Garante que a URL não seja nula se o encaminhamento for ocorrer
                forward_url=settings.FORWARD_POST_URL if settings.FORWARD_POST_URL else "N/A"
            )
            db_summary = crud.create_email_summary(db, summary_data)
            created_summaries.append(db_summary)

            # 4. Encaminha o resumo apenas se a URL estiver configurada
            if settings.FORWARD_POST_URL:
                # Atualiza o objeto para garantir que a URL correta seja usada
                summary_data.forward_url = settings.FORWARD_POST_URL
                await _forward_summary(summary_data, db_summary, db)
            else:
                print("FORWARD_POST_URL não configurada. Pulando etapa de encaminhamento.")
                # Opcional: Atualizar o status para indicar que foi pulado
                crud.update_summary_status(db, db_summary.id, models.ForwardStatusEnum.pending, "Encaminhamento não configurado.")

            # 5. Marca o e-mail como lido no Gmail
            service.users().messages().modify(
                userId='me', id=msg['id'], body={'removeLabelIds': ['UNREAD']}
            ).execute()
            print(f"E-mail {msg['id']} processado e marcado como lido.")

        return created_summaries

    except HttpError as error:
        print(f"Ocorreu um erro na API do Gmail: {error}")
        return []
    except Exception as e:
        print(f"Ocorreu um erro inesperado no processamento de e-mails: {e}")
        return []
