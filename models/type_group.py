"""
AppTypeGroup model.

Table: app_type_group
Defines groups/categories of type values used across the application.
Each group acts as a namespace for related types (e.g. 'session_status').
IDs are manually assigned to match Python enums.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class AppTypeGroup:
    id: int
    name: str
    description: str
    add_date: datetime
    update_date: datetime
