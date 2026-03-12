import logging
import re

logger = logging.getLogger(__name__)

# Words/patterns that should be rejected before hitting the LLM
BLOCKED_PATTERNS = [
    r"\bgun\b", r"\brifle\b", r"\bpistol\b", r"\bshotgun\b",
    r"\bknife\b", r"\bsword\b", r"\bdagger\b", r"\bweapon\b",
    r"\bbomb\b", r"\bgrenade\b", r"\bexplosive\b", r"\bmissile\b",
    r"\bkill\b", r"\bdeath\b", r"\bdead\b", r"\bblood\b", r"\bgore\b",
    r"\bnude\b", r"\bnaked\b", r"\bsexy\b", r"\bnsfw\b",
    r"\bdrug\b", r"\bcocaine\b", r"\bheroin\b", r"\bweed\b",
    r"\bhitler\b", r"\bnazi\b", r"\bterrorist\b",
]

_blocked_re = re.compile("|".join(BLOCKED_PATTERNS), re.IGNORECASE)

# Max input length
MAX_INPUT_LENGTH = 100


def validate_input(prompt: str) -> str | None:
    """Validate and sanitize user input.

    Returns None if input is safe, or an error message if blocked.
    """
    if not prompt or not prompt.strip():
        return "empty_input"

    prompt = prompt.strip()

    if len(prompt) > MAX_INPUT_LENGTH:
        return "input_too_long"

    if _blocked_re.search(prompt):
        return "blocked_content"

    # Check for non-printable or suspicious characters
    if not all(c.isprintable() or c.isspace() for c in prompt):
        return "invalid_characters"

    return None
