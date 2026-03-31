from datetime import UTC

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models import Assistant, Conversation, Document, UsageLog, User
from app.schemas import DashboardOverview
from app.schemas.dashboard import ActivityItem, MetricItem


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardOverview:
    conversation_count = db.scalar(
        select(func.count()).select_from(Conversation).where(Conversation.user_id == current_user.id)
    ) or 0
    assistant_count = db.scalar(
        select(func.count()).select_from(Assistant).where(Assistant.user_id == current_user.id)
    ) or 0
    document_count = db.scalar(
        select(func.count()).select_from(Document).where(Document.user_id == current_user.id)
    ) or 0
    token_total = db.scalar(
        select(func.coalesce(func.sum(UsageLog.total_tokens), 0)).where(UsageLog.user_id == current_user.id)
    ) or 0

    recent_conversations = (
        db.execute(
            select(Conversation)
            .where(Conversation.user_id == current_user.id)
            .order_by(Conversation.updated_at.desc())
            .limit(3)
        )
        .scalars()
        .all()
    )

    metrics = [
        MetricItem(label="Open conversations", value=str(conversation_count), detail="按最近更新排序"),
        MetricItem(label="Configured assistants", value=str(assistant_count), detail="助手与场景模板数量"),
        MetricItem(label="Knowledge files", value=str(document_count), detail="已接入到资料库的文档"),
        MetricItem(label="Token footprint", value=f"{token_total:,}", detail="本地演示环境累计 token 估算"),
    ]

    activity = [
        ActivityItem(
            label=conversation.title,
            detail=conversation.summary or "最近一次工作流会话",
            timestamp=conversation.updated_at.astimezone(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        )
        for conversation in recent_conversations
    ]

    return DashboardOverview(
        metrics=metrics,
        active_assistants=[
            "产品策略助手已绑定资料库",
            "知识库问答助手正在等待新文档",
            "客服运营模板可直接继续扩展",
        ],
        pending_documents=[
            "建议补一份产品 FAQ，用于验证知识库问答体验",
            "建议补一份品牌语气规范，用于生成统一文案",
        ],
        activity=activity,
    )

