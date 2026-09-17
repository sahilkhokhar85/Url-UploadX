from __future__ import annotations

import asyncpg


class FormatPreferenceStore:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    async def init(self) -> None:
        await self.pool.execute(
            """
            CREATE TABLE IF NOT EXISTS format_preferences (
                user_id BIGINT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

    async def get(self, user_id: int) -> str | None:
        value = await self.pool.fetchval(
            """
            SELECT value
            FROM format_preferences
            WHERE user_id = $1
            """,
            user_id,
        )
        return value or None

    async def set(self, user_id: int, value: str) -> None:
        await self.pool.execute(
            """
            INSERT INTO format_preferences (user_id, value)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO UPDATE SET value = EXCLUDED.value
            """,
            user_id,
            value,
        )

    async def clear(self, user_id: int) -> None:
        await self.pool.execute(
            """
            DELETE FROM format_preferences
            WHERE user_id = $1
            """,
            user_id,
        )
