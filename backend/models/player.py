"""
AppPlayer model.

Table: app_players
Stores players who have participated in the spell bee game.
One player can have multiple game sessions.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AppPlayer:
    id: str
    name: str
    add_date: datetime
    update_date: datetime
