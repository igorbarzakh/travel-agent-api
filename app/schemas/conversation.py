from datetime import datetime

from pydantic import BaseModel, Field
from app.core.types import MessageRole


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: MessageRole
    content: str
    created_at: datetime


class MessagePageResponse(BaseModel):
    items: list[MessageResponse]
    next_cursor: int | None
    has_more: bool


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=255,
    )


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str | None
    created_at: datetime
    updated_at: datetime


class MessageCreateRequest(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=2000,
    )
