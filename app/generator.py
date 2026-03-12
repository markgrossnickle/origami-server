import json
import logging

import anthropic

from app.config import ANTHROPIC_API_KEY, CATEGORY_PROMPTS, FALLBACK_MODEL, MAX_TOKENS, MODEL

logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are an origami model generator for a Roblox game. Given a subject, return a JSON object describing how to build it from Roblox Parts in an origami/paper-craft style.

Rules:
- Use 15-40 parts maximum
- Each part has: shape (Block/Ball/Cylinder/Wedge/Corner), position [x,y,z], size [x,y,z], rotation [x,y,z] (degrees), color [r,g,b] (0-255), material (SmoothPlastic/Neon/Foil/Glass)
- Position is relative to model center at [0,0,0], ground is y=0
- Keep models roughly 8-12 studs tall
- Return ONLY valid JSON, no explanation

Style — IMPORTANT, follow this closely:
- Think like folded paper: use angled Wedge parts for folds, creases, and tapered shapes
- Prefer flat, geometric surfaces over smooth curves — use Blocks and Wedges, not Balls (unless eyes or small accents)
- Rotate parts at angles (15°, 30°, 45°) to suggest paper folds rather than keeping everything axis-aligned
- Use subtle color variation within the same hue family (e.g. light blue body, slightly darker blue wings) — not uniform flat color
- Material should be SmoothPlastic for most parts (looks like paper), Foil for metallic accents, Neon sparingly for glowing details
- NEVER place two parts at the exact same position or let faces overlap — this causes visual flickering. Offset detail parts by at least 0.1 studs from the surface they sit on
- Leave small gaps between parts to suggest separate paper folds rather than a solid mass
- Prefer asymmetric, characterful poses over rigid symmetry — slight head tilt, one arm up, tail curving
- Add small detail parts: eyes, nostrils, claws, buttons, antennae — these make the model read well from a distance

Response format:
{
  "name": "Dragon",
  "category": "creature",
  "parts": [
    {
      "name": "body",
      "shape": "Block",
      "position": [0, 4, 0],
      "size": [3, 4, 5],
      "rotation": [0, 0, 0],
      "color": [80, 200, 80],
      "material": "SmoothPlastic"
    }
  ],
  "animation": "idle_bob",
  "description": "A fierce origami dragon with angular wings"
}

Available animations: idle_bob, spin_slow, bounce, wobble, flutter, breathe, none
Available categories: creature, avatar, vehicle, building, tool, prop

Only generate safe, child-friendly objects. Refuse weapons, gore, inappropriate content — return {"error": "unsafe"} instead."""


def _build_system_prompt(category: str | None, raw: bool) -> str:
    """Build the system prompt, optionally adding category-specific guidance."""
    if raw:
        return SYSTEM_PROMPT

    if category and category in CATEGORY_PROMPTS:
        guidance = CATEGORY_PROMPTS[category]
        return f"{SYSTEM_PROMPT}\n\nCategory guidance for this request ({category}): {guidance}"

    # No category — tell the LLM to auto-detect
    return f"{SYSTEM_PROMPT}\n\nAuto-detect the best category from the prompt and set the \"category\" field accordingly."


async def _call_llm(prompt: str, model: str, system: str) -> dict:
    """Make one LLM call and parse the JSON response. Raises on failure."""
    message = await client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": f"Create an origami model of: {prompt}"}],
    )

    text = message.content[0].text.strip()

    # Extract JSON from response (handle markdown code blocks)
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(text)


async def generate_model(
    prompt: str,
    category: str | None = None,
    raw: bool = False,
) -> dict:
    """Generate an origami model description from a text prompt."""
    system = _build_system_prompt(category, raw)

    for attempt, model in enumerate([MODEL, FALLBACK_MODEL]):
        try:
            result = await _call_llm(prompt, model, system)

            if "error" in result:
                return {"error": result["error"]}

            # Validate part count
            parts = result.get("parts", [])
            if len(parts) > 50:
                result["parts"] = parts[:50]

            # Add metadata
            result["model_used"] = model
            if category:
                result["category_hint"] = category
            else:
                result["category_hint"] = result.get("category", "unknown")

            return result

        except json.JSONDecodeError:
            if attempt == 0:
                logger.warning("Haiku returned invalid JSON, falling back to Sonnet")
                continue
            logger.warning("Fallback model also returned invalid JSON")
            return {"error": "generation_failed"}
        except anthropic.APIError as e:
            if attempt == 0:
                logger.warning("Haiku API error (%s), falling back to Sonnet", e)
                continue
            logger.warning("Fallback model API error: %s", e)
            return {"error": "api_error"}
        except Exception:
            logger.exception("Unexpected error in generate_model")
            return {"error": "internal_error"}

    return {"error": "generation_failed"}
