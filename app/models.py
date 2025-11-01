import enum
from sqlalchemy import (Column, Integer, String, Text, Boolean, DateTime,
                        LargeBinary, ForeignKey, Enum)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class EmailStatusEnum(enum.Enum):
    draft = 'draft'
    queued = 'queued'
    sent = 'sent'
    failed = 'failed'


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    encrypted_credentials = Column(LargeBinary, nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    forward_url = Column(String(2048), nullable=True) # URL para encaminhar resumos

    received_emails = relationship("ReceivedEmail", back_populates="account", cascade="all, delete-orphan")
    outgoing_emails = relationship("OutgoingEmail", back_populates="account", cascade="all, delete-orphan")


class ReceivedEmail(Base):
    __tablename__ = "received_emails"
    id = Column(Integer, primary_key=True, index=True)
    gmail_message_id = Column(String(255), unique=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    sender = Column(String(255), nullable=False)
    subject = Column(Text)
    body = Column(Text)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, server_default='False')
    account = relationship("Account", back_populates="received_emails")
    summaries = relationship("EmailSummary", back_populates="received_email", cascade="all, delete-orphan")


class OutgoingEmail(Base):
    __tablename__ = "outgoing_emails"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    recipient = Column(String(255), nullable=False)
    subject = Column(Text)
    body = Column(Text)
    status = Column(Enum(EmailStatusEnum), nullable=False, default=EmailStatusEnum.draft)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    account = relationship("Account", back_populates="outgoing_emails")


class ForwardStatusEnum(enum.Enum):
    pending = 'pending'
    success = 'success'
    failed = 'failed'


class EmailSummary(Base):
    __tablename__ = "email_summaries"

    id = Column(Integer, primary_key=True, index=True)
    received_email_id = Column(Integer, ForeignKey("received_emails.id"), nullable=False, index=True)
    summary_text = Column(Text, nullable=False)
    forward_url = Column(String(2048), nullable=False)
    forward_status = Column(Enum(ForwardStatusEnum), nullable=False, default=ForwardStatusEnum.pending)
    status_message = Column(Text, nullable=True) # To store potential error messages
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    received_email = relationship("ReceivedEmail", back_populates="summaries")