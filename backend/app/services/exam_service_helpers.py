from datetime import datetime, timedelta, timezone


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def expiry_from(started_at: datetime, duration_seconds: int) -> datetime:
    return started_at + timedelta(seconds=duration_seconds)
