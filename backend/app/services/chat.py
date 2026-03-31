from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import Assistant, Conversation, DocumentChunk, Message, UsageLog
from app.services.knowledge import format_citations, score_chunk


@dataclass
class KnowledgeMatch:
    title: str
    content: str
    score: int


@dataclass
class ChatContext:
    citations: list[dict[str, str]]
    knowledge_matches: list[KnowledgeMatch]
    history: list[dict[str, str]]


def collect_knowledge_matches(db: Session, query: str, knowledge_base_ids: list[str]) -> list[KnowledgeMatch]:
    if not knowledge_base_ids:
        return []

    stmt: Select[tuple[DocumentChunk]] = (
        select(DocumentChunk)
        .where(DocumentChunk.knowledge_base_id.in_(knowledge_base_ids))
        .order_by(DocumentChunk.created_at.desc())
    )
    chunks = db.execute(stmt).scalars().all()
    matches: list[KnowledgeMatch] = []
    for chunk in chunks:
        score = score_chunk(query, chunk.content, chunk.keywords)
        if score <= 0:
            continue
        matches.append(
            KnowledgeMatch(
                score=score,
                content=chunk.content,
                title=chunk.document.title if chunk.document else "Untitled document",
            )
        )

    matches.sort(key=lambda item: item.score, reverse=True)
    return matches[:3]


def build_chat_context(
    db: Session,
    conversation: Conversation,
    user_prompt: str,
    selected_knowledge_base_ids: list[str],
) -> ChatContext:
    assistant = conversation.assistant
    if selected_knowledge_base_ids:
        knowledge_base_ids = selected_knowledge_base_ids
    elif assistant:
        knowledge_base_ids = [kb.id for kb in assistant.knowledge_bases]
    else:
        knowledge_base_ids = []
    knowledge_matches = collect_knowledge_matches(db, user_prompt, knowledge_base_ids)

    history_rows = (
        db.execute(
            select(Message)
            .where(Message.conversation_id == conversation.id)
            .order_by(Message.created_at.asc())
            .limit(12)
        )
        .scalars()
        .all()
    )

    history: list[dict[str, str]] = []
    for message in history_rows:
        if message.role not in {"user", "assistant"}:
            continue
        history.append({"role": message.role, "content": message.content})

    return ChatContext(
        citations=format_citations([match.__dict__ for match in knowledge_matches]),
        knowledge_matches=knowledge_matches,
        history=history,
    )


def build_instructions(assistant: Assistant | None, knowledge_matches: list[KnowledgeMatch]) -> str:
    base_prompt = assistant.system_prompt if assistant else "你是一名通用工作助手，回答需要结构化、清晰、可执行。"
    lines = [
        base_prompt.strip(),
        "",
        "补充要求：",
        "1. 默认使用中文回答，除非用户明确要求其他语言。",
        "2. 回答优先保持准确和可执行，避免空泛描述。",
        "3. 如果提供了知识库片段，优先基于这些片段作答；信息不足时要明确说明。",
    ]

    if knowledge_matches:
        lines.extend(["", "知识库上下文："])
        for index, match in enumerate(knowledge_matches, start=1):
            lines.append(f"[资料{index}] 标题：{match.title}")
            lines.append(match.content)
            lines.append("")

    return "\n".join(lines).strip()


def record_usage(
    db: Session,
    *,
    user_id: str,
    conversation_id: str,
    model: str,
    provider: str,
    total_tokens: int,
    latency_ms: int,
    status: str = "success",
    estimated_cost: float = 0,
) -> None:
    db.add(
        UsageLog(
            user_id=user_id,
            conversation_id=conversation_id,
            request_type="chat",
            provider=provider,
            model=model,
            status=status,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            estimated_cost=estimated_cost,
        )
    )
