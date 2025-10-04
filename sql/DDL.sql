-- Tabela de Contas do Gmail
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Senha encriptada pelo Backend
    encrypted_credentials BYTEA,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP -- Carimbo Data/Hora de Criação
);
-- Tabela de Mensagens Recebidas
CREATE TABLE received_emails (
    id SERIAL PRIMARY KEY,
    gmail_message_id VARCHAR(255) UNIQUE, -- ID único do provedor
    account_id INTEGER NOT NULL,
    sender VARCHAR(255) NOT NULL, -- Endereço de e-mail do remetente
    subject TEXT, -- Assunto do e-mail
    body TEXT, -- Conteúdo do e-mail
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Carimbo Data/Hora de Recebimento
    is_read BOOLEAN DEFAULT FALSE, -- Indica se o e-mail foi lido ou não
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

-- Conversão de Status de Email de STRING para ENUM
CREATE TYPE email_status AS ENUM ('draft', 'queued', 'sent', 'failed');

-- Tabela de Mensagens Enviadas
CREATE TABLE outgoing_emails (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL,
    recipient VARCHAR(255) NOT NULL, -- Endereço de e-mail do destinatário
    subject TEXT, -- Assunto do e-mail
    body TEXT, -- Conteúdo do e-mail
    status email_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT, -- Mensagem de erro, se houver
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

-- Cria um índice na coluna account_id da tabela received_emails
CREATE INDEX idx_received_emails_account_id ON received_emails(account_id);

-- Cria um índice na coluna account_id da tabela outgoing_emails
CREATE INDEX idx_outgoing_emails_account_id ON outgoing_emails(account_id);
