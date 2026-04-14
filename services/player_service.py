"""
PlayerService — handles player creation and lookup.

Uses sql/player_queries.sql for all DB operations.
"""

import uuid
from datetime import datetime, timezone

from config.database import get_connection, load_query
from models.player import AppPlayer


class PlayerService:

    async def create_player(self, name: str) -> AppPlayer:
        player_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        query = load_query("player_queries.sql", "create_player")
        conn = await get_connection()
        try:
            await conn.execute(query, {
                "id": player_id,
                "name": name,
                "add_date": now,
                "update_date": now,
            })
            await conn.commit()
        finally:
            await conn.close()

        return AppPlayer(
            id=player_id,
            name=name,
            add_date=now,
            update_date=now,
        )

    async def get_player(self, player_id: str):
        query = load_query("player_queries.sql", "get_player_by_id")
        conn = await get_connection()
        try:
            cursor = await conn.execute(query, {"id": player_id})
            row = await cursor.fetchone()
            if not row:
                return None
            return AppPlayer(
                id=row["id"],
                name=row["name"],
                add_date=row["add_date"],
                update_date=row["update_date"],
            )
        finally:
            await conn.close()
