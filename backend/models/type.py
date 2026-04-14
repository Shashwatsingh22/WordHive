"""
AppType model.

Table: app_type
Stores individual type values belonging to a type group.
Used as a lookup/reference table for statuses and categories.
IDs are manually assigned to match Python enums.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AppType:
    id: int
    group_id: int
    name: str
    description: str
    add_date: datetime
    update_date: datetime
