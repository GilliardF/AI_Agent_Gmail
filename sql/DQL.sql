-- 3) Worker para consultar email's pelo Backend
SELECT * FROM outgoing_emails WHERE status = 'queued' ORDER BY created_at LIMIT 10 FOR UPDATE SKIP LOCKED;
