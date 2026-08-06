from __future__ import annotations

import re

_TAG_PATTERN = re.compile(r"</?(?:b|i|code|u|strong|em)>", re.IGNORECASE)
_ANCHOR_PATTERN = re.compile(r"</?a[^>]*>", re.IGNORECASE)


def apply_caption_style(caption: str | None, style: str | None) -> str | None:
    if not caption:
        return caption

    stripped = _TAG_PATTERN.sub("", caption)

    if not style or style == "normal":
        return stripped
    if style == "bold":
        return f"<b>{stripped}</b>"
    if style == "italic":
        return f"<i>{stripped}</i>"
    if style == "mono":
        # <code> can't contain links, so strip any <a> tags too
        plain = _ANCHOR_PATTERN.sub("", stripped)
        return f"<code>{plain}</code>"
    return stripped
