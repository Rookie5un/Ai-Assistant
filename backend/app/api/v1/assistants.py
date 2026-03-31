from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models import Assistant, KnowledgeBase, User
from app.schemas import AssistantCreate, AssistantRead


router = APIRouter(prefix="/assistants", tags=["assistants"])
SUPPORTED_PROVIDERS = {"openai", "qwen", "doubao"}


@router.get("", response_model=list[AssistantRead])
def list_assistants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AssistantRead]:
    assistants = (
        db.execute(
            select(Assistant)
            .where(Assistant.user_id == current_user.id)
            .options(selectinload(Assistant.knowledge_bases))
            .order_by(Assistant.is_default.desc(), Assistant.updated_at.desc())
        )
        .scalars()
        .all()
    )
    payload = []
    for assistant in assistants:
        provider = assistant.metadata_json.get("provider", settings.llm_provider)
        payload.append(
            AssistantRead(
                id=assistant.id,
                name=assistant.name,
                description=assistant.description,
                system_prompt=assistant.system_prompt,
                provider=provider,
                model=assistant.model,
                temperature=assistant.temperature,
                top_p=assistant.top_p,
                max_tokens=assistant.max_tokens,
                is_default=assistant.is_default,
                visibility=assistant.visibility,
                knowledge_base_ids=[kb.id for kb in assistant.knowledge_bases],
                created_at=assistant.created_at,
                updated_at=assistant.updated_at,
            )
        )
    return payload


@router.post("", response_model=AssistantRead, status_code=status.HTTP_201_CREATED)
def create_assistant(
    payload: AssistantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssistantRead:
    knowledge_bases = []
    if payload.knowledge_base_ids:
        knowledge_bases = (
            db.execute(
                select(KnowledgeBase).where(
                    KnowledgeBase.user_id == current_user.id,
                    KnowledgeBase.id.in_(payload.knowledge_base_ids),
                )
            )
            .scalars()
            .all()
        )
        if len(knowledge_bases) != len(payload.knowledge_base_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid knowledge base selection.")

    provider = payload.provider.strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported assistant provider.")

    assistant = Assistant(
        user_id=current_user.id,
        name=payload.name.strip(),
        description=payload.description,
        system_prompt=payload.system_prompt.strip(),
        model=payload.model,
        temperature=payload.temperature,
        top_p=payload.top_p,
        max_tokens=payload.max_tokens,
        is_default=payload.is_default,
        metadata_json={"provider": provider},
    )
    assistant.knowledge_bases = knowledge_bases
    db.add(assistant)
    db.commit()
    db.refresh(assistant)
    return AssistantRead(
        id=assistant.id,
        name=assistant.name,
        description=assistant.description,
        system_prompt=assistant.system_prompt,
        provider=provider,
        model=assistant.model,
        temperature=assistant.temperature,
        top_p=assistant.top_p,
        max_tokens=assistant.max_tokens,
        is_default=assistant.is_default,
        visibility=assistant.visibility,
        knowledge_base_ids=[kb.id for kb in knowledge_bases],
        created_at=assistant.created_at,
        updated_at=assistant.updated_at,
    )
