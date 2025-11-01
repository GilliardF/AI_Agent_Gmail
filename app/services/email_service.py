import base64
from datetime import datetime
from email.mime.text import MIMEText # NOVO: Import necessário para criar a resposta do e-mail

import httpx
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.config import settings
from app.security import get_agent_gmail_service

# --- Validação da Chave de API do Google (mantida) ---
if not settings.GOOGLE_API_KEY:
    raise ValueError(
        "A chave da API do Google (GOOGLE_API_KEY) não foi encontrada. "
        "Verifique seu arquivo .env e garanta que a chave para o Gemini está configurada."
    )

# --- _decode_email_body (mantida sem alterações) ---
def _decode_email_body(parts: list) -> str:
    """Decodifica o corpo do e-mail a partir das partes da mensagem."""
    # ... (seu código original aqui, sem alterações)
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
            return _decode_email_body(part.get("parts", []))
    return body


# --- ALTERADO: Função de IA para GERAR RESPOSTA em vez de resumir ---
async def _generate_reply_with_ai(original_body: str, sender: str, subject: str) -> str:
    """
    Gera uma resposta de e-mail usando a API REST do Google Gemini.
    """
    if not original_body:
        return ""

    api_url = f"https://generativelanguage.googleapis.com/v1/models/{settings.GEMINI_MODEL_NAME}:generateContent?key={settings.GOOGLE_API_KEY}"
    headers = {"Content-Type": "application/json"}

    async with httpx.AsyncClient() as client:
        # NOVO PROMPT: Instrução para gerar uma resposta, não um resumo.
        prompt = (
            "Você é um assistente de IA profissional e sua tarefa é responder e-mails. "
            "Baseado no e-mail original abaixo, gere uma resposta educada, concisa e relevante. "
            "Responda apenas com o corpo do texto da resposta, sem cabeçalhos como 'Assunto:' ou 'Para:'.\n\n"
            f"--- E-mail Original ---\n"
            f"De: {sender}\n"
            f"Assunto: {subject}\n"
            f"Corpo: {original_body}\n"
            f"--- Fim do E-mail Original ---\n\n"
            f"Resposta Sugerida:"
        )
        data = {"contents": [{"parts": [{"text": prompt}]}]}

        try:
            response = await client.post(api_url, json=data, headers=headers, timeout=60.0)
            response.raise_for_status()
            result = response.json()

            if not result.get("candidates") or not result["candidates"][0].get("content", {}).get("parts"):
                finish_reason = result.get("candidates", [{}])[0].get("finishReason", "UNKNOWN")
                error_message = f"A API do Gemini não retornou conteúdo. Motivo: {finish_reason}"
                print(error_message)
                return "" # Retorna vazio em caso de erro para não enviar e-mail em branco

            reply_text = result["candidates"][0]["content"]["parts"][0]["text"]
            return reply_text.strip()
        except (httpx.HTTPStatusError, KeyError, IndexError) as e:
            print(f"Erro ao chamar a API do Gemini: {e}")
            return ""


# --- NOVO: Função para ENVIAR A RESPOSTA via API do Gmail ---
def _send_reply_email(service, to: str, subject: str, message_text: str, thread_id: str):
    """
    Envia a resposta do e-mail usando a API do Gmail, mantendo na mesma thread.
    """
    try:
        message = MIMEText(message_text)
        message['to'] = to
        message['from'] = 'me'
        message['subject'] = subject

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        body = {'raw': raw_message, 'threadId': thread_id}

        service.users().messages().send(userId='me', body=body).execute()
        print(f"Resposta enviada com sucesso para {to} na thread {thread_id}.")
    except HttpError as error:
        print(f"Ocorreu um erro ao enviar o e-mail: {error}")


# --- ALTERADO: Função principal para orquestrar o processo de RESPOSTA ---
async def process_and_reply_to_emails(db: Session, agent: models.Account):
    """
    Processo principal para ler e-mails não lidos, gerar uma resposta com IA e enviá-la.
    """
    service = get_agent_gmail_service(agent=agent, db=db)
    if not service:
        raise ConnectionError("Não foi possível conectar ao serviço do Gmail.")

    try:
        results = service.users().messages().list(userId='me', q='is:unread').execute()
        messages = results.get('messages', [])

        if not messages:
            print("Nenhum e-mail não lido encontrado.")
            return

        for message_info in messages:
            msg = service.users().messages().get(userId='me', id=message_info['id'], format='full').execute()
            
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])
            thread_id = msg['threadId'] # Essencial para manter a conversa
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sem Assunto')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Desconhecido')
            
            body = _decode_email_body(payload.get('parts', []))
            if not body and payload.get('body', {}).get('data'):
                 body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

            # --- Lógica de salvar e-mail recebido (mantida) ---
            email_data = schemas.ReceivedEmailCreate(
                gmail_message_id=msg['id'], account_id=agent.id, sender=sender,
                subject=subject, body=body, received_at=datetime.fromtimestamp(int(msg['internalDate']) / 1000)
            )
            crud.get_or_create_received_email(db, email_data)

            # 1. Gera a resposta com a IA
            ai_reply = await _generate_reply_with_ai(original_body=body, sender=sender, subject=subject)

            # 2. Envia a resposta se a IA gerou algum conteúdo
            if ai_reply:
                reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"
                _send_reply_email(
                    service,
                    to=sender,
                    subject=reply_subject,
                    message_text=ai_reply,
                    thread_id=thread_id
                )
            else:
                print(f"Nenhuma resposta foi gerada pela IA para o e-mail de {sender}. O e-mail não será respondido.")

            # 3. Marca o e-mail como lido no Gmail (mantido)
            service.users().messages().modify(
                userId='me', id=msg['id'], body={'removeLabelIds': ['UNREAD']}
            ).execute()
            print(f"E-mail {msg['id']} processado e marcado como lido.")

    except HttpError as error:
        print(f"Ocorreu um erro na API do Gmail: {error}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado no processamento de e-mails: {e}")
        
def send_new_email(service, to: str, subject: str, body_text: str):
    """
    Cria e envia um novo e-mail (não é uma resposta).
    """
    try:
        message = MIMEText(body_text)
        message['to'] = to
        message['from'] = 'me'
        message['subject'] = subject

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        body = {'raw': raw_message}

        sent_message = service.users().messages().send(userId='me', body=body).execute()
        print(f"Novo e-mail enviado com sucesso para {to}. Message ID: {sent_message['id']}")
        return sent_message
    except HttpError as error:
        print(f"Ocorreu um erro ao enviar o novo e-mail: {error}")
        # Lança a exceção para que o endpoint possa tratá-la
        raise ConnectionError(f"Falha ao enviar e-mail: {error}")
    
def send_new_email(service, to: str, subject: str, body_text: str):
    """
    Cria e envia um novo e-mail (não é uma resposta).
    """
    try:
        message = MIMEText(body_text)
        message['to'] = to
        message['from'] = 'me'  # 'me' se refere à conta autenticada do agente
        message['subject'] = subject

        # Codifica a mensagem no formato esperado pela API do Gmail
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        body = {'raw': raw_message}

        # Executa o envio
        sent_message = service.users().messages().send(userId='me', body=body).execute()
        print(f"Novo e-mail enviado com sucesso para {to}. Message ID: {sent_message['id']}")
        return sent_message
    except HttpError as error:
        print(f"Ocorreu um erro ao enviar o novo e-mail: {error}")
        # Lança a exceção para que o endpoint no router possa tratá-la adequadamente
        raise ConnectionError(f"Falha ao enviar e-mail: {error}")