from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeBaseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None


class DocumentRead(BaseModel):
    id: str
    title: str
    source_type: str
    file_name: str | None = None
    status: str
    excerpt: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeBaseRead(BaseModel):
    id: str
    name: str
    description: str | None = None
    status: str
    embedding_model: str
    created_at: datetime
    updated_at: datetime
    documents: list[DocumentRead] = []

    model_config = {"from_attributes": True}

