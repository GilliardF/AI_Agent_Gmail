-- Fluxo de Trabalho
-- 1) Criação de e-mails:
INSERT INTO outgoing_emails (account_id, recipient, subject, body, status)
VALUES (1, 'destinatario@exemplo.com', 'Assunto do E-mail', 'Corpo da mensagem.', 'draft');

-- 2) Envio de e-mails que estão agendados:
UPDATE outgoing_emails
SET status = 'queued'
WHERE id = <id_do_email_a_ser_enviado>;

-- 3) Atualização quando o e-mail é enviado:
UPDATE outgoing_emails
SET status = 'sent', sent_at = CURRENT_TIMESTAMP
WHERE id = <id_do_email_enviado>;


-- 3.1) Se houver falha no envio será registrado no sql:
UPDATE outgoing_emails
SET status = 'failed', error_message = 'Motivo da falha SMTP...'
WHERE id = <id_do_email_com_falha>;
