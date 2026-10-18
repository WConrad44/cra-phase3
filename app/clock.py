from datetime import datetime, timezone
from threading import Lock

_lock = Lock()
_fixed_now: datetime | None = None


def normalize_utc(value: datetime) -> datetime:
    # Database drivers such as SQLite may return stored UTC timestamps without tzinfo.
    # User-facing schemas separately reject naive timestamps; internally, naive values are UTC.
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0)


def now() -> datetime:
    with _lock:
        if _fixed_now is not None:
            return _fixed_now
    return datetime.now(timezone.utc).replace(microsecond=0)


def set_fixed(value: datetime) -> datetime:
    global _fixed_now
    value = normalize_utc(value)
    with _lock:
        _fixed_now = value
    return value


def clear_fixed() -> None:
    global _fixed_now
    with _lock:
        _fixed_now = None


def get_fixed() -> datetime | None:
    with _lock:
        return _fixed_now
