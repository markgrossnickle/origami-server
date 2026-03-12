import json
import logging

import anthropic

from app.config import ANTHROPIC_API_KEY, CATEGORY_PROMPTS, FALLBACK_MODEL, MAX_TOKENS, MODEL, MODELS, SCENE_PLANNER_PROMPT, STYLE_PROMPTS
from app.safety import validate_output

logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a 3D model generator for a Roblox game. Given a subject, return a JSON object describing how to build it from Roblox Parts.

RULES:
- The "name" field should be the subject itself (e.g. "Dragon", "Sports Car")
- Use 15-40 parts maximum
- Each part has: shape (Block/Ball/Cylinder/Wedge), position [x,y,z], size [x,y,z], rotation [x,y,z] (degrees), color [r,g,b] (0-255), material, transparency (0-1, default 0), body_part (optional, for avatars only)
- Available materials: SmoothPlastic, Neon, Foil, Glass, Metal, Fabric, Wood, Concrete, Brick, Marble, Ice
- Position is relative to model center at [0,0,0], ground is y=0
- NEVER place two parts at the exact same position — offset by at least 0.2 studs
- Return ONLY valid JSON, no explanation

CONSTRUCTION:
- Choose shapes and arrangement that best represent the subject naturally
- Use the right shape for the job: Blocks for flat/boxy forms, Balls for round/organic, Cylinders for tubes/limbs, Wedges for angular/pointed features
- Add 2-3 small detail parts for character (eyes, horns, whiskers, spots, antennae)

ORIENTATION AND SCALE:
- Creatures/animals: horizontal and low (2-4 studs tall, 8-12 studs long)
- Buildings: vertical (15-20 studs tall)
- Vehicles: horizontal (6-8 tall, 12-16 long)
- Props/tools: compact (2-8 studs)

Response format:
{
  "name": "Dragon",
  "category": "creature",
  "parts": [
    {
      "name": "seg_1",
      "shape": "Block",
      "position": [0, 2, 0],
      "size": [1.5, 1.2, 1.5],
      "rotation": [0, 0, 0],
      "color": [80, 200, 80],
      "material": "SmoothPlastic",
      "transparency": 0
    }
  ],
  "animation": "idle_bob",
  "locomotion": "fly",
  "description": "A fierce dragon with angular wings"
}

Available animations: idle_bob, spin_slow, bounce, wobble, flutter, breathe, none
Available categories: creature, avatar, vehicle, building, tool, hat, prop

PART NAMING — the game animates parts based on their name prefix:
- Body segments: seg_1, seg_2, seg_3... (body fold animation)
- Wings: wing_L_1, wing_R_1 (flapping animation)
- Tail: tail_1, tail_2 (swaying animation)
- Jaw: jaw_lower (open/close animation)
- Legs: leg_FL_1, leg_FR_1, leg_BL_1, leg_BR_1 (walking cycle)
- Eyes/details: eye_L, eye_R, horn_1 (no animation, attached to body)
Use these prefixes so the game can animate the model correctly.

LOCOMOTION (required for creatures):
- "walk" — four-legged or bipedal ground walker (dogs, horses, dinosaurs)
- "slither" — legless ground crawler (worms, snakes, caterpillars)
- "fly" — winged flyer (birds, dragons, butterflies)
- "float" — drifting/hovering (ghosts, jellyfish, spirits)
- "hop" — jumping movement (frogs, rabbits, kangaroos)
- "stationary" — doesn't move (corals, plants, mushroom creatures)
Choose the locomotion that best matches how this creature would naturally move.

SHAPE SAFETY:
- This is a children's game. Consider what the FINAL 3D SHAPE looks like.
- NEVER generate shapes that resemble genitalia, middle fingers, or other inappropriate body parts.
- If a prompt asks for a shape combination that would look phallic (e.g. a tall cylinder with spheres at the base), refuse with {"error": "unsafe"}.
- If the prompt is clearly trying to trick you into making something inappropriate, refuse.

Generate child-friendly content. Fantasy creatures (skeletons, zombies, ghosts, dragons, monsters) are fine — this is a game! Only refuse explicit gore, nudity, hate symbols, drug references, or shapes resembling genitalia/obscene gestures — return {"error": "unsafe"} for those."""


def _build_system_prompt(category: str | None, raw: bool, style: str = "origami") -> str:
    """Build the system prompt, layering style and category guidance."""
    if raw:
        return SYSTEM_PROMPT

    parts = [SYSTEM_PROMPT]

    # Layer 1: Style override (replaces construction aesthetics)
    if style and style in STYLE_PROMPTS:
        parts.append(f"\n\n{STYLE_PROMPTS[style]}")

    # Layer 2: Category guidance (type-specific structure)
    if category and category in CATEGORY_PROMPTS:
        guidance = CATEGORY_PROMPTS[category]
        parts.append(f"\n\nCategory guidance for this request ({category}): {guidance}")
    else:
        parts.append('\n\nAuto-detect the best category from the prompt and set the "category" field accordingly.')

    return "".join(parts)


def _extract_json(text: str) -> dict:
    """Extract JSON object from LLM response, handling extra text or code blocks."""
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code blocks
    if "```" in text:
        # Find content between first ``` and last ```
        start = text.index("```")
        end = text.rindex("```")
        if start != end:
            inner = text[start:end]
            # Remove the opening ```json or ```
            inner = inner.split("\n", 1)[1] if "\n" in inner else inner[3:]
            try:
                return json.loads(inner.strip())
            except json.JSONDecodeError:
                pass

    # Find outermost { ... } braces
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("No valid JSON found in response", text, 0)


async def _call_llm(prompt: str, model: str, system: str) -> dict:
    """Make one LLM call and parse the JSON response. Raises on failure."""
    message = await client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": f"Create an origami model of: {prompt}"}],
    )

    if message.stop_reason == "max_tokens":
        logger.warning("Response truncated at max_tokens (%s) for model %s", MAX_TOKENS, model)

    text = message.content[0].text.strip()
    return _extract_json(text)


async def generate_model(
    prompt: str,
    category: str | None = None,
    style: str = "origami",
    raw: bool = False,
    model: str = "haiku",
) -> dict:
    """Generate an origami model description from a text prompt."""
    system = _build_system_prompt(category, raw, style)

    primary, fallback = MODELS.get(model, (MODEL, FALLBACK_MODEL))
    models_to_try = [primary] if fallback is None else [primary, fallback]

    for attempt, model_id in enumerate(models_to_try):
        try:
            result = await _call_llm(prompt, model_id, system)

            if "error" in result:
                return {"error": result["error"]}

            # Validate and sanitize LLM output
            result = validate_output(result)
            if result is None:
                if attempt == 0 and len(models_to_try) > 1:
                    logger.warning("%s output failed validation, falling back", model_id)
                    continue
                return {"error": "generation_failed"}

            # Add metadata
            result["model_used"] = model_id
            if category:
                result["category_hint"] = category
            else:
                result["category_hint"] = result.get("category", "unknown")

            return result

        except json.JSONDecodeError as e:
            if attempt == 0 and len(models_to_try) > 1:
                logger.warning("%s returned invalid JSON, falling back. Raw: %s", model_id, e.doc[:500] if e.doc else "empty")
                continue
            logger.warning("Model %s returned invalid JSON. Raw: %s", model_id, e.doc[:500] if e.doc else "empty")
            return {"error": "generation_failed"}
        except anthropic.APIError as e:
            if attempt == 0 and len(models_to_try) > 1:
                logger.warning("%s API error (%s), falling back", model_id, e)
                continue
            logger.warning("Model %s API error: %s", model_id, e)
            return {"error": "api_error"}
        except Exception:
            logger.exception("Unexpected error in generate_model")
            return {"error": "internal_error"}

    return {"error": "generation_failed"}


def _validate_scene_plan(result: dict) -> dict | None:
    """Validate the scene planner output. Returns sanitized result or None if invalid."""
    if not isinstance(result, dict):
        return None

    name = result.get("name")
    if not isinstance(name, str) or not name.strip():
        result["name"] = "Scene"

    items = result.get("items")
    if not isinstance(items, list) or len(items) == 0:
        return None

    # Cap at 15 items
    if len(items) > 15:
        items = items[:15]

    valid_categories = {"creature", "building", "prop", "vehicle"}
    sanitized = []

    for item in items:
        if not isinstance(item, dict):
            continue

        desc = item.get("description")
        if not isinstance(desc, str) or not desc.strip():
            continue

        cat = item.get("category", "prop")
        if cat not in valid_categories:
            cat = "prop"

        pos = item.get("position", [0, 0, 0])
        if not isinstance(pos, list) or len(pos) < 3:
            pos = [0, 0, 0]
        # Clamp positions to within scene radius
        pos = [max(-60, min(60, float(p))) for p in pos[:3]]

        rotation = item.get("rotation_y", 0)
        if not isinstance(rotation, (int, float)):
            rotation = 0
        rotation = float(rotation) % 360

        entry = {
            "description": desc.strip()[:100],
            "category": cat,
            "position": pos,
            "rotation_y": rotation,
        }

        # Only creatures can be enemies
        if cat == "creature":
            entry["enemy"] = bool(item.get("enemy", False))

        sanitized.append(entry)

    if not sanitized:
        return None

    result["items"] = sanitized
    return result


async def generate_scene(
    prompt: str,
    model: str = "sonnet",
) -> dict:
    """Generate a scene plan from a world/environment description."""
    primary, fallback = MODELS.get(model, (MODEL, FALLBACK_MODEL))
    models_to_try = [primary] if fallback is None else [primary, fallback]

    for attempt, model_id in enumerate(models_to_try):
        try:
            message = await client.messages.create(
                model=model_id,
                max_tokens=MAX_TOKENS,
                system=SCENE_PLANNER_PROMPT,
                messages=[{"role": "user", "content": f"Plan a scene: {prompt}"}],
            )

            if message.stop_reason == "max_tokens":
                logger.warning("Scene plan truncated at max_tokens for model %s", model_id)

            text = message.content[0].text.strip()
            result = _extract_json(text)

            if "error" in result:
                return {"error": result["error"]}

            result = _validate_scene_plan(result)
            if result is None:
                if attempt == 0 and len(models_to_try) > 1:
                    logger.warning("%s scene plan failed validation, falling back", model_id)
                    continue
                return {"error": "scene_planning_failed"}

            result["model_used"] = model_id
            return result

        except json.JSONDecodeError as e:
            if attempt == 0 and len(models_to_try) > 1:
                logger.warning(
                    "%s returned invalid scene JSON, falling back. Raw: %s",
                    model_id,
                    e.doc[:500] if e.doc else "empty",
                )
                continue
            logger.warning("Model %s returned invalid scene JSON", model_id)
            return {"error": "scene_planning_failed"}
        except anthropic.APIError as e:
            if attempt == 0 and len(models_to_try) > 1:
                logger.warning("%s API error during scene planning (%s), falling back", model_id, e)
                continue
            logger.warning("Model %s API error during scene planning: %s", model_id, e)
            return {"error": "api_error"}
        except Exception:
            logger.exception("Unexpected error in generate_scene")
            return {"error": "internal_error"}

    return {"error": "scene_planning_failed"}
