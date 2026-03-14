import json
import logging

import httpx

from app.config import (
    ANTHROPIC_API_KEY,
    CATEGORY_PROMPTS,
    GOOGLE_API_KEY,
    MAX_TOKENS,
    MODELS,
    OPENAI_API_KEY,
    STYLE_PROMPTS,
)
from app.safety import validate_output

logger = logging.getLogger(__name__)

# Lazy-loaded clients — only created on first use to save memory
_anthropic_client = None
_openai_client = None
_http_client = None  # Shared httpx client for Google Gemini REST API


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    return _anthropic_client


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        import openai
        _openai_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


def _get_http_client():
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=60.0)
    return _http_client
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
- Creatures/animals: orient naturally for the species (8-12 studs in longest dimension)
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
  "attributes": {},
  "description": "A fierce dragon with angular wings"
}

"attributes" is an optional dict of key-value behavior/physics hints. See category guidance for what attributes to set for each category. Omit or leave empty if no special behavior is needed.

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


def _user_message(prompt: str, category: str | None = None) -> str:
    if category == "animation":
        return f"Create a keyframe animation for: {prompt}"
    return f"Create an origami model of: {prompt}"


async def _call_anthropic(prompt: str, model_id: str, system: str, category: str | None = None) -> dict:
    """Call Anthropic Claude API and parse JSON response."""
    import anthropic

    client = _get_anthropic_client()
    message = await client.messages.create(
        model=model_id,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": _user_message(prompt, category)}],
    )

    if message.stop_reason == "max_tokens":
        logger.warning("Response truncated at max_tokens (%s) for model %s", MAX_TOKENS, model_id)

    text = message.content[0].text.strip()
    return _extract_json(text)


async def _call_openai(prompt: str, model_id: str, system: str, category: str | None = None) -> dict:
    """Call OpenAI API and parse JSON response."""
    client = _get_openai_client()
    response = await client.chat.completions.create(
        model=model_id,
        max_tokens=MAX_TOKENS,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": _user_message(prompt, category)},
        ],
    )

    text = response.choices[0].message.content.strip()
    return _extract_json(text)


async def _call_google(prompt: str, model_id: str, system: str, category: str | None = None) -> dict:
    """Call Google Gemini REST API directly (no SDK — saves ~120MB RAM)."""
    client = _get_http_client()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"

    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": _user_message(prompt, category)}]}],
        "generationConfig": {"maxOutputTokens": MAX_TOKENS},
    }

    response = await client.post(url, params={"key": GOOGLE_API_KEY}, json=payload)
    response.raise_for_status()
    data = response.json()

    # Extract text from Gemini response
    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini returned no candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        raise ValueError("Gemini returned empty parts")

    text = parts[0].get("text", "").strip()
    return _extract_json(text)


async def _call_llm(prompt: str, provider: str, model_id: str, system: str, category: str | None = None) -> dict:
    """Route to the correct provider and parse JSON response."""
    if provider == "anthropic":
        return await _call_anthropic(prompt, model_id, system, category)
    elif provider == "openai":
        return await _call_openai(prompt, model_id, system, category)
    elif provider == "google":
        return await _call_google(prompt, model_id, system, category)
    else:
        raise ValueError(f"Unknown provider: {provider}")


async def generate_model(
    prompt: str,
    category: str | None = None,
    style: str = "origami",
    raw: bool = False,
    model: str = "haiku",
) -> dict:
    """Generate an origami model description from a text prompt."""
    system = _build_system_prompt(category, raw, style)

    entry = MODELS.get(model)
    if not entry:
        return {"error": "invalid_model"}
    provider, primary, fallback = entry
    models_to_try = [primary] if fallback is None else [primary, fallback]

    for attempt, model_id in enumerate(models_to_try):
        try:
            result = await _call_llm(prompt, provider, model_id, system, category=category)

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
        except Exception as e:
            # Check if it's a known API error from any provider
            err_type = type(e).__name__
            if "APIError" in err_type or "HTTPStatusError" in err_type:
                if attempt == 0 and len(models_to_try) > 1:
                    logger.warning("%s API error (%s), falling back", model_id, e)
                    continue
                logger.warning("Model %s API error: %s", model_id, e)
                return {"error": "api_error"}
            logger.exception("Unexpected error in generate_model")
            return {"error": "internal_error"}

    return {"error": "generation_failed"}
