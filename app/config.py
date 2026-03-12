import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_KEY = os.environ.get("API_KEY", "")

# Model config
MODEL = "claude-haiku-4-5-20251001"
FALLBACK_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 2048
API_TIMEOUT = 30  # seconds

# Rate limiting
RATE_LIMIT_BURST_SECONDS = 10  # 1 request per N seconds
RATE_LIMIT_HOURLY = 20  # max requests per hour per player

# Category prompt additions
CATEGORY_PROMPTS = {
    "creature": "Animal/fantasy creature. 4 legs (or appropriate limbs), tail, head with features. Ground stance. 8-10 studs tall. Emphasis on recognizable silhouette.",
    "avatar": "Humanoid character. Standing upright, head/torso/arms/legs. 10-12 studs tall. Can have accessories (hat, cape, etc). Face features on head.",
    "vehicle": "Vehicle/transport. Wheels, wings, or propulsion on bottom/sides. Elongated body. 6-8 studs tall, 12-16 studs long. Functional details (windows, doors).",
    "building": "Architecture/structure. Flat bottom, vertical walls, roof. Door opening suggested. 15-20 studs tall. Can include windows, chimney, details.",
    "tool": "Handheld tool/item. 3-5 studs total size. Grip/handle at bottom, functional end at top. Simple but recognizable.",
    "prop": "Decorative object/prop. 2-8 studs. Sits on ground or table. Detail-focused.",
}
