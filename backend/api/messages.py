import html
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from crud.schemas import (
    BatchResult,
    ChannelDTO,
    MessageDTO,
    MessageListResponse,
    MessageStats,
    ReadUpdatePayload,
    SyncResult,
)
from dao.messages import (
    batch_update_read_status,
    get_last_message_id,
    mark_all_read,
    query_messages,
)
from model.db import get_db
from service.telegram import (
    fetch_channel_data,
    import_messages_to_db,
    normalize_channel_id,
    refresh_account_channels,
)

router = APIRouter()


def _html_to_text(content: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", content, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text).strip()


@router.get("/messages", response_model=MessageListResponse, summary="分页查询消息")
async def list_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    channel_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    is_read: Optional[bool] = Query(None),
    start_date: Optional[str] = Query(None, description="ISO 8601"),
    end_date: Optional[str] = Query(None, description="ISO 8601"),
    plain_text: bool = Query(False, description="是否返回去除 HTML 标签后的纯文本 content"),
    db: AsyncSession = Depends(get_db),
):
    total, rows = await query_messages(
        db,
        channel_id=channel_id,
        keyword=keyword,
        is_read=is_read,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )

    items = []
    for message, status in rows:
        content = message.content or ""
        if plain_text:
            content = _html_to_text(content)
        items.append(
            MessageDTO(
                channel_id=message.channel_id,
                message_id=message.message_id,
                grouped_id=message.grouped_id,
                is_read=status.is_read if status else False,
                sent_at=message.sent_at,
                content=content,
                media_type=message.media_type,
                images=message.images or [],
                stats=MessageStats(
                    views=message.views,
                    forwards=message.forwards,
                    replies=message.replies,
                ),
                link=message.message_link,
            )
        )
    return MessageListResponse(total=total, page=page, page_size=page_size, items=items)


@router.patch("/messages/read", response_model=BatchResult, summary="批量更新已读状态")
async def patch_read_status(
    payload: ReadUpdatePayload,
    db: AsyncSession = Depends(get_db),
):
    message_keys = [(item.channel_id, item.message_id) for item in payload.message_keys]
    affected = await batch_update_read_status(db, message_keys, payload.is_read)
    return BatchResult(affected=affected)


@router.post("/messages/mark-all-read", response_model=BatchResult, summary="全部标记为已读")
async def patch_mark_all_read(
    channel_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    affected = await mark_all_read(db, channel_id)
    return BatchResult(affected=affected)


@router.get("/channels", response_model=list[ChannelDTO], summary="获取当前账号的广播频道列表")
async def get_channels(db: AsyncSession = Depends(get_db)):
    try:
        channels = await refresh_account_channels(db)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"频道加载失败: {error}") from error
    return [
        ChannelDTO(id=channel["id"], name=channel["name"], username=channel["username"])
        for channel in channels
    ]


@router.post("/channel/sync-telegram", response_model=SyncResult, summary="同步指定频道消息")
async def sync_telegram(
    channel_id: Optional[int] = Query(None, description="要同步的 Telegram 频道 ID"),
    sync_all: bool = Query(False, description="是否同步频道全部历史消息"),
    limit: int = Query(200, ge=1, le=2000, description="仅在 sync_all=false 时生效"),
    db: AsyncSession = Depends(get_db),
):
    if channel_id is None:
        raise HTTPException(status_code=400, detail="请先选择频道")

    try:
        channel_id = normalize_channel_id(channel_id)
        effective_limit = None if sync_all else limit
        min_message_id = 0
        if not sync_all:
            min_message_id = await get_last_message_id(db, channel_id)

        payload = await fetch_channel_data(
            channel_id=channel_id,
            limit=effective_limit,
            persist_output=False,
            min_id=min_message_id,
        )
        messages = payload.get("messages", [])
        inserted, updated, last_message_id = await import_messages_to_db(
            db,
            messages,
            channel=payload.get("channel"),
        )
        return SyncResult(
            fetched=len(messages),
            inserted=inserted,
            updated=updated,
            last_message_id=last_message_id or min_message_id,
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"同步失败: {error}") from error
