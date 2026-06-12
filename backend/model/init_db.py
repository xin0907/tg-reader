from sqlalchemy import text

from model.db import engine
from model.entities import Base


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS idx_status_unread "
                "ON message_status(channel_id, message_id) "
                "WHERE is_read = FALSE"
            )
        )
