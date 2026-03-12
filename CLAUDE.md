# Origami Server

AI-powered Roblox 3D model generator. Takes text prompts, uses Claude to produce JSON descriptions of Roblox parts that form folded-paper origami-style models.

## Tech Stack

- **Python 3.12** with **FastAPI** + **Uvicorn**
- **Anthropic SDK** (async) — Claude Haiku 4.5 primary, Sonnet 4 fallback
- **Pydantic** for request/response validation
- **Docker** → **Fly.io** deployment (region: iad, port: 8080)

## Commands

```bash
# Run dev server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080

# Docker
docker build -t origami-server .
docker run -p 8080:8080 origami-server
```

No test suite exists. No linter/formatter configured.

## Project Structure

```
app/
  main.py        — FastAPI endpoints (POST /api/generate, GET /health)
  generator.py   — LLM call logic, prompt composition, JSON extraction
  config.py      — All prompts, model config, style/category definitions
  safety.py      — Input validation, output geometry checks, content moderation
  cache.py       — In-memory LRU cache (500 entries, 1h TTL)
  rate_limit.py  — Per-player burst (10s) and hourly (20/hr) rate limiting
```

Total: ~923 lines of Python across 6 files.

## Architecture

**Request flow**: API key auth → rate limit → input safety check → cache lookup → LLM generation (Haiku, fallback Sonnet) → output validation → response

**Prompt composition** (generator.py): Base system prompt + optional style layer + optional category layer. The `raw` flag skips style/category layers.

**Categories**: creature, avatar, vehicle, building, tool, hat, prop
**Styles**: origami, lowpoly, voxel, balloon, wireframe, crystal, plush, steampunk, pixel, neon, freestyle

## Environment Variables

- `ANTHROPIC_API_KEY` — Claude API key (required)
- `API_KEY` — Server auth key sent by Roblox game servers (required)

## Key Conventions

- Snake_case functions/variables, PascalCase classes
- Async throughout (`AsyncAnthropic`, `async def` endpoints)
- Type hints on all functions
- Structured JSON output from LLM with strict geometry rules
- Parts use only 4 Roblox shapes: Block, Ball, Cylinder, Wedge
- Models limited to 15-40 parts, sizes 0.1-50 studs

## Safety Layers

1. **Input**: blocked words regex, character allowlist, prompt injection detection
2. **Output**: shape/material/color/size/position validation, phallic geometry detection, middle-finger detection, name sanitization

## Important Context

- Prompt engineering is the core complexity — config.py holds 400+ lines of system/style/category prompts
- The "accordion fold" technique using Wedge chains is the signature aesthetic
- All geometry is Roblox-specific (studs, Part types, materials)
- Avatar models include `body_part` field mapping to Roblox skeleton
- max_tokens is 4096 to prevent vehicle/complex model truncation
