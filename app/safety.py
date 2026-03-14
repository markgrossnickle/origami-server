import logging
import math
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
    # Anatomical / euphemism patterns
    r"\bpenis\b", r"\bdick\b", r"\bcock\b", r"\bphallic\b", r"\bphallus\b",
    r"\bboob\b", r"\bboobs\b", r"\btits\b", r"\bbreast\b",
    r"\bbutt\s*plug\b", r"\bdildo\b", r"\bvagina\b", r"\banus\b",
    r"\bmiddle\s+finger\b", r"\bflip\w*\s+off\b", r"\bflipping\s+off\b",
    # Shape-based euphemisms people use to bypass filters
    r"\bcylinder\b.*\bballs?\b", r"\bballs?\b.*\bcylinder\b",
    r"\blong\b.*\bshaft\b", r"\bshaft\b.*\bballs?\b",
    r"\btwo\s+balls\b", r"\b2\s+balls\b",
    r"\berect\b", r"\berection\b",
    r"\bpp\b",
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

# Only allow safe characters: letters, spaces, periods, and commas
_safe_chars_re = re.compile(r"^[a-zA-Z\s.,]+$")

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


def _check_phallic_geometry(parts: list[dict]) -> bool:
    """Detect phallic-looking geometry: a tall cylinder/block with balls at or near its base.

    Returns True if the shape is suspicious and should be rejected.
    """
    # Separate parts by shape
    cylinders = []
    balls = []
    blocks = []

    for p in parts:
        shape = p.get("shape", "Block")
        size = p.get("size", [1, 1, 1])
        pos = p.get("position", [0, 0, 0])

        if not isinstance(size, list) or len(size) < 3:
            continue
        if not isinstance(pos, list) or len(pos) < 3:
            continue

        sx, sy, sz = float(size[0]), float(size[1]), float(size[2])
        px, py, pz = float(pos[0]), float(pos[1]), float(pos[2])

        entry = {"sx": sx, "sy": sy, "sz": sz, "px": px, "py": py, "pz": pz}

        if shape == "Cylinder":
            cylinders.append(entry)
        elif shape == "Ball":
            balls.append(entry)
        elif shape == "Block":
            blocks.append(entry)

    # Check: tall vertical cylinder/block + 2 balls near its base
    shafts = []
    for c in cylinders + blocks:
        height = c["sy"]
        width = max(c["sx"], c["sz"])
        # Tall and narrow = shaft-like (height at least 2x the width)
        if height > 2.0 and height / max(width, 0.1) >= 2.0:
            shafts.append(c)

    if not shafts or len(balls) < 2:
        return False

    for shaft in shafts:
        shaft_bottom_y = shaft["py"] - shaft["sy"] / 2
        shaft_cx = shaft["px"]
        shaft_cz = shaft["pz"]

        # Find balls near the bottom of the shaft
        nearby_balls = 0
        for ball in balls:
            # Ball should be near the shaft's bottom Y
            ball_y = ball["py"]
            dy = abs(ball_y - shaft_bottom_y)
            # Ball should be laterally close to the shaft
            dx = abs(ball["px"] - shaft_cx)
            dz = abs(ball["pz"] - shaft_cz)
            lateral_dist = math.sqrt(dx * dx + dz * dz)

            if dy < 2.0 and lateral_dist < 4.0:
                nearby_balls += 1

        if nearby_balls >= 2:
            logger.warning("Phallic geometry detected: tall shaft with %d balls at base", nearby_balls)
            return True

    return False


def _check_middle_finger(parts: list[dict]) -> bool:
    """Detect middle-finger-like geometry: one tall narrow part flanked by shorter parts."""
    tall_parts = []
    short_parts = []

    for p in parts:
        size = p.get("size", [1, 1, 1])
        pos = p.get("position", [0, 0, 0])
        if not isinstance(size, list) or len(size) < 3:
            continue
        if not isinstance(pos, list) or len(pos) < 3:
            continue

        sx, sy, sz = float(size[0]), float(size[1]), float(size[2])
        px, py, pz = float(pos[0]), float(pos[1]), float(pos[2])
        width = max(sx, sz)

        entry = {"sx": sx, "sy": sy, "sz": sz, "px": px, "py": py, "pz": pz, "width": width}

        if sy / max(width, 0.1) >= 3.0 and sy > 2.0:
            tall_parts.append(entry)
        elif sy / max(width, 0.1) >= 1.5 and sy > 1.0:
            short_parts.append(entry)

    if len(tall_parts) != 1 or len(short_parts) < 2:
        return False

    # Check if shorter parts flank the tall one laterally
    tall = tall_parts[0]
    flanking = 0
    for s in short_parts:
        lateral = abs(s["px"] - tall["px"]) + abs(s["pz"] - tall["pz"])
        y_diff = abs(s["py"] - tall["py"])
        if lateral < 4.0 and y_diff < 3.0 and s["sy"] < tall["sy"] * 0.7:
            flanking += 1

    if flanking >= 2:
        logger.warning("Middle-finger-like geometry detected")
        return True

    return False


def _validate_animation_output(result: dict) -> dict | None:
    """Validate animation keyframe output. Returns sanitized result or None if invalid."""
    keyframes = result.get("keyframes")
    if not isinstance(keyframes, list) or len(keyframes) == 0:
        return None

    # Validate duration
    duration = result.get("duration")
    if not isinstance(duration, (int, float)) or duration <= 0:
        result["duration"] = 2.0
    result["duration"] = max(0.5, min(10.0, float(result["duration"])))

    # Validate loop flag
    if not isinstance(result.get("loop"), bool):
        result["loop"] = False

    # Sanitize keyframes
    valid_joints = {
        "Neck", "Waist",
        "RightShoulder", "LeftShoulder", "RightElbow", "LeftElbow",
        "RightWrist", "LeftWrist",
        "RightHip", "LeftHip", "RightKnee", "LeftKnee",
        "RightAnkle", "LeftAnkle", "Root",
    }
    sanitized_kf = []
    for kf in keyframes:
        if not isinstance(kf, dict):
            continue
        time = kf.get("time")
        if not isinstance(time, (int, float)):
            continue
        time = max(0, min(result["duration"], float(time)))

        joints = kf.get("joints")
        if not isinstance(joints, dict):
            continue

        sanitized_joints = {}
        for joint_name, angles in joints.items():
            if joint_name not in valid_joints:
                continue
            if not isinstance(angles, list) or len(angles) < 3:
                continue
            # Clamp angles to -180..180
            sanitized_joints[joint_name] = [
                max(-180, min(180, float(a))) for a in angles[:3]
            ]

        if sanitized_joints:
            sanitized_kf.append({"time": time, "joints": sanitized_joints})

    if not sanitized_kf:
        return None

    result["keyframes"] = sanitized_kf

    # Sanitize name
    name = result.get("name", "")
    if isinstance(name, str):
        result["name"] = re.sub(r"[^a-zA-Z0-9\s\-'.,!?&]", "", name)[:50]

    return result


def validate_output(result: dict) -> dict | None:
    """Validate LLM output. Returns sanitized result or None if invalid."""
    if not isinstance(result, dict):
        return None

    # Animation output has keyframes instead of parts
    if "keyframes" in result and "parts" not in result:
        return _validate_animation_output(result)

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

    # Geometric shape checks — catch inappropriate shapes the LLM generated
    if _check_phallic_geometry(sanitized_parts):
        return None
    if _check_middle_finger(sanitized_parts):
        return None

    # Sanitize name — strip anything weird
    name = result.get("name", "")
    if isinstance(name, str):
        result["name"] = re.sub(r"[^a-zA-Z0-9\s\-'.,!?&]", "", name)[:50]

    return result
