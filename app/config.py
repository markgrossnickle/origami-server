import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_KEY = os.environ.get("API_KEY", "")

# Model config
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 2048
API_TIMEOUT = 30  # seconds

# Safety: allowed categories for generation
ALLOWED_CATEGORIES = [
    "animal",
    "vehicle",
    "building",
    "food",
    "plant",
    "fantasy_creature",
    "object",
    "nature",
    "instrument",
    "furniture",
]
