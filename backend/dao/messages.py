from sqlalchemy import Select, and_, func, or_, select, tuple_, update
from sqlalchemy.ext.asyncio import AsyncSession

from model.entities import MessageStatus, TgMessage
from utils.dates import parse_iso_date


async def query_messages(
    session: AsyncSession,
    *,
    channel_id: int | None,
    keyword: str | None,
    is_read: bool | None,
    start_date: str | None,
    end_date: str | None,
    page: int,
    page_size: int,
) -> tuple[int, list[tuple[TgMessage, MessageStatus | None]]]:
    stmt: Select = select(TgMessage, MessageStatus).join(
        MessageStatus,
        and_(
            MessageStatus.channel_id == TgMessage.channel_id,
            MessageStatus.message_id == TgMessage.message_id,
        ),
        isouter=True,
    )

    conditions = []
    if channel_id is not None:
        conditions.append(TgMessage.channel_id == channel_id)
    if keyword:
        conditions.append(TgMessage.content.ilike(f"%{keyword}%"))
    if is_read is not None:
        conditions.append(
            or_(
                MessageStatus.is_read == is_read,
                and_(MessageStatus.message_id.is_(None), is_read is False),
            )
        )

    start_dt = parse_iso_date(start_date) if start_date else None
    end_dt = parse_iso_date(end_date) if end_date else None
    if start_dt:
        conditions.append(TgMessage.sent_at >= start_dt)
    if end_dt:
        conditions.append(TgMessage.sent_at <= end_dt)

    if conditions:
        stmt = stmt.where(*conditions)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(total_stmt)).scalar_one()

    stmt = (
        stmt.order_by(TgMessage.sent_at.desc(), TgMessage.message_id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await session.execute(stmt)).all()
    return total, rows


async def batch_update_read_status(
    session: AsyncSession, message_keys: list[tuple[int, int]], is_read: bool
) -> int:
    unique_keys = list(dict.fromkeys(message_keys))
    if not unique_keys:
        return 0

    existing = (
        await session.execute(
            select(MessageStatus.channel_id, MessageStatus.message_id).where(
                tuple_(MessageStatus.channel_id, MessageStatus.message_id).in_(unique_keys)
            )
        )
    ).all()
    existing_keys = {(int(channel_id), int(message_id)) for channel_id, message_id in existing}

    for channel_id, message_id in unique_keys:
        if (channel_id, message_id) not in existing_keys:
            session.add(
                MessageStatus(channel_id=channel_id, message_id=message_id, is_read=is_read)
            )

    if existing_keys:
        await session.execute(
            update(MessageStatus)
            .where(
                tuple_(MessageStatus.channel_id, MessageStatus.message_id).in_(
                    list(existing_keys)
                )
            )
            .values(is_read=is_read)
        )

    await session.commit()
    return len(unique_keys)


async def mark_all_read(session: AsyncSession, channel_id: int | None) -> int:
    stmt = select(TgMessage.channel_id, TgMessage.message_id).order_by(
        TgMessage.sent_at.desc(), TgMessage.message_id.desc()
    )
    if channel_id is not None:
        stmt = stmt.where(TgMessage.channel_id == channel_id)
    target_keys = [
        (int(row.channel_id), int(row.message_id)) for row in (await session.execute(stmt)).all()
    ]
    if not target_keys:
        return 0
    return await batch_update_read_status(session, target_keys, True)


async def get_last_message_id(session: AsyncSession, channel_id: int) -> int:
    stmt = select(func.max(TgMessage.message_id)).where(TgMessage.channel_id == channel_id)
    last_message_id = (await session.execute(stmt)).scalar_one_or_none()
    return int(last_message_id or 0)
