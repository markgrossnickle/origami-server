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
- Each part has: shape (Block/Ball/Cylinder/Wedge), position [x,y,z], size [x,y,z], rotation [x,y,z] (degrees), color [r,g,b] (0-255), material (SmoothPlastic/Neon/Foil/Glass), transparency (0-1, default 0), body_part (optional, for avatars only)
- Position is relative to model center at [0,0,0], ground is y=0
- Return ONLY valid JSON, no explanation

Construction style — THIS IS CRITICAL, follow it exactly:

ACCORDION FOLD CHAINS (the signature technique):
- The primary building block is CHAINS of Wedge parts arranged like an accordion/zigzag fold
- Chains run HORIZONTALLY (along the X axis), NOT vertically. Creatures are long and low, not tall towers
- Each chain segment is a Wedge, spaced ~0.55-0.7 studs apart along the X axis
- EVERY OTHER segment is rotated 180° on the Z axis: rotation [0,0,180] for even segments, [0,0,0] for odd. This creates the zigzag fold look
- Segments TAPER from head to tail: the first segment is largest (scale 1.0), the last is smallest (scale ~0.6). Use a linear taper
- Give segments a slight Z-axis wave: offset Z position by sin(index * 0.7) * 0.3 for an organic curve
- Set transparency to 0.06 on ALL paper parts (subtle translucency like real paper)

COLOR ALTERNATION (key to the paper-fold look):
- Pick TWO close shades of the same hue. Example: sage green [160,190,140] and lighter green [140,180,120]
- Alternate these colors on every other segment: segment 1 = color A, segment 2 = color B, segment 3 = color A, etc.
- Use muted, natural paper colors: sage greens, warm tans, dusty pinks, soft blues, cream whites. NEVER saturated neon colors

DETAILS AND FINISHING:
- Ball parts ONLY for tiny details: eyes (~0.3 studs, dark [20,20,20]), nostrils, buttons
- Material: SmoothPlastic on everything (it looks like paper). Foil only for metallic accents. Neon very sparingly for glowing eyes only
- Leave small gaps (0.2-0.5 studs) between segments — they should NOT be a solid mass
- NEVER place two parts at the exact same position — offset by at least 0.2 studs
- Add 2-3 small detail parts for character (eyes, horns, whiskers, spots, antennae)

ORIENTATION AND SCALE:
- Creatures/animals are HORIZONTAL and LOW to the ground (2-4 studs tall, 8-12 studs long)
- Buildings are vertical (15-20 studs tall)
- Vehicles are horizontal (6-8 tall, 12-16 long)
- Props/tools are compact (2-8 studs)

Here is a CONCRETE EXAMPLE of a worm built with this technique (study this pattern):
{
  "name": "Worm",
  "category": "creature",
  "parts": [
    {"name": "seg_1", "shape": "Wedge", "position": [0, 0.6, 0], "size": [0.72, 0.6, 0.72], "rotation": [0, 0, 0], "color": [160, 190, 140], "material": "SmoothPlastic", "transparency": 0.06},
    {"name": "seg_2", "shape": "Wedge", "position": [-0.66, 0.6, 0.2], "size": [0.69, 0.57, 0.69], "rotation": [0, 0, 180], "color": [140, 180, 120], "material": "SmoothPlastic", "transparency": 0.06},
    {"name": "seg_3", "shape": "Wedge", "position": [-1.32, 0.6, 0.28], "size": [0.65, 0.54, 0.65], "rotation": [0, 0, 0], "color": [160, 190, 140], "material": "SmoothPlastic", "transparency": 0.06},
    {"name": "seg_4", "shape": "Wedge", "position": [-1.98, 0.6, 0.19], "size": [0.62, 0.51, 0.62], "rotation": [0, 0, 180], "color": [140, 180, 120], "material": "SmoothPlastic", "transparency": 0.06},
    {"name": "seg_5", "shape": "Wedge", "position": [-2.64, 0.6, -0.02], "size": [0.58, 0.48, 0.58], "rotation": [0, 0, 0], "color": [160, 190, 140], "material": "SmoothPlastic", "transparency": 0.06},
    {"name": "eye_L", "shape": "Ball", "position": [0.2, 0.9, 0.2], "size": [0.24, 0.24, 0.24], "rotation": [0, 0, 0], "color": [20, 20, 20], "material": "SmoothPlastic"},
    {"name": "eye_R", "shape": "Ball", "position": [0.2, 0.9, -0.2], "size": [0.24, 0.24, 0.24], "rotation": [0, 0, 0], "color": [20, 20, 20], "material": "SmoothPlastic"}
  ],
  "animation": "idle_bob",
  "description": "A segmented paper worm with accordion folds"
}

Notice: segments chain along X, alternate Z-rotation (0° / 180°), taper smaller, Z-wave offset, two green shades alternating.
Apply this SAME accordion-chain technique to ALL creatures (snake = long chain, bird = short body chain + wing chains, spider = body chain + leg chains, dragon = body chain + wing chains + tail chain).

Response format:
{
  "name": "Dragon",
  "category": "creature",
  "parts": [
    {
      "name": "body_1",
      "shape": "Wedge",
      "position": [0, 2, 0],
      "size": [1.5, 1.2, 1.5],
      "rotation": [0, 0, 0],
      "color": [80, 200, 80],
      "material": "SmoothPlastic",
      "transparency": 0.06
    }
  ],
  "animation": "idle_bob",
  "description": "A fierce origami dragon with angular wings"
}

Available animations: idle_bob, spin_slow, bounce, wobble, flutter, breathe, none
Available categories: creature, avatar, vehicle, building, tool, prop

SHAPE SAFETY — this is critical:
- This is a children's game. Consider what the FINAL 3D SHAPE looks like, not just the text prompt.
- NEVER generate shapes that resemble genitalia, middle fingers, or other inappropriate body parts — even if the prompt seems innocent.
- If a prompt asks for a shape combination that would look phallic (e.g. a tall cylinder with spheres at the base), refuse with {"error": "unsafe"}.
- If the prompt is clearly trying to trick you into making something inappropriate through euphemism or indirect description, refuse.

Generate child-friendly content. Fantasy creatures (skeletons, zombies, ghosts, witches, dragons, monsters) are perfectly fine — this is a game! Only refuse explicit gore, nudity, real-world hate symbols, drug references, or shapes resembling genitalia/obscene gestures — return {"error": "unsafe"} for those."""


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
