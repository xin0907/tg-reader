from datetime import datetime, timezone

from sqlalchemy import BIGINT, Boolean, DateTime, ForeignKeyConstraint, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TgChannel(Base):
    __tablename__ = "tg_channels"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=func.now(),
    )


class TgMessage(Base):
    __tablename__ = "tg_messages"

    channel_id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=False)
    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    grouped_id: Mapped[str | None] = mapped_column(String(100), index=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="[纯媒体消息]")
    media_type: Mapped[str | None] = mapped_column(String(50))
    images: Mapped[list[str]] = mapped_column(JSONB, default=list)
    views: Mapped[int] = mapped_column(Integer, default=0)
    forwards: Mapped[int] = mapped_column(Integer, default=0)
    replies: Mapped[int] = mapped_column(Integer, default=0)
    message_link: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    status: Mapped["MessageStatus"] = relationship(
        back_populates="message",
        cascade="all, delete-orphan",
        uselist=False,
    )


class MessageStatus(Base):
    __tablename__ = "message_status"
    __table_args__ = (
        ForeignKeyConstraint(
            ["channel_id", "message_id"],
            ["tg_messages.channel_id", "tg_messages.message_id"],
            ondelete="CASCADE",
        ),
    )

    channel_id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=False)
    message_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=func.now(),
    )

    message: Mapped[TgMessage] = relationship(back_populates="status")
