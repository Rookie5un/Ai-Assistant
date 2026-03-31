from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models import Assistant, Conversation, Document, DocumentChunk, KnowledgeBase, Message, User
from app.services.knowledge import chunk_text, extract_keywords


def seed_demo_content(db: Session) -> None:
    legacy_demo = db.execute(select(User).where(User.email == "demo@ai-assistant.local")).scalar_one_or_none()
    current_demo = db.execute(select(User).where(User.email == settings.demo_user_email)).scalar_one_or_none()

    if legacy_demo and not current_demo:
        legacy_demo.email = settings.demo_user_email
        legacy_demo.display_name = "Demo Operator"
        db.commit()
        current_demo = legacy_demo

    if db.execute(select(User.id)).first():
        return

    user = User(
        email=settings.demo_user_email,
        password_hash=hash_password(settings.demo_user_password),
        display_name="Demo Operator",
        role="admin",
    )
    db.add(user)
    db.flush()

    kb1 = KnowledgeBase(
        user_id=user.id,
        name="产品资料库",
        description="首版产品定位、上线清单和用户反馈摘要。",
    )
    kb2 = KnowledgeBase(
        user_id=user.id,
        name="运营脚本库",
        description="面向客服与运营的标准回复与活动脚本。",
    )
    db.add_all([kb1, kb2])
    db.flush()

    assistant1 = Assistant(
        user_id=user.id,
        name="产品策略助手",
        description="适合整理需求、路线图和版本说明。",
        system_prompt="你是一名产品与交付助手，回答需要结构化、清晰、可执行。",
        model=settings.qwen_model,
        temperature=0.6,
        is_default=True,
        metadata_json={"provider": "qwen"},
    )
    assistant2 = Assistant(
        user_id=user.id,
        name="知识库问答助手",
        description="优先使用上传资料回答，并标注引用。",
        system_prompt="你是一名知识库助手，优先基于文档片段生成回答。",
        model=settings.doubao_model,
        temperature=0.3,
        metadata_json={"provider": "doubao"},
    )
    assistant1.knowledge_bases.append(kb1)
    assistant2.knowledge_bases.extend([kb1, kb2])
    db.add_all([assistant1, assistant2])
    db.flush()

    documents = [
        Document(
            knowledge_base_id=kb1.id,
            user_id=user.id,
            title="MVP 上线清单",
            source_type="text",
            status="ready",
            excerpt="核心目标是稳定聊天、文件问答、助手配置和基础运营统计。",
            content=(
                "MVP 上线清单包括四个优先级最高的能力：稳定的聊天体验、文件上传后可检索、"
                "助手角色配置、管理员基础统计。首页需要能快速看到系统状态，聊天页需要支持流式输出。"
            ),
        ),
        Document(
            knowledge_base_id=kb2.id,
            user_id=user.id,
            title="客服场景回复模板",
            source_type="text",
            status="ready",
            excerpt="客服助手回答要先确认问题，再给出步骤，最后补充升级路径。",
            content=(
                "客服回复建议采用三段式结构：先复述问题确认场景，再列出可操作步骤，"
                "最后说明如果仍未解决应如何升级处理。整体语气需要稳定、具体、避免空话。"
            ),
        ),
    ]
    db.add_all(documents)
    db.flush()

    for document in documents:
        for index, chunk in enumerate(chunk_text(document.content or "")):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    knowledge_base_id=document.knowledge_base_id,
                    chunk_index=index,
                    content=chunk,
                    keywords=extract_keywords(chunk),
                )
            )

    conversation = Conversation(
        user_id=user.id,
        assistant_id=assistant1.id,
        title="首版交付讨论",
        summary="围绕 MVP 范围与视觉方向的启动会话。",
    )
    db.add(conversation)
    db.flush()

    db.add_all(
        [
            Message(
                conversation_id=conversation.id,
                role="user",
                content="帮我梳理一下首版 AI 助手系统最应该先做什么。",
                metadata_json={"citations": []},
            ),
            Message(
                conversation_id=conversation.id,
                role="assistant",
                content=(
                    "建议优先做三件事：1. 打通登录、会话和基础聊天。2. 接好知识库文档上传与检索。"
                    "3. 补助手配置和基础后台统计。这样你能最快验证产品价值。"
                ),
                model="gpt-4.1-mini",
                metadata_json={"citations": [{"title": "MVP 上线清单", "snippet": documents[0].excerpt}]},
            ),
        ]
    )
    conversation.last_message_at = conversation.updated_at
    db.commit()
