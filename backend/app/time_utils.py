from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return UTC now as a naive datetime for the existing database columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
