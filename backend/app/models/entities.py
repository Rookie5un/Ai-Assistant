from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


assistant_knowledge_bases = Table(
    "assistant_knowledge_bases",
    Base.metadata,
    Column("assistant_id", String(36), ForeignKey("assistants.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "knowledge_base_id",
        String(36),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime(timezone=True), default=utcnow, nullable=False),
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20), default="user")
    status: Mapped[str] = mapped_column(String(20), default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    assistants: Mapped[list["Assistant"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    knowledge_bases: Mapped[list["KnowledgeBase"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Assistant(TimestampMixin, Base):
    __tablename__ = "assistants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    system_prompt: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(120), default="gpt-4.1-mini")
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    top_p: Mapped[float] = mapped_column(Float, default=1.0)
    max_tokens: Mapped[int | None] = mapped_column(Integer)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    visibility: Mapped[str] = mapped_column(String(20), default="private")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="assistants")
    knowledge_bases: Mapped[list["KnowledgeBase"]] = relationship(
        secondary=assistant_knowledge_bases,
        back_populates="assistants",
    )
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="assistant")


class KnowledgeBase(TimestampMixin, Base):
    __tablename__ = "knowledge_bases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active")
    embedding_model: Mapped[str] = mapped_column(String(120), default="lexical-demo")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="knowledge_bases")
    assistants: Mapped[list["Assistant"]] = relationship(
        secondary=assistant_knowledge_bases,
        back_populates="knowledge_bases",
    )
    documents: Mapped[list["Document"]] = relationship(back_populates="knowledge_base", cascade="all, delete-orphan")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="knowledge_base", cascade="all, delete-orphan")


class Document(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_base_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(20), default="upload")
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), default="ready")
    excerpt: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)

    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    knowledge_base_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("knowledge_bases.id", ondelete="CASCADE"),
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    keywords: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="chunks")
    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="chunks")


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    assistant_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("assistants.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200), default="新会话")
    summary: Mapped[str | None] = mapped_column(Text)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    user: Mapped["User"] = relationship(back_populates="conversations")
    assistant: Mapped[Assistant | None] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    model: Mapped[str | None] = mapped_column(String(120))
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        index=True,
    )
    request_type: Mapped[str] = mapped_column(String(20), default="chat")
    provider: Mapped[str] = mapped_column(String(50), default="demo-engine")
    model: Mapped[str] = mapped_column(String(120), default="gpt-4.1-mini")
    status: Mapped[str] = mapped_column(String(20), default="success")
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
