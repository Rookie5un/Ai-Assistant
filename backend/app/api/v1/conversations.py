from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.models import Assistant, Conversation, Message, User
from app.schemas import ConversationCreate, ConversationRead, MessageCreate, MessageRead
from app.services.chat import build_chat_context, build_instructions, record_usage
from app.services.llm import CompatibleResponsesService, LLMProviderError, LLMUsage


router = APIRouter(prefix="/conversations", tags=["conversations"])
llm_service = CompatibleResponsesService()


@router.get("", response_model=list[ConversationRead])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ConversationRead]:
    conversations = (
        db.execute(
            select(Conversation)
            .where(Conversation.user_id == current_user.id)
            .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.updated_at.desc())
        )
        .scalars()
        .all()
    )
    return [ConversationRead.model_validate(conversation) for conversation in conversations]


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationRead:
    conversation = Conversation(
        user_id=current_user.id,
        assistant_id=payload.assistant_id,
        title=payload.title.strip(),
        summary="等待第一条消息",
        last_message_at=datetime.now(UTC),
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return ConversationRead.model_validate(conversation)


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
def list_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MessageRead]:
    conversation = db.execute(
        select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
    ).scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    messages = (
        db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        .scalars()
        .all()
    )
    return [MessageRead.model_validate(message) for message in messages]


@router.post("/{conversation_id}/stream")
def stream_message(
    conversation_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    conversation = (
        db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
            .options(joinedload(Conversation.assistant).selectinload(Assistant.knowledge_bases))
        )
        .scalar_one_or_none()
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    if payload.assistant_id:
        selected_assistant = db.execute(
            select(Assistant).where(Assistant.id == payload.assistant_id, Assistant.user_id == current_user.id)
        ).scalar_one_or_none()
        if not selected_assistant:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assistant selection is invalid.")
        conversation.assistant_id = selected_assistant.id

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=payload.content.strip(),
        status="completed",
    )
    conversation.summary = payload.content[:120]
    conversation.last_message_at = datetime.now(UTC)
    db.add(user_message)
    db.commit()

    refreshed_conversation = (
        db.execute(
            select(Conversation)
            .where(Conversation.id == conversation.id)
            .options(joinedload(Conversation.assistant).selectinload(Assistant.knowledge_bases))
        )
        .scalar_one()
    )
    chat_context = build_chat_context(db, refreshed_conversation, payload.content, payload.knowledge_base_ids)
    assistant = refreshed_conversation.assistant
    provider_name = assistant.metadata_json.get("provider", settings.llm_provider) if assistant else settings.llm_provider
    llm_service.ensure_configured(provider_name)
    provider_config = llm_service.get_provider_config(provider_name)
    model_name = assistant.model if assistant else provider_config.default_model
    instructions = build_instructions(assistant, chat_context.knowledge_matches)

    def event_stream():
        response_parts: list[str] = []
        usage = LLMUsage()
        status_value = "completed"

        yield f"data: {json.dumps({'type': 'meta', 'citations': chat_context.citations}, ensure_ascii=False)}\n\n"

        try:
            for event in llm_service.stream_response(
                provider=provider_name,
                model=model_name,
                instructions=instructions,
                history=chat_context.history,
                temperature=assistant.temperature if assistant else 0.7,
                top_p=assistant.top_p if assistant else 1.0,
                max_output_tokens=assistant.max_tokens if assistant else None,
                metadata={
                    "conversation_id": conversation.id,
                    "user_id": current_user.id,
                },
            ):
                if event.type == "delta":
                    response_parts.append(event.delta)
                    yield f"data: {json.dumps({'type': 'delta', 'delta': event.delta}, ensure_ascii=False)}\n\n"

                if event.type == "completed" and event.usage:
                    usage = event.usage
        except LLMProviderError as exc:
            status_value = "failed"
            error_text = f"\n\n模型调用失败：{exc}"
            response_parts.append(error_text)
            yield f"data: {json.dumps({'type': 'delta', 'delta': error_text}, ensure_ascii=False)}\n\n"

        response_text = "".join(response_parts).strip() or "模型未返回可用内容。"

        with SessionLocal() as stream_db:
            persisted_conversation = stream_db.execute(
                select(Conversation)
                .where(Conversation.id == conversation.id, Conversation.user_id == current_user.id)
                .options(joinedload(Conversation.assistant))
            ).scalar_one()
            assistant_message = Message(
                conversation_id=persisted_conversation.id,
                role="assistant",
                content=response_text,
                status=status_value,
                model=persisted_conversation.assistant.model if persisted_conversation.assistant else model_name,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                metadata_json={
                    "citations": chat_context.citations,
                    "provider_response_id": usage.provider_response_id,
                },
            )
            persisted_conversation.summary = payload.content[:120]
            persisted_conversation.last_message_at = datetime.now(UTC)
            stream_db.add(assistant_message)
            record_usage(
                stream_db,
                user_id=current_user.id,
                conversation_id=persisted_conversation.id,
                model=assistant_message.model or model_name,
                provider=provider_name,
                total_tokens=usage.total_tokens,
                latency_ms=usage.latency_ms,
                status="success" if status_value == "completed" else "failed",
            )
            stream_db.commit()

        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
