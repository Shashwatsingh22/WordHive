"""
In-memory game state tracker for active Pipecat sessions.

Tracks live game data that gets pushed to the frontend via Daily app messages.
Persisted to DB when the session ends.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from config.constants import SCORE_PER_CORRECT


@dataclass
class ActiveGame:
    session_id: str
    player_id: str
    player_name: str
    current_word: Optional[str] = None
    score: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    total_words: int = 0
    words_used: List[str] = field(default_factory=list)

    def record_attempt(self, word: str, is_correct: bool):
        self.total_words += 1
        if is_correct:
            self.correct_count += 1
            self.score += SCORE_PER_CORRECT
        else:
            self.incorrect_count += 1
        self.words_used.append(word)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "player_name": self.player_name,
            "score": self.score,
            "correct_count": self.correct_count,
            "incorrect_count": self.incorrect_count,
            "total_words": self.total_words,
            "current_word": self.current_word,
        }


active_games: Dict[str, ActiveGame] = {}
