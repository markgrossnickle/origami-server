import json
import logging

import anthropic

from app.config import ANTHROPIC_API_KEY, MAX_TOKENS, MODEL

logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are an origami model generator for a Roblox game. Given a subject, return a JSON object describing how to build it from Roblox Parts in an origami/low-poly style.

Rules:
- Use 15-40 parts maximum
- Each part has: shape (Block/Ball/Cylinder/Wedge/Corner), position [x,y,z], size [x,y,z], rotation [x,y,z] (degrees), color [r,g,b] (0-255), material (SmoothPlastic/Neon/Foil/Glass)
- Position is relative to model center at [0,0,0], ground is y=0
- Use the origami/low-poly aesthetic — angular, folded paper look
- Keep models roughly 8-12 studs tall
- Return ONLY valid JSON, no explanation

Response format:
{
  "name": "Dragon",
  "category": "fantasy_creature",
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

Only generate safe, child-friendly objects. Refuse weapons, gore, inappropriate content — return {"error": "unsafe"} instead."""


async def generate_model(prompt: str) -> dict:
    """Generate an origami model description from a text prompt."""
    try:
        message = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Create an origami model of: {prompt}"}],
        )

        text = message.content[0].text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(text)

        if "error" in result:
            return {"error": result["error"]}

        # Validate part count
        parts = result.get("parts", [])
        if len(parts) > 50:
            result["parts"] = parts[:50]

        return result

    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM response as JSON")
        return {"error": "generation_failed"}
    except anthropic.APIError as e:
        logger.warning("Anthropic API error: %s", e)
        return {"error": "api_error"}
    except Exception:
        logger.exception("Unexpected error in generate_model")
        return {"error": "internal_error"}
