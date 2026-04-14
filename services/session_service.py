"""
SessionService — handles game session lifecycle.

Uses sql/session_queries.sql for all DB operations.
"""

import uuid
from datetime import datetime, timezone

from config.database import get_connection, load_query
from enums import SessionStatus
from models.session import AppSession


class SessionService:

    async def create_session(self, player_id: str) -> AppSession:
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        query = load_query("session_queries.sql", "create_session")
        conn = await get_connection()
        try:
            await conn.execute(query, {
                "id": session_id,
                "player_id": player_id,
                "status_id": SessionStatus.IN_PROGRESS,
                "add_date": now,
                "update_date": now,
            })
            await conn.commit()
        finally:
            await conn.close()

        return AppSession(
            id=session_id,
            player_id=player_id,
            status_id=SessionStatus.IN_PROGRESS,
            total_words=0,
            correct_count=0,
            incorrect_count=0,
            score=0,
            add_date=now,
            update_date=now,
            ended_at=None,
        )

    async def get_session(self, session_id: str):
        query = load_query("session_queries.sql", "get_session_by_id")
        conn = await get_connection()
        try:
            cursor = await conn.execute(query, {"id": session_id})
            row = await cursor.fetchone()
            if not row:
                return None
            return AppSession(
                id=row["id"],
                player_id=row["player_id"],
                status_id=row["status_id"],
                total_words=row["total_words"],
                correct_count=row["correct_count"],
                incorrect_count=row["incorrect_count"],
                score=row["score"],
                add_date=row["add_date"],
                update_date=row["update_date"],
                ended_at=row["ended_at"],
            )
        finally:
            await conn.close()

    async def update_score(self, session_id: str, total_words: int,
                           correct: int, incorrect: int, score: int):
        now = datetime.now(timezone.utc).isoformat()
        query = load_query("session_queries.sql", "update_session_score")
        conn = await get_connection()
        try:
            await conn.execute(query, {
                "id": session_id,
                "total_words": total_words,
                "correct_count": correct,
                "incorrect_count": incorrect,
                "score": score,
                "update_date": now,
            })
            await conn.commit()
        finally:
            await conn.close()

    async def end_session(self, session_id: str, status_id: int):
        now = datetime.now(timezone.utc).isoformat()
        query = load_query("session_queries.sql", "end_session")
        conn = await get_connection()
        try:
            await conn.execute(query, {
                "id": session_id,
                "status_id": status_id,
                "ended_at": now,
                "update_date": now,
            })
            await conn.commit()
        finally:
            await conn.close()

    async def get_leaderboard(self) -> list:
        query = load_query("session_queries.sql", "get_leaderboard")
        conn = await get_connection()
        try:
            cursor = await conn.execute(query, {
                "completed_status_id": SessionStatus.COMPLETED,
            })
            rows = await cursor.fetchall()
            return [
                {
                    "player_name": row["player_name"],
                    "score": row["score"],
                    "correct": row["correct_count"],
                    "total": row["total_words"],
                    "date": row["add_date"],
                }
                for row in rows
            ]
        finally:
            await conn.close()
