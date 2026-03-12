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

# Prompt injection patterns — attempts to override the system prompt
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)",
    r"disregard\s+(all\s+)?(previous|prior|above)",
    r"forget\s+(all\s+)?(previous|prior|above)",
    r"new\s+instructions",
    r"system\s*prompt",
    r"you\s+are\s+(now|a)\b",
    r"act\s+as\b",
    r"pretend\s+(to|you)",
    r"instead\s*,?\s*(return|output|give|respond)",
    r"do\s+not\s+follow",
    r"override",
    r"\brole\s*:",
    r"\bassistant\s*:",
    r"\bsystem\s*:",
    r"\buser\s*:",
    r"```",
    r"\{.*\"parts\"",
    r"\{.*\"error\"",
    r"return\s+json",
    r"output\s+json",
    r"<\w+>",  # HTML/XML tags
]

_blocked_re = re.compile("|".join(BLOCKED_PATTERNS), re.IGNORECASE)
_injection_re = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)

# Only allow safe characters: letters, numbers, spaces, and basic punctuation
_safe_chars_re = re.compile(r"^[a-zA-Z0-9\s\-'.,!?&]+$")

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

    # Only allow safe characters
    if not _safe_chars_re.match(prompt):
        return "invalid_characters"

    if _blocked_re.search(prompt):
        return "blocked_content"

    if _injection_re.search(prompt):
        logger.warning("Prompt injection attempt blocked: %s", prompt)
        return "blocked_content"

    return None


VALID_SHAPES = {"Block", "Ball", "Cylinder", "Wedge"}
VALID_MATERIALS = {"SmoothPlastic", "Neon", "Glass", "Metal", "Wood", "Foil",
                   "Concrete", "Brick", "Marble", "Granite", "Fabric", "Ice",
                   "Sand", "Grass"}


def validate_output(result: dict) -> dict | None:
    """Validate LLM output. Returns sanitized result or None if invalid."""
    if not isinstance(result, dict):
        return None

    # Must have parts list
    parts = result.get("parts")
    if not isinstance(parts, list) or len(parts) == 0:
        return None

    # Cap at 50 parts
    if len(parts) > 50:
        parts = parts[:50]
        result["parts"] = parts

    sanitized_parts = []
    for part in parts:
        if not isinstance(part, dict):
            continue

        # Validate shape
        shape = part.get("shape", "Block")
        if shape not in VALID_SHAPES:
            part["shape"] = "Block"

        # Validate material
        material = part.get("material", "SmoothPlastic")
        if material not in VALID_MATERIALS:
            part["material"] = "SmoothPlastic"

        # Clamp color values to 0-255
        color = part.get("color")
        if isinstance(color, list) and len(color) >= 3:
            part["color"] = [max(0, min(255, int(c))) for c in color[:3]]

        # Clamp size to reasonable bounds (0.1 to 50 studs)
        size = part.get("size")
        if isinstance(size, list) and len(size) >= 3:
            part["size"] = [max(0.1, min(50, float(s))) for s in size[:3]]

        # Clamp position to reasonable bounds (-100 to 100)
        pos = part.get("position")
        if isinstance(pos, list) and len(pos) >= 3:
            part["position"] = [max(-100, min(100, float(p))) for p in pos[:3]]

        # Clamp transparency to 0-1
        transparency = part.get("transparency")
        if transparency is not None:
            part["transparency"] = max(0, min(1, float(transparency)))

        sanitized_parts.append(part)

    if not sanitized_parts:
        return None

    result["parts"] = sanitized_parts

    # Sanitize name — strip anything weird
    name = result.get("name", "")
    if isinstance(name, str):
        result["name"] = re.sub(r"[^a-zA-Z0-9\s\-'.,!?&]", "", name)[:50]

    return result
