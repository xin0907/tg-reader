from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MessageStats(BaseModel):
    views: int = 0
    forwards: int = 0
    replies: int = 0


class MessageDTO(BaseModel):
    channel_id: int
    message_id: int
    grouped_id: Optional[str] = None
    is_read: bool
    sent_at: datetime
    content: str
    media_type: Optional[str] = None
    images: list[str] = Field(default_factory=list)
    stats: MessageStats
    link: Optional[str] = None


class MessageListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[MessageDTO]


class MessageKey(BaseModel):
    channel_id: int
    message_id: int


class ReadUpdatePayload(BaseModel):
    message_keys: list[MessageKey] = Field(..., min_length=1)
    is_read: bool = True


class BatchResult(BaseModel):
    affected: int


class ChannelDTO(BaseModel):
    id: int
    name: str
    username: Optional[str] = None


class SyncResult(BaseModel):
    fetched: int
    inserted: int
    updated: int
    last_message_id: int
