from datetime import datetime, timedelta

from ..clock import normalize_utc


def calculate_deadlines(aware_at: datetime, fix_available_at: datetime | None = None) -> dict[str, datetime | None]:
    aware_at = normalize_utc(aware_at)
    fix_time = normalize_utc(fix_available_at) if fix_available_at else None
    return {
        "early_warning": aware_at + timedelta(hours=24),
        "notification": aware_at + timedelta(hours=72),
        "final_report": fix_time + timedelta(days=14) if fix_time else None,
    }
