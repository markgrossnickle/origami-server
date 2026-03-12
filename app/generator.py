import json
import logging

import anthropic

from app.config import ANTHROPIC_API_KEY, CATEGORY_PROMPTS, FALLBACK_MODEL, MAX_TOKENS, MODEL
from app.safety import validate_output

logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are an origami model generator for a Roblox game. Given a subject, return a JSON object describing how to build it from Roblox Parts in a folded-paper origami style.

Rules:
- The "name" field should be the subject itself (e.g. "Dragon", "Sports Car") — do NOT prefix with "Origami"
- Use 15-40 parts maximum
- Each part has: shape (Block/Ball/Cylinder/Wedge), position [x,y,z], size [x,y,z], rotation [x,y,z] (degrees), color [r,g,b] (0-255), material (SmoothPlastic/Neon/Foil/Glass)
- Position is relative to model center at [0,0,0], ground is y=0
- Keep models roughly 8-12 studs tall
- Return ONLY valid JSON, no explanation

Construction style — follow this VERY closely, this is the signature look:
- Build like real origami: the model should look like it was folded from sheets of colored paper
- Use MANY Wedge parts — they are your primary building block. Wedges create the angled fold lines that make origami look like origami
- Construct bodies from CHAINS of alternating Wedge segments — like an accordion fold. A worm = chain of wedges tapering toward the tail. A bird = wedge body with wedge wings. A car = wedge hood, block cabin, wedge trunk
- Alternate between two close shades of the same color on adjacent segments (e.g. sage green RGB(160,190,140) and lighter green RGB(140,180,120)). This color alternation on segments is KEY to the paper-fold look
- Taper segments: parts near extremities (tail, snout, wing tips) should be smaller than center/body parts
- Rotate alternating segments 180° on the Z axis to create the accordion/zigzag fold pattern
- Leave small gaps (0.2-0.5 studs) between segments to suggest separate folds, NOT a solid mass
- Use Ball parts ONLY for tiny details: eyes (dark, ~0.3 studs), nostrils, buttons
- Material: SmoothPlastic on everything (it looks like paper). Use Foil only for metallic buckles/clasps. Use Neon very sparingly for glowing eyes only
- Use muted, natural paper colors — sage greens, warm tans, dusty pinks, soft blues, cream whites. Avoid saturated neon colors
- NEVER place two parts at the exact same position or let faces overlap — offset by at least 0.2 studs
- Add 2-3 small detail parts (eyes, horns, whiskers, spots) to give the model character

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

Generate child-friendly content. Fantasy creatures (skeletons, zombies, ghosts, witches, dragons, monsters) are perfectly fine — this is a game! Only refuse explicit gore, nudity, real-world hate symbols, or drug references — return {"error": "unsafe"} for those."""


def _build_system_prompt(category: str | None, raw: bool) -> str:
    """Build the system prompt, optionally adding category-specific guidance."""
    if raw:
        return SYSTEM_PROMPT

    if category and category in CATEGORY_PROMPTS:
        guidance = CATEGORY_PROMPTS[category]
        return f"{SYSTEM_PROMPT}\n\nCategory guidance for this request ({category}): {guidance}"

    # No category — tell the LLM to auto-detect
    return f"{SYSTEM_PROMPT}\n\nAuto-detect the best category from the prompt and set the \"category\" field accordingly."


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
    raw: bool = False,
) -> dict:
    """Generate an origami model description from a text prompt."""
    system = _build_system_prompt(category, raw)

    for attempt, model in enumerate([MODEL, FALLBACK_MODEL]):
        try:
            result = await _call_llm(prompt, model, system)

            if "error" in result:
                return {"error": result["error"]}

            # Validate and sanitize LLM output
            result = validate_output(result)
            if result is None:
                if attempt == 0:
                    logger.warning("Haiku output failed validation, falling back")
                    continue
                return {"error": "generation_failed"}

            # Add metadata
            result["model_used"] = model
            if category:
                result["category_hint"] = category
            else:
                result["category_hint"] = result.get("category", "unknown")

            return result

        except json.JSONDecodeError as e:
            if attempt == 0:
                logger.warning("Haiku returned invalid JSON, falling back to Sonnet. Raw: %s", e.doc[:500] if e.doc else "empty")
                continue
            logger.warning("Fallback model also returned invalid JSON. Raw: %s", e.doc[:500] if e.doc else "empty")
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
