"""
AttemptService — handles recording word spelling attempts.

Uses sql/attempt_queries.sql for all DB operations.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from config.database import get_connection, load_query
from models.word_attempt import AppWordAttempt


class AttemptService:

    async def record_attempt(self, session_id: str, word: str,
                             user_spelling: Optional[str],
                             is_correct: Optional[bool],
                             attempt_number: int) -> AppWordAttempt:
        attempt_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        query = load_query("attempt_queries.sql", "create_attempt")
        conn = await get_connection()
        try:
            await conn.execute(query, {
                "id": attempt_id,
                "session_id": session_id,
                "word": word,
                "user_spelling": user_spelling,
                "is_correct": is_correct,
                "attempt_number": attempt_number,
                "add_date": now,
            })
            await conn.commit()
        finally:
            await conn.close()

        return AppWordAttempt(
            id=attempt_id,
            session_id=session_id,
            word=word,
            user_spelling=user_spelling,
            is_correct=is_correct,
            attempt_number=attempt_number,
            add_date=now,
        )

    async def get_attempts(self, session_id: str) -> List[AppWordAttempt]:
        query = load_query("attempt_queries.sql", "get_attempts_by_session")
        conn = await get_connection()
        try:
            cursor = await conn.execute(query, {"session_id": session_id})
            rows = await cursor.fetchall()
            return [
                AppWordAttempt(
                    id=row["id"],
                    session_id=row["session_id"],
                    word=row["word"],
                    user_spelling=row["user_spelling"],
                    is_correct=row["is_correct"],
                    attempt_number=row["attempt_number"],
                    add_date=row["add_date"],
                )
                for row in rows
            ]
        finally:
            await conn.close()
