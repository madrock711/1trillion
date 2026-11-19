"""Regular KRX session times and confirmed date-specific exceptions."""

from datetime import time
from typing import NamedTuple


class SessionHours(NamedTuple):
    open: time
    auction: time
    close: time


DEFAULT_HOURS = SessionHours(time(9), time(15, 20), time(15, 30))
SESSION_OVERRIDES = {
    # KRX temporary CSAT schedule: KIND notice 20261105000216.
    "2026-11-19": SessionHours(time(10), time(16, 20), time(16, 30)),
}


def krx_session_hours(date: str) -> SessionHours:
    return SESSION_OVERRIDES.get(date, DEFAULT_HOURS)
