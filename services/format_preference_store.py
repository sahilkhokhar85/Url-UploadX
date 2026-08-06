from __future__ import annotations

from pathlib import Path


class FormatPreferenceStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, user_id: int) -> Path:
        return self.root / f"{user_id}.txt"

    def get(self, user_id: int) -> str | None:
        path = self._path(user_id)
        if not path.exists():
            return None
        value = path.read_text().strip()
        return value or None

    def set(self, user_id: int, value: str) -> None:
        self._path(user_id).write_text(value)

    def clear(self, user_id: int) -> None:
        path = self._path(user_id)
        if path.exists():
            path.unlink()
