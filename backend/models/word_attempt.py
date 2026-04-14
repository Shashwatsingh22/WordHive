"""
AppWordAttempt model.

Table: app_word_attempts
Records each individual word spelling attempt within a game session.
Captures the word given by the bot, what the user spelled, and the result.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AppWordAttempt:
    id: str
    session_id: str
    word: str
    user_spelling: Optional[str]
    is_correct: Optional[bool]
    attempt_number: int
    add_date: datetime
