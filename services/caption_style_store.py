from __future__ import annotations

import asyncpg


class CaptionStyleStore:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def init(self) -> None:
        await self.pool.execute(
            """
            CREATE TABLE IF NOT EXISTS caption_styles (
                user_id BIGINT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

    async def get(self, user_id: int) -> str | None:
        value = await self.pool.fetchval(
            """
            SELECT value
            FROM caption_styles
            WHERE user_id = $1
            """,
            user_id,
        )
        return value or None

    async def set(self, user_id: int, value: str) -> None:
        await self.pool.execute(
            """
            INSERT INTO caption_styles (user_id, value)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET value = EXCLUDED.value
            """,
            user_id,
            value,
        )
