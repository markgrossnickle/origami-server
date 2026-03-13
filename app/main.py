import logging
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Header
from pydantic import BaseModel

from app.cache import get_cached, set_cached
from app.config import API_KEY, CATEGORY_PROMPTS, MODELS, STYLE_PROMPTS
from app.generator import generate_model, generate_scene
from app.rate_limit import check_rate_limit
from app.safety import validate_input

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Origami Server", docs_url=None, redoc_url=None)

CategoryType = Literal["creature", "avatar", "vehicle", "building", "tool", "hat", "prop", "animation"]
StyleType = Literal[
    "origami", "lowpoly", "voxel", "balloon", "wireframe",
    "crystal", "plush", "steampunk", "pixel", "neon", "freestyle",
]
ModelType = Literal["haiku", "sonnet", "opus"]


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
    model: ModelType = "haiku"
    raw: bool = False
    dm_mode: bool = False


class GenerateResponse(BaseModel):
    success: bool
    model: dict | None = None
    error: str | None = None
    category_hint: str | None = None
    model_used: str | None = None


class SceneRequest(BaseModel):
    prompt: str
    player_id: str
    style: StyleType = "origami"
    model: ModelType = "sonnet"


class SceneResponse(BaseModel):
    success: bool
    scene: dict | None = None
    error: str | None = None
    model_used: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, _: None = Depends(verify_api_key)):
    logger.info("Generate request from %s: %s (dm_mode=%s)", request.player_id, request.prompt, request.dm_mode)

    # Rate limit check (DM mode uses relaxed limits for scene building)
    rate_error = check_rate_limit(request.player_id, dm_mode=request.dm_mode)
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

    # Validate model
    if request.model not in MODELS:
        return GenerateResponse(success=False, error="invalid_model")

    # TODO: Re-enable cache after testing
    # cache_key = f"{request.prompt}:{request.category or ''}:{request.style}:{request.model}:{'raw' if request.raw else ''}"
    # cached = get_cached(cache_key)
    # if cached:
    #     return GenerateResponse(
    #         success=True,
    #         model=cached,
    #         category_hint=cached.get("category_hint"),
    #         model_used=cached.get("model_used"),
    #     )

    # Generate via LLM
    result = await generate_model(request.prompt, category=request.category, style=request.style, raw=request.raw, model=request.model)

    if "error" in result:
        return GenerateResponse(success=False, error=result["error"])

    return GenerateResponse(
        success=True,
        model=result,
        category_hint=result.get("category_hint"),
        model_used=result.get("model_used"),
    )


@app.post("/api/generate-scene", response_model=SceneResponse)
async def generate_scene_endpoint(request: SceneRequest, _: None = Depends(verify_api_key)):
    logger.info("Scene request from %s: %s", request.player_id, request.prompt)

    # Rate limit check (uses DM rate limits)
    rate_error = check_rate_limit(request.player_id, dm_mode=True)
    if rate_error:
        logger.warning("Rate limited %s: %s", request.player_id, rate_error)
        return SceneResponse(success=False, error=rate_error)

    # Safety check
    safety_error = validate_input(request.prompt)
    if safety_error:
        logger.warning("Blocked scene input from %s: %s (%s)", request.player_id, request.prompt, safety_error)
        return SceneResponse(success=False, error=safety_error)

    # Validate model
    if request.model not in MODELS:
        return SceneResponse(success=False, error="invalid_model")

    # Generate scene plan via LLM
    result = await generate_scene(request.prompt, model=request.model)

    if "error" in result:
        return SceneResponse(success=False, error=result["error"])

    return SceneResponse(
        success=True,
        scene=result,
        model_used=result.get("model_used"),
    )
