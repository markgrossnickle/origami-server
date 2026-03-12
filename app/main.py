import logging

from fastapi import Depends, FastAPI, HTTPException, Header
from pydantic import BaseModel

from app.cache import get_cached, set_cached
from app.config import API_KEY
from app.generator import generate_model
from app.safety import validate_input

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Origami Server", docs_url=None, redoc_url=None)


def verify_api_key(x_api_key: str = Header()):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY not configured")
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


class GenerateRequest(BaseModel):
    prompt: str
    player_id: str


class GenerateResponse(BaseModel):
    success: bool
    model: dict | None = None
    error: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest, _: None = Depends(verify_api_key)):
    logger.info("Generate request from %s: %s", request.player_id, request.prompt)

    # Safety check
    safety_error = validate_input(request.prompt)
    if safety_error:
        logger.warning("Blocked input from %s: %s (%s)", request.player_id, request.prompt, safety_error)
        return GenerateResponse(success=False, error=safety_error)

    # Check cache
    cached = get_cached(request.prompt)
    if cached:
        return GenerateResponse(success=True, model=cached)

    # Generate via LLM
    result = await generate_model(request.prompt)

    if "error" in result:
        return GenerateResponse(success=False, error=result["error"])

    # Cache successful result
    set_cached(request.prompt, result)

    return GenerateResponse(success=True, model=result)
