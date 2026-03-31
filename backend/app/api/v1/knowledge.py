from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.v1.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models import Document, DocumentChunk, KnowledgeBase, User
from app.schemas import KnowledgeBaseCreate, KnowledgeBaseRead
from app.services.knowledge import chunk_text, extract_keywords, extract_text_from_upload


router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


def _serialize_knowledge_base(knowledge_base: KnowledgeBase) -> KnowledgeBaseRead:
    return KnowledgeBaseRead(
        id=knowledge_base.id,
        name=knowledge_base.name,
        description=knowledge_base.description,
        status=knowledge_base.status,
        embedding_model=knowledge_base.embedding_model,
        created_at=knowledge_base.created_at,
        updated_at=knowledge_base.updated_at,
        documents=knowledge_base.documents,
    )


@router.get("", response_model=list[KnowledgeBaseRead])
def list_knowledge_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[KnowledgeBaseRead]:
    knowledge_bases = (
        db.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.user_id == current_user.id)
            .options(selectinload(KnowledgeBase.documents))
            .order_by(KnowledgeBase.updated_at.desc())
        )
        .scalars()
        .all()
    )
    return [_serialize_knowledge_base(item) for item in knowledge_bases]


@router.post("", response_model=KnowledgeBaseRead, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    payload: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeBaseRead:
    knowledge_base = KnowledgeBase(
        user_id=current_user.id,
        name=payload.name.strip(),
        description=payload.description,
    )
    db.add(knowledge_base)
    db.commit()
    db.refresh(knowledge_base)
    return _serialize_knowledge_base(knowledge_base)


@router.post("/{knowledge_base_id}/documents", response_model=KnowledgeBaseRead)
def upload_document(
    knowledge_base_id: str,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> KnowledgeBaseRead:
    knowledge_base = (
        db.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.id == knowledge_base_id, KnowledgeBase.user_id == current_user.id)
            .options(selectinload(KnowledgeBase.documents))
        )
        .scalar_one_or_none()
    )
    if not knowledge_base:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found.")

    storage_dir = Path(settings.upload_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    sanitized_name = Path(file.filename or "document").name
    destination = storage_dir / f"{knowledge_base.id}-{sanitized_name}"
    content = extract_text_from_upload(file)

    file.file.seek(0)
    destination.write_bytes(file.file.read())

    document = Document(
        knowledge_base_id=knowledge_base.id,
        user_id=current_user.id,
        title=(title or Path(sanitized_name).stem).strip(),
        source_type="upload",
        file_name=sanitized_name,
        file_path=str(destination),
        mime_type=file.content_type,
        status="ready",
        excerpt=content[:220],
        content=content,
    )
    db.add(document)
    db.flush()

    for index, chunk in enumerate(chunk_text(content)):
        db.add(
            DocumentChunk(
                document_id=document.id,
                knowledge_base_id=knowledge_base.id,
                chunk_index=index,
                content=chunk,
                keywords=extract_keywords(chunk),
            )
        )

    db.commit()
    refreshed = (
        db.execute(
            select(KnowledgeBase)
            .where(KnowledgeBase.id == knowledge_base.id)
            .options(selectinload(KnowledgeBase.documents))
        )
        .scalar_one()
    )
    return _serialize_knowledge_base(refreshed)

