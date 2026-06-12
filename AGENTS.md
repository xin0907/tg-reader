# AGENTS.md

This file provides guidance to Codex when working with code in this repository.

## Commands

```bash
# Docker (all services: db + backend + frontend)
docker compose up -d
docker compose up -d --build
docker compose down
docker compose down -v

# Backend dev (Python/FastAPI)
cd backend && uv sync
cd backend && uv run python scripts/login_telegram.py
cd backend && uv run python main.py

# Frontend dev (Vue 3/Vite)
cd frontend && pnpm install
cd frontend && pnpm dev
cd frontend && pnpm build
cd frontend && pnpm lint
cd frontend && pnpm format
```

## Architecture

**Read flow:** Handler (`api/messages.py`) -> DAO (`dao/messages.py`) -> SQLAlchemy ORM entities (`model/entities.py`) -> Pydantic DTOs (`crud/schemas.py`) -> JSON response.

**Channel flow:** `GET /api/channels` calls Telethon `iter_dialogs()`, keeps only broadcast channels, upserts `tg_channels`, and returns `id/name/username` for the frontend channel sidebar.

**Sync flow:** The user must select a channel before syncing. Handler -> Service (`service/telegram.py`) -> Telethon `iter_messages(min_id=...)` -> message grouping/normalization -> `import_messages_to_db()`. Incremental sync reads `max(tg_messages.message_id)` for the selected `channel_id`.

**Images:** Sync stores lazy proxy URLs only. Images are downloaded on first `GET /images/{channel_id}/{message_id}.jpg` and cached under a per-channel image directory.

**Client singleton pattern:** `_get_telegram_client()` lazily creates and caches one `TelegramClient`, protected by `_client_lock`. Telegram calls are rate-limited by `_telegram_rate_lock` and `telegram_request_min_interval_seconds`. Sync, channel refresh, and image downloads share `_sync_lock` to avoid concurrent session writes.

**Three DB entities:** `TgChannel` stores channel names/usernames. `TgMessage` uses composite primary key `(channel_id, message_id)` because Telegram message IDs are only unique inside a channel. `MessageStatus` uses the same composite key and tracks `is_read`.

**Message grouping:** Telegram albums sharing `grouped_id` are collapsed into one normalized entry with the smallest `message_id`, max stats, and aggregated image URLs. `images` is stored as PostgreSQL JSONB.

**Frontend pattern:** Single-page Vue app with no router or Pinia store. `HomeView.vue` owns state. `ChannelSidebar` renders searchable, collapsible channel navigation with loading state. `FilterBar` emits debounced keyword/read/page-size criteria and sync payloads. `MessageTable` renders HTML with `v-html` and lazy-loads backend image URLs.

## Key conventions

- API, frontend, and database fields use `snake_case`.
- `crud/` contains Pydantic schemas only; database work lives in `dao/`.
- Channel selection comes from the current Telegram account dialogs.
- Docker Compose reads root `.env` automatically. The backend reads root `.env` and then `backend/.env.local` for direct local overrides.
- Telethon sessions are local runtime credentials. Generate them with `backend/scripts/login_telegram.py`; never commit `*.session`.
- PostgreSQL is the documented/default database. Keep database access behind SQLAlchemy async APIs.

## Docker networking

Frontend nginx serves the Vue build and proxies `/api/` and `/images/` to `http://backend:8000`. Backend connects to PostgreSQL at `db:5432` inside Compose. Host-mapped ports are only for local access.
