from datetime import datetime, timezone as dt_timezone
from typing import Optional


def from_stripe_timestamp(value: Optional[int]) -> Optional[datetime]:
    if not value:
        return None

    return datetime.fromtimestamp(value, tz=dt_timezone.utc)
