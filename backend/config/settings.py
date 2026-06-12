from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            Path(__file__).resolve().parents[2] / ".env",
            Path(__file__).resolve().parents[1] / ".env.local",
        ),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    app_host: str = "127.0.0.1"
    app_port: int = 8000

    database_url: str = "postgresql+asyncpg://tg_reader:change_me@localhost:5432/tg_reader"

    api_id: int = 0
    api_hash: str = ""
    session_name: str = "telegram_session"
    proxy_scheme: Optional[str] = None
    proxy_host: Optional[str] = None
    proxy_port: Optional[int] = None

    output_file: str = "channel_full_data.json"
    image_dir: str = "static/images"
    telegram_sync_wait_time_seconds: float = 0.5
    telegram_request_min_interval_seconds: float = 0.8

    @property
    def output_path(self) -> Path:
        return Path(self.output_file)

    @property
    def image_path(self) -> Path:
        return Path(self.image_dir)

    @property
    def proxy(self) -> Optional[tuple[str, str, int]]:
        if self.proxy_scheme and self.proxy_host and self.proxy_port:
            return (self.proxy_scheme, self.proxy_host, self.proxy_port)
        return None


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
