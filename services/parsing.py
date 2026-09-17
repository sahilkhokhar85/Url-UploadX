from __future__ import annotations

import re
from urllib.parse import urlparse

from aiogram.types import MessageEntity

from utils.models import ParsedInput


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
                    entity.offset : entity.offset + entity.length
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

    # Hotstar image links
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

    # Zee5 image links
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

    # SonyLIV image links
    if hostname.endswith("sonyliv.com"):
        match = re.search(
            r"^(.*?\.jpg)",
            url,
            flags=re.IGNORECASE,
        )

        if match:
            return match.group(1)

        return url

    # Prime Video / Amazon image links
    if hostname == "m.media-amazon.com":
        url = re.sub(
            r"\._[\w,]+_\.jpg$",
            ".jpg",
            url,
            flags=re.IGNORECASE,
        )

        return url

    return url


def get_image_label(label_text: str) -> str | None:
    """
    Label detection:

    Portrait              -> Portrait
    Zee5 Poster           -> Poster
    Netflix Poster        -> Poster
    SonyLIV Poster        -> Poster

    Cover                 -> Cover
    App Cover             -> Cover
    Netflix Cover         -> Cover
    Zee5 Cover            -> Cover

    Logo                  -> ignored
    """

    label = label_text.strip().lower()

    # Sirf Portrait word detect
    if "portrait" in label:
        return "Portrait"

    # OTT naam ignore karke sirf Poster word detect
    if "poster" in label:
        return "Poster"

    # App ho ya na ho, sirf Cover word detect
    if "cover" in label:
        return "Cover"

    # Logo aur unknown labels ignore
    return None


def extract_labeled_links(
    text: str,
    entities: list[MessageEntity] | None,
) -> tuple[list[tuple[str, str]], str] | None:
    """
    Example input:

    Zee5 Poster: Link
    Portrait: Link
    App Cover: Link
    Logo: Link

    Returns:

    [
        ("Portrait", "portrait_url"),
        ("Poster", "poster_url"),
        ("Cover", "cover_url"),
    ]
    """

    if not text or not entities:
        return None

    lines = text.splitlines()

    # Har line ka character offset range
    line_ranges: list[tuple[int, int, str]] = []
    current_offset = 0

    for line in lines:
        line_start = current_offset
        line_end = current_offset + len(line)

        line_ranges.append(
            (
                line_start,
                line_end,
                line,
            )
        )

        current_offset = line_end + 1

    found_links: dict[str, str] = {}

    for entity in entities:
        entity_url: str | None = None

        if entity.type == "text_link" and entity.url:
            entity_url = entity.url

        elif entity.type == "url":
            entity_url = text[
                entity.offset : entity.offset + entity.length
            ]

        if not entity_url:
            continue

        matching_line: str | None = None

        for line_start, line_end, line_text in line_ranges:
            if line_start <= entity.offset <= line_end:
                matching_line = line_text
                break

        if not matching_line:
            continue

        # Link se pehle ka text label hoga
        label_text = matching_line.split(
            ":",
            1,
        )[0].strip()

        image_label = get_image_label(label_text)

        # Logo / unknown label ignore
        if not image_label:
            continue

        found_links[image_label] = _normalize_url(
            entity_url.strip()
        )

    if not found_links:
        return None

    # Processing order
    required_order = [
        "Portrait",
        "Poster",
        "Cover",
    ]

    ordered_links: list[tuple[str, str]] = []

    for label in required_order:
        if label in found_links:
            ordered_links.append(
                (
                    label,
                    found_links[label],
                )
            )

    if not ordered_links:
        return None

    # Title intentionally return nahi karna.
    # Multi-image caption file name se banega.
    return ordered_links, ""


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
            for part in text.split(
                " * ",
                maxsplit=1,
            )
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
    hostname = (
        urlparse(url).hostname or ""
    ).lower()

    return (
        hostname == "youtube.com"
        or hostname.endswith(".youtube.com")
        or hostname == "youtu.be"
        or hostname.endswith(".youtu.be")
    )
