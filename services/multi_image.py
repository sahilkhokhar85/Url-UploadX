from __future__ import annotations

import logging
from datetime import datetime

from aiogram.types import Message

from config import Settings
from services.caption_style_store import CaptionStyleStore
from services.direct_downloads import download_direct_file
from services.request_store import RequestStore
from services.thumbnail_store import ThumbnailStore
from services.telegram_uploads import upload_artifact
from utils.models import DownloadOption, ParsedInput

logger = logging.getLogger(__name__)


async def execute_multi_image_request(
    *,
    status_message: Message,
    source_message: Message,
    user_id: int,
    links: list[tuple[str, str]],
    title: str,
    settings: Settings,
    request_store: RequestStore,
    thumbnail_store: ThumbnailStore,
    caption_store: CaptionStyleStore,
) -> None:
    token = request_store.create_token()
    work_dir = request_store.work_directory(token)
    started_at = datetime.now()

    try:
        caption_style = await caption_store.get(user_id)

        for index, (label, url) in enumerate(
            links,
            start=1,
        ):
            await status_message.edit_text(
                f"⬇️ Downloading <b>{label}</b> "
                f"({index}/{len(links)})"
            )

            parsed = ParsedInput(
                source_url=url,
                custom_file_name=None,
            )

            option = DownloadOption(
                option_id=f"multi_{index}",
                label=label,
                send_type="photo",
                mode="direct",
                file_ext="jpg",
            )

            artifact = await download_direct_file(
                status_message=status_message,
                parsed_input=parsed,
                option=option,
                settings=settings,
                work_dir=work_dir,
                suggested_ext="jpg",
            )

            # Downloaded filename caption mein rahega.
            artifact.caption = artifact.file_name

            # Portrait / Poster / Cover ke saath upload_artifact()
            # automatically link send nahi karega.
            artifact.skip_link = True

            await upload_artifact(
                bot=source_message.bot,
                status_message=status_message,
                source_message=source_message,
                artifact=artifact,
                thumbnail_path=thumbnail_store.get(user_id),
                started_at=started_at,
                caption_style=caption_style,
            )

        await status_message.edit_text(
            "✅ All images uploaded successfully."
        )

    except Exception as exc:
        logger.exception(
            "Multi-image request failed | user=%s error=%s",
            user_id,
            exc,
        )

        await status_message.edit_text(
            f"❌ Upload failed\n<code>{exc}</code>"
        )

    finally:
        request_store.delete(token)
