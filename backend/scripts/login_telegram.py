import asyncio
import sys
from getpass import getpass
from pathlib import Path

from telethon import TelegramClient, errors

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from config.settings import get_settings


async def login() -> None:
    settings = get_settings()
    if not settings.api_id or not settings.api_hash:
        raise SystemExit(
            "Please fill API_ID and API_HASH in .env or backend/.env.local before logging in."
        )

    client = TelegramClient(
        settings.session_name,
        settings.api_id,
        settings.api_hash,
        proxy=settings.proxy,
    )
    await client.connect()
    try:
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"Already logged in as {getattr(me, 'username', None) or me.id}.")
            return

        phone = input("Telegram phone number, including country code: ").strip()
        if not phone:
            raise SystemExit("Phone number is required.")

        await client.send_code_request(phone)
        code = input("Telegram login code: ").strip()
        if not code:
            raise SystemExit("Login code is required.")

        try:
            await client.sign_in(phone=phone, code=code)
        except errors.SessionPasswordNeededError:
            password = getpass("Two-step verification password: ")
            await client.sign_in(password=password)

        me = await client.get_me()
        print(f"Logged in as {getattr(me, 'username', None) or me.id}.")
        print(f"Session saved to: {settings.session_name}.session")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(login())
