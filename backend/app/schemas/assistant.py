from datetime import datetime

from pydantic import BaseModel, Field


class AssistantBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    system_prompt: str = Field(min_length=10)
    provider: str = "openai"
    model: str = "gpt-4.1-mini"
    temperature: float = Field(default=0.7, ge=0, le=2)
    top_p: float = Field(default=1.0, gt=0, le=1)
    max_tokens: int | None = Field(default=800, gt=0)
    knowledge_base_ids: list[str] = []


class AssistantCreate(AssistantBase):
    is_default: bool = False


class AssistantRead(AssistantBase):
    id: str
    is_default: bool
    visibility: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
