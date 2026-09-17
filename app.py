from __future__ import annotations

import logging
import os

import asyncpg
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Settings
from utils.logging_config import setup_logging

from routers.callbacks import router as callbacks_router
from routers.commands import router as commands_router
from routers.intake import router as intake_router
from routers.thumbnails import router as thumbnails_router

from services.cooldown import CooldownManager
from services.caption_style_store import CaptionStyleStore
from services.format_preference_store import FormatPreferenceStore
from services.request_store import RequestStore
from services.thumbnail_store import ThumbnailStore


async def create_database_pool() -> asyncpg.Pool:
    database_url = os.environ.get("DATABASE_URL", "").strip()

    if not database_url:
        raise RuntimeError("DATABASE_URL is required")

    return await asyncpg.create_pool(
        dsn=database_url,
        min_size=1,
        max_size=5,
    )


async def create_dispatcher(
    settings: Settings,
    pool: asyncpg.Pool,
) -> Dispatcher:
    dispatcher = Dispatcher()

    format_store = FormatPreferenceStore(pool)
    caption_store = CaptionStyleStore(pool)

    await format_store.init()
    await caption_store.init()

    dispatcher.include_router(commands_router)
    dispatcher.include_router(thumbnails_router)
    dispatcher.include_router(intake_router)
    dispatcher.include_router(callbacks_router)

    dispatcher.workflow_data.update(
        settings=settings,
        cooldown=CooldownManager(
            timeout_seconds=settings.process_max_timeout
        ),
        request_store=RequestStore(
            settings.requests_dir,
            settings.work_dir,
        ),
        thumbnail_store=ThumbnailStore(
            settings.thumbnails_dir
        ),
        format_store=format_store,
        caption_store=caption_store,
    )

    return dispatcher


async def run() -> None:
    setup_logging()

    settings = Settings.from_env()
    settings.ensure_directories()

    pool = await create_database_pool()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        ),
    )

    try:
        dispatcher = await create_dispatcher(
            settings,
            pool,
        )

        logging.getLogger(__name__).info(
            "Bot is starting | download_dir=%s requests_dir=%s proxy=%s cooldown=%ss",
            settings.download_location,
            settings.requests_dir,
            "enabled" if settings.http_proxy else "disabled",
            settings.process_max_timeout,
        )

        await dispatcher.start_polling(bot)

    finally:
        await bot.session.close()
        await pool.close()
