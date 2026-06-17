# TG Reader

**Language:** English | [简体中文](README.zh-CN.md)

TG Reader is a personal Telegram broadcast-channel reader. It refreshes the
channel list from your logged-in Telegram account, syncs selected channels on
demand, and provides a web UI for reading, filtering, image preview, and
read/unread management.

## Features

- Refresh broadcast channels from the current Telegram account.
- Sync one selected channel on demand; page load does not auto-sync messages.
- Browse local messages by channel, keyword, unread state, and page size.
- Show the source channel when browsing all channels.
- Lazy-load Telegram images through `/images/{channel_id}/{message_id}.jpg`.
- Store messages by `(channel_id, message_id)` to avoid multi-channel ID collisions.

## Screenshots

Message list with channel sidebar, filters, read status, and image thumbnails:

![Message list](docs/screenshots/message-list.png)

Hover preview for long message content:

![Message hover preview](docs/screenshots/message-hover-preview.png)

Image lightbox with gallery navigation:

![Image lightbox](docs/screenshots/image-lightbox.png)

Read-state actions and Telegram link shortcuts:

![Read-state actions](docs/screenshots/read-state-actions.png)

## Stack

- Backend: FastAPI, SQLAlchemy async, Pydantic, Telethon
- Frontend: Vue 3, TypeScript, Vite, Element Plus
- Database: PostgreSQL

## Responsible Use

TG Reader uses the official Telegram API through Telethon and only reads
channels that are accessible from the logged-in Telegram account. It is intended
for personal reading, filtering, and local message management.

Do not use this project to redistribute channel content, bypass access
restrictions, mirror Telegram channels, or collect Telegram data for AI training
or other unauthorized purposes. Users are responsible for respecting Telegram's
terms and the rights of channel owners.

## Configuration

The repository only commits one public environment template:

```text
.env.example
```

Create your private Docker configuration from it:

```bash
cp .env.example .env
```

Then edit `.env` and fill in your own values:

```env
POSTGRES_USER=tg_reader
POSTGRES_PASSWORD=change_me
POSTGRES_DB=tg_reader

API_ID=
API_HASH=
SESSION_NAME=telegram_session
```

Get `API_ID` and `API_HASH` from your Telegram developer account:

https://my.telegram.org/apps

Docker Compose reads the root `.env` automatically, so Docker commands do not
need `--env-file`. Never commit `.env`, `.env.local`, `backend/.env.local`,
`frontend/.env.local`, or Telethon `*.session` files.

## Docker Usage

Build the backend image once, then create the Telegram session:

```bash
docker compose build backend
docker compose run --rm backend uv run python scripts/login_telegram.py
```

Start all services:

```bash
docker compose up -d --build
```

Stop all services:

```bash
docker compose down
```

Reset the Docker database and volumes:

```bash
docker compose down -v
```

Docker services:

- `db`: PostgreSQL
- `backend`: FastAPI API on host port `8000`
- `frontend`: nginx-served Vue app on host port `80`

The frontend container proxies `/api/` and `/images/` to the backend service.
Docker stores the Telegram session in the `telegram_session` volume and image
cache in the `backend_images` volume.

## Local Development

For local development, keep using the same root `.env` as the shared base
configuration. The backend also reads `backend/.env.local` if you want private
local overrides, and Vite reads `frontend/.env.local` if you want frontend-only
overrides.

Start PostgreSQL from the repository root:

```bash
docker compose up -d db
```

Start the backend:

```bash
cd backend
uv sync
uv run python main.py
```

Start the frontend in another terminal:

```bash
cd frontend
pnpm install
pnpm dev
```

Default local URLs:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

To bind the Vite dev server to a specific LAN address, create or edit
`frontend/.env.local`:

```env
VITE_DEV_HOST=0.0.0.0
VITE_DEV_PORT=5173
VITE_API_BASE=http://localhost:8000/api
VITE_IMAGE_BASE=http://localhost:8000
```

## Usage Flow

1. Open the frontend.
2. Wait for the channel sidebar to load channels from the logged-in Telegram account.
3. Select a channel.
4. Click sync to import messages for the selected channel.
5. Use channel, keyword, unread, and page-size filters to browse local messages.

## Checks

Backend:

```bash
cd backend
uv run python -m compileall api config crud dao model service scripts main.py
```

Frontend:

```bash
cd frontend
pnpm type-check
pnpm build-only
pnpm lint
```

Docker Compose:

```bash
docker compose config --quiet
```

## License

MIT
