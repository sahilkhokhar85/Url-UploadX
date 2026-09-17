from __future__ import annotations

import re
from urllib.parse import urlparse

from aiogram.types import MessageEntity

from utils.models import ParsedInput


IMAGE_LABELS = {
    "portrait": "Portrait",
    "zee5 poster": "Zee5 Poster",
    "zee5": "Zee5 Poster",
    "app cover": "App Cover",
    "logo": "Logo",
}


def _entity_text(
    text: str,
    entity: MessageEntity,
) -> str:
    return text[entity.offset: entity.offset + entity.length].strip()


def extract_labeled_links(
    text: str,
    entities: list[MessageEntity] | None,
) -> tuple[list[tuple[str, str]], str] | None:
    if not entities:
        return None

    found: dict[str, str] = {}

    for entity in entities:
        if entity.type != "text_link" or not entity.url:
            continue

        label_text = _entity_text(text, entity)
        label_key = re.sub(r"\s+", " ", label_text.lower()).strip()

        if label_key in IMAGE_LABELS:
            found[IMAGE_LABELS[label_key]] = entity.url.strip()

    required_order = [
        "Portrait",
        "Zee5 Poster",
        "App Cover",
        "Logo",
    ]

    links = [
        (label, found[label])
        for label in required_order
        if label in found
    ]

    if not links:
        return None

    title = ""

    for line in text.splitlines():
        clean_line = line.strip()

        if not clean_line:
            continue

        lowered = clean_line.lower()

        if any(
            lowered.startswith(label.lower() + ":")
            for label in required_order
        ):
            continue

        if clean_line.startswith(("http://", "https://")):
            continue

        title = clean_line

    if not title:
        title = "Downloaded Images"

    return links, title


def extract_link_text(
    text: str,
    entities: list[MessageEntity] | None,
) -> str | None:
    if entities:
        for entity in entities:
            if entity.type == "text_link" and entity.url:
                return entity.url

            if entity.type == "url":
                return text[
                    entity.offset: entity.offset + entity.length
                ]

    if "http://" in text or "https://" in text:
        return text

    return None


def _extract_url(
    text: str,
    entities: list[MessageEntity] | None,
) -> str:
    entity_url = extract_link_text(text, entities)

    if not entity_url:
        raise ValueError("No URL found in the message")

    return entity_url.strip()


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    if hostname.endswith("hotstar.com") and "/image/upload/" in url:
        url = re.sub(
            r"/image/upload/[^/]+/sources/",
            "/image/upload/sources/",
            url,
        )

        if not url.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        ):
            url = f"{url}.jpg"

        return url

    if hostname.endswith("zee5.com") and "/image/upload/" in url:
        url = re.sub(
            r"/image/upload/[^/]+/resources/",
            "/image/upload/resources/",
            url,
        )

        if not url.lower().endswith(
            (".jpg", ".jpeg", ".png", ".webp")
        ):
            url = f"{url}.jpg"

        return url

    if hostname.endswith("sonyliv.com"):
        match = re.search(
            r"^(.*?\.jpg)",
            url,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

        return url

    if hostname == "m.media-amazon.com":
        return re.sub(
            r"\._[\w,]+_\.jpg$",
            ".jpg",
            url,
            flags=re.IGNORECASE,
        )

    return url


def parse_user_input(
    text: str,
    entities: list[MessageEntity] | None = None,
) -> ParsedInput:
    if "|" in text:
        parts = [
            part.strip()
            for part in text.split("|")
        ]

        if len(parts) == 2:
            return ParsedInput(
                source_url=_normalize_url(parts[0]),
                custom_file_name=parts[1],
            )

        if len(parts) == 4:
            return ParsedInput(
                source_url=_normalize_url(parts[0]),
                custom_file_name=parts[1],
                username=parts[2],
                password=parts[3],
            )

    if " * " in text:
        url, file_name = [
            part.strip()
            for part in text.split(" * ", maxsplit=1)
        ]

        return ParsedInput(
            source_url=_normalize_url(url),
            custom_file_name=file_name,
        )

    return ParsedInput(
        source_url=_normalize_url(
            _extract_url(text, entities)
        )
    )


def is_probable_youtube_url(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").lower()

    return (
        hostname == "youtube.com"
        or hostname.endswith(".youtube.com")
        or hostname == "youtu.be"
        or hostname.endswith(".youtu.be")
    )
