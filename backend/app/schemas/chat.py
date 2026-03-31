from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str = Field(default="新会话", min_length=1, max_length=200)
    assistant_id: str | None = None


class ConversationRead(BaseModel):
    id: str
    title: str
    summary: str | None = None
    assistant_id: str | None = None
    pinned: bool
    archived: bool
    last_message_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str = Field(min_length=1)
    assistant_id: str | None = None
    knowledge_base_ids: list[str] = []


class MessageRead(BaseModel):
    id: str
    role: str
    content: str
    status: str
    model: str | None = None
    created_at: datetime
    metadata_json: dict = {}

    model_config = {"from_attributes": True}
