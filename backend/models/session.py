"""
AppSession model.

Table: app_sessions
Represents a single spell bee game session.
Tracks score, word counts, and session lifecycle.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AppSession:
    id: str
    player_id: str
    status_id: int
    total_words: int
    correct_count: int
    incorrect_count: int
    score: int
    add_date: datetime
    update_date: datetime
    ended_at: Optional[datetime]
