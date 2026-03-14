import time
from collections import defaultdict

from app.config import (
    RATE_LIMIT_BURST_SECONDS,
    RATE_LIMIT_HOURLY,
)

# Per-player tracking: {player_id: list of timestamps}
_request_log: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(player_id: str) -> str | None:
    """Check rate limits for a player.

    Returns None if allowed, or an error string with cooldown info if blocked.
    """
    now = time.time()

    log = _request_log[player_id]
    _request_log[player_id] = log = [t for t in log if now - t < 3600]
    burst = RATE_LIMIT_BURST_SECONDS
    hourly = RATE_LIMIT_HOURLY

    # Check burst limit (1 per N seconds)
    if log and (now - log[-1]) < burst:
        cooldown = burst - (now - log[-1])
        return f"rate_limited: wait {cooldown:.1f}s"

    # Check hourly limit
    if len(log) >= hourly:
        oldest = log[0]
        cooldown = 3600 - (now - oldest)
        return f"rate_limited: hourly limit reached, resets in {cooldown:.0f}s"

    # Record this request
    log.append(now)
    return None
