import logging
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Header
from pydantic import BaseModel

from app.cache import get_cached, set_cached
from app.config import API_KEY, CATEGORY_PROMPTS, STYLE_PROMPTS
from app.generator import generate_model
from app.rate_limit import check_rate_limit
from app.safety import validate_input

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Origami Server", docs_url=None, redoc_url=None)

CategoryType = Literal["creature", "avatar", "vehicle", "building", "tool", "hat", "prop"]
StyleType = Literal[
    "origami", "lowpoly", "voxel", "balloon", "wireframe",
    "crystal", "plush", "steampunk", "pixel", "neon", "freestyle",
]


def verify_api_key(x_api_key: str = Header()):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY not configured")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


class GenerateRequest(BaseModel):
    prompt: str
    player_id: str
    category: CategoryType | None = None
    style: StyleType = "origami"
    raw: bool = False


class GenerateResponse(BaseModel):
    success: bool
    model: dict | None = None
    error: str | None = None
    category_hint: str | None = None
    model_used: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, _: None = Depends(verify_api_key)):
    logger.info("Generate request from %s: %s", request.player_id, request.prompt)

    # Rate limit check
    rate_error = check_rate_limit(request.player_id)
    if rate_error:
        logger.warning("Rate limited %s: %s", request.player_id, rate_error)
        return GenerateResponse(success=False, error=rate_error)

    # Safety check
    safety_error = validate_input(request.prompt)
    if safety_error:
        logger.warning("Blocked input from %s: %s (%s)", request.player_id, request.prompt, safety_error)
        return GenerateResponse(success=False, error=safety_error)

    # Validate category if provided
    if request.category and request.category not in CATEGORY_PROMPTS:
        return GenerateResponse(success=False, error="invalid_category")

    # Validate style
    if request.style not in STYLE_PROMPTS:
        return GenerateResponse(success=False, error="invalid_style")

    # Check cache
    cache_key = f"{request.prompt}:{request.category or ''}:{request.style}:{'raw' if request.raw else ''}"
    cached = get_cached(cache_key)
    if cached:
        return GenerateResponse(
            success=True,
            model=cached,
            category_hint=cached.get("category_hint"),
            model_used=cached.get("model_used"),
        )

    # Generate via LLM
    result = await generate_model(request.prompt, category=request.category, style=request.style, raw=request.raw)

    if "error" in result:
        return GenerateResponse(success=False, error=result["error"])

    # Cache successful result
    set_cached(cache_key, result)

    return GenerateResponse(
        success=True,
        model=result,
        category_hint=result.get("category_hint"),
        model_used=result.get("model_used"),
    )
