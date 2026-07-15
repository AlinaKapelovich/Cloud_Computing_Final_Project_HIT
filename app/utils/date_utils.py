"""Date helpers.

We deliberately store a patient's birth date (not a frozen age) and calculate the
age on demand, so the value never becomes stale.
"""
from datetime import date, datetime, timezone


def parse_date(value):
    """Parse an ISO date string (YYYY-MM-DD) into a date, or return None."""
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def calculate_age(birth_date):
    """Return an integer age in years from a birth date (date or ISO string)."""
    birth = parse_date(birth_date)
    if birth is None:
        return None
    today = date.today()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def now_utc():
    """Timezone-naive UTC timestamp used for created_at/updated_at fields.

    `datetime.utcnow()` is deprecated, so we build the same naive-UTC value from a
    timezone-aware "now" and drop the tzinfo — keeping stored timestamps unchanged.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
