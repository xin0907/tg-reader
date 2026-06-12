import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from api.messages import router
from config.settings import get_settings
from model.init_db import init_db
from service.telegram import get_or_download_message_image, shutdown_telegram_client

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    os.makedirs(settings.image_dir, exist_ok=True)
    await init_db()
    try:
        yield
    finally:
        await shutdown_telegram_client()


app = FastAPI(title="TG-Pulse API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/images/{channel_id}/{file_name}", summary="按需下载并返回图片")
async def get_image(channel_id: int, file_name: str):
    if not file_name.endswith(".jpg"):
        raise HTTPException(status_code=404, detail="仅支持 jpg 图片")
    raw_id = file_name.removesuffix(".jpg")
    if not raw_id.isdigit():
        raise HTTPException(status_code=404, detail="无效图片 ID")

    image_path = await get_or_download_message_image(channel_id, int(raw_id))
    if image_path is None:
        raise HTTPException(status_code=404, detail="图片不存在")
    return FileResponse(path=image_path, media_type="image/jpeg")


app.include_router(router, prefix="/api", tags=["Messages"])


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.app_host, port=settings.app_port, reload=True)
