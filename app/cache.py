import logging
import time
from collections import OrderedDict

logger = logging.getLogger(__name__)

# Simple in-memory LRU cache
MAX_CACHE_SIZE = 500
CACHE_TTL = 3600  # 1 hour

_cache: OrderedDict[str, tuple[dict, float]] = OrderedDict()


def normalize_key(prompt: str) -> str:
    """Normalize prompt for cache lookup."""
    return prompt.strip().lower()


def get_cached(prompt: str) -> dict | None:
    """Get a cached model if available and not expired."""
    key = normalize_key(prompt)
    if key in _cache:
        result, timestamp = _cache[key]
        if time.time() - timestamp < CACHE_TTL:
            _cache.move_to_end(key)
            logger.info("Cache hit: %s", key)
            return result
        else:
            del _cache[key]
    return None


def set_cached(prompt: str, result: dict) -> None:
    """Cache a generated model."""
    if "error" in result:
        return  # Don't cache errors

    key = normalize_key(prompt)
    _cache[key] = (result, time.time())

    # Evict oldest if over limit
    while len(_cache) > MAX_CACHE_SIZE:
        _cache.popitem(last=False)

    logger.info("Cached: %s (total: %d)", key, len(_cache))
