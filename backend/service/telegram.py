import asyncio
import html
import json
import time
from pathlib import Path
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from telethon import TelegramClient, errors
from telethon.extensions import html as telethon_html

from config.settings import get_settings
from model.entities import MessageStatus, TgChannel, TgMessage
from utils.dates import parse_iso_date
from utils.encoder import TelegramJSONEncoder

settings = get_settings()
_sync_lock = asyncio.Lock()
_client_lock = asyncio.Lock()
_telegram_rate_lock = asyncio.Lock()
_last_telegram_request_at = 0.0
_image_download_locks: dict[tuple[int, int], asyncio.Lock] = {}
_telegram_client: TelegramClient | None = None


def normalize_channel_id(channel_id: int) -> int:
    if channel_id > 0:
        return int(f"-100{channel_id}")
    return channel_id


def _ensure_telegram_config(action: str) -> None:
    if not settings.api_id or not settings.api_hash:
        raise RuntimeError(
            f"Please configure API_ID/API_HASH in .env or backend/.env.local before {action}"
        )


async def _get_telegram_client() -> TelegramClient:
    global _telegram_client
    async with _client_lock:
        if _telegram_client is None:
            _telegram_client = TelegramClient(
                settings.session_name,
                settings.api_id,
                settings.api_hash,
                proxy=settings.proxy,
            )
        if not _telegram_client.is_connected():
            await _telegram_client.connect()
        return _telegram_client


async def shutdown_telegram_client() -> None:
    global _telegram_client
    async with _client_lock:
        if _telegram_client is None:
            return
        if _telegram_client.is_connected():
            await _telegram_client.disconnect()
        _telegram_client = None


async def _wait_for_telegram_slot() -> None:
    global _last_telegram_request_at
    min_interval = max(settings.telegram_request_min_interval_seconds, 0)
    if min_interval <= 0:
        return

    async with _telegram_rate_lock:
        now = time.monotonic()
        wait_seconds = min_interval - (now - _last_telegram_request_at)
        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)
        _last_telegram_request_at = time.monotonic()


def _extract_channel_id(message: dict[str, Any]) -> int:
    explicit_channel_id = message.get("channel_id")
    if explicit_channel_id is not None:
        return normalize_channel_id(int(explicit_channel_id))

    peer = message.get("peer_id") or {}
    channel_id = peer.get("channel_id")
    if channel_id is None:
        return 0
    return normalize_channel_id(int(channel_id))


def _compose_link(channel_id: int, message_id: int) -> str:
    channel_text = str(channel_id).replace("-100", "")
    return f"https://t.me/c/{channel_text}/{message_id}"


def _channel_title(entity: Any, channel_id: int) -> str:
    title = getattr(entity, "title", None) or getattr(entity, "first_name", None)
    username = getattr(entity, "username", None)
    return str(title or username or channel_id)


def _channel_username(entity: Any) -> str | None:
    username = getattr(entity, "username", None)
    return str(username) if username else None


def _text_to_safe_html(text: str) -> str:
    escaped = html.escape(text)
    return escaped.replace("\n", "<br>")


def _render_message_html(message: Any) -> str:
    direct_html = getattr(message, "text_html", None)
    if isinstance(direct_html, str) and direct_html.strip():
        return direct_html.strip()

    text = (getattr(message, "message", None) or "").strip()
    entities = getattr(message, "entities", None) or []
    if text and entities:
        try:
            return telethon_html.unparse(text, entities)
        except Exception:
            return _text_to_safe_html(text)

    return _text_to_safe_html(text) if text else ""


def normalize_group(messages: list[dict[str, Any]]) -> dict[str, Any]:
    head = messages[0]
    message_id = min(int(message["id"]) for message in messages)
    grouped_id = str(head.get("grouped_id")) if head.get("grouped_id") else None

    content = "[纯媒体消息]"
    images: list[str] = []
    media_type = "Text"
    views = 0
    forwards = 0
    replies = 0

    for message in messages:
        rendered_html = (message.get("rendered_html") or "").strip()
        text = (message.get("message") or "").strip()
        if content == "[纯媒体消息]":
            if rendered_html:
                content = rendered_html
            elif text:
                content = _text_to_safe_html(text)

        local_image = message.get("local_image_url")
        if local_image:
            images.append(local_image)
            media_type = "Photo"
        else:
            media = message.get("media") or {}
            media_tag = media.get("_", "")
            if media_tag:
                media_type = media_tag.replace("MessageMedia", "") or media_type

        views = max(views, int(message.get("views") or 0))
        forwards = max(forwards, int(message.get("forwards") or 0))
        reply = message.get("replies") or {}
        if isinstance(reply, dict):
            replies = max(replies, int(reply.get("replies") or 0))

    channel_id = _extract_channel_id(head)
    return {
        "channel_id": channel_id,
        "message_id": message_id,
        "grouped_id": grouped_id,
        "sent_at": parse_iso_date(head.get("date")),
        "content": content,
        "media_type": media_type,
        "images": images,
        "views": views,
        "forwards": forwards,
        "replies": replies,
        "message_link": _compose_link(channel_id, message_id),
    }


def group_messages(raw_messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    singles: list[dict[str, Any]] = []

    for message in raw_messages:
        grouped_id = message.get("grouped_id")
        if grouped_id is None:
            singles.append(message)
        else:
            grouped.setdefault(str(grouped_id), []).append(message)

    normalized = [normalize_group([message]) for message in singles]
    normalized.extend(normalize_group(items) for items in grouped.values())
    normalized.sort(key=lambda item: item["message_id"])
    return normalized


async def _upsert_channel(
    session: AsyncSession,
    channel_id: int,
    name: str,
    username: str | None,
) -> None:
    channel = await session.get(TgChannel, channel_id)
    if channel is None:
        session.add(TgChannel(id=channel_id, name=name, username=username))
        return

    channel.name = name
    channel.username = username


async def refresh_account_channels(session: AsyncSession) -> list[dict[str, Any]]:
    _ensure_telegram_config("加载频道列表")

    channels: list[dict[str, Any]] = []
    async with _sync_lock:
        client = await _get_telegram_client()
        try:
            await _wait_for_telegram_slot()
            async for dialog in client.iter_dialogs():
                entity = getattr(dialog, "entity", None)
                if not getattr(dialog, "is_channel", False):
                    continue
                if getattr(dialog, "is_group", False):
                    continue
                if not getattr(entity, "broadcast", False):
                    continue
                if getattr(entity, "megagroup", False):
                    continue

                raw_channel_id = getattr(entity, "id", None) or dialog.id
                channel_id = normalize_channel_id(int(raw_channel_id))
                channel = {
                    "id": channel_id,
                    "name": _channel_title(entity, channel_id),
                    "username": _channel_username(entity),
                }
                await _upsert_channel(
                    session,
                    channel["id"],
                    channel["name"],
                    channel["username"],
                )
                channels.append(channel)
        except errors.FloodWaitError as error:
            raise RuntimeError(f"触发频率限制，请等待 {error.seconds} 秒") from error

    await session.commit()
    channels.sort(key=lambda item: (item["name"].lower(), item["id"]))
    return channels


async def fetch_channel_data(
    channel_id: int,
    limit: Optional[int] = 200,
    persist_output: bool = False,
    min_id: int = 0,
) -> dict[str, Any]:
    _ensure_telegram_config("同步 Telegram")

    settings.image_path.mkdir(parents=True, exist_ok=True)
    normalized_channel_id = normalize_channel_id(channel_id)
    payload: dict[str, Any] = {"channel": None, "messages": []}

    async with _sync_lock:
        client = await _get_telegram_client()
        try:
            await _wait_for_telegram_slot()
            entity = await client.get_entity(normalized_channel_id)
            if not getattr(entity, "broadcast", False) or getattr(entity, "megagroup", False):
                raise RuntimeError("请选择一个 Telegram 广播频道")

            raw_channel_id = getattr(entity, "id", None) or normalized_channel_id
            normalized_channel_id = normalize_channel_id(int(raw_channel_id))
            payload["channel"] = {
                "id": normalized_channel_id,
                "name": _channel_title(entity, normalized_channel_id),
                "username": _channel_username(entity),
            }

            await _wait_for_telegram_slot()
            async for message in client.iter_messages(
                entity,
                limit=limit,
                min_id=min_id,
                wait_time=max(settings.telegram_sync_wait_time_seconds, 0),
            ):
                message_dict = message.to_dict()
                message_dict["channel_id"] = normalized_channel_id
                message_dict["rendered_html"] = _render_message_html(message)
                message_dict["local_image_url"] = None
                if message.media and hasattr(message.media, "photo"):
                    message_dict["local_image_url"] = (
                        f"/images/{normalized_channel_id}/{message.id}.jpg"
                    )
                payload["messages"].append(message_dict)
        except errors.FloodWaitError as error:
            raise RuntimeError(f"触发频率限制，请等待 {error.seconds} 秒") from error

    if persist_output:
        output = settings.output_path
        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, cls=TelegramJSONEncoder),
            encoding="utf-8",
        )
    return payload


async def import_messages_to_db(
    session: AsyncSession,
    raw_messages: list[dict[str, Any]],
    channel: dict[str, Any] | None = None,
) -> tuple[int, int, int]:
    normalized = group_messages(raw_messages)
    inserted = 0
    updated = 0
    last_message_id = 0
    channel_meta = channel or {}
    meta_channel_id = int(channel_meta["id"]) if channel_meta.get("id") else None

    if meta_channel_id is not None:
        await _upsert_channel(
            session,
            meta_channel_id,
            str(channel_meta.get("name") or meta_channel_id),
            channel_meta.get("username"),
        )

    for payload in normalized:
        channel_id = int(payload["channel_id"])
        message_id = int(payload["message_id"])
        last_message_id = max(last_message_id, message_id)

        if channel_id != meta_channel_id:
            await _upsert_channel(session, channel_id, str(channel_id), None)

        item = await session.get(
            TgMessage,
            {"channel_id": channel_id, "message_id": message_id},
        )
        if item is None:
            session.add(TgMessage(**payload))
            session.add(
                MessageStatus(channel_id=channel_id, message_id=message_id, is_read=False)
            )
            inserted += 1
        else:
            for key, value in payload.items():
                setattr(item, key, value)
            updated += 1

    await session.commit()
    return inserted, updated, last_message_id


async def get_or_download_message_image(channel_id: int, message_id: int) -> Optional[Path]:
    _ensure_telegram_config("访问图片")

    settings.image_path.mkdir(parents=True, exist_ok=True)
    normalized_channel_id = normalize_channel_id(channel_id)
    channel_image_path = settings.image_path / str(normalized_channel_id)
    channel_image_path.mkdir(parents=True, exist_ok=True)
    file_path = channel_image_path / f"{message_id}.jpg"
    if file_path.exists():
        return file_path

    lock_key = (normalized_channel_id, message_id)
    image_lock = _image_download_locks.setdefault(lock_key, asyncio.Lock())
    async with image_lock:
        if file_path.exists():
            return file_path

        async with _sync_lock:
            client = await _get_telegram_client()
            await _wait_for_telegram_slot()
            message = await client.get_messages(normalized_channel_id, ids=message_id)
            if not message or not message.media or not hasattr(message.media, "photo"):
                return None
            await _wait_for_telegram_slot()
            await client.download_media(message.media, file=str(file_path))
            return file_path if file_path.exists() else None
