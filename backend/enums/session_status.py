"""SessionStatus enum — maps to app_type.id where group_id = TypeGroup.SESSION_STATUS"""

from enum import IntEnum


class SessionStatus(IntEnum):
    IN_PROGRESS = 1
    COMPLETED = 2
    ABANDONED = 3
