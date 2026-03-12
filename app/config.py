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
    "creature": (
        "Animal or fantasy creature. 4 legs (or appropriate limbs), tail, head with features. "
        "Ground stance, 8-10 studs tall. Emphasis on recognizable silhouette. "
        "Style: use Wedge parts for snout, ears, tail tip, and claws. Tilt the head slightly. "
        "Body should be a large Block or two, legs are thin angled Blocks. "
        "Add small Ball parts for eyes. Use 2-3 shades of the main color. "
        "Suggest animation: idle_bob for calm creatures, wobble for nervous ones, flutter if it has wings."
    ),
    "avatar": (
        "Humanoid character. Standing upright, head/torso/arms/legs. 10-12 studs tall. "
        "Can have accessories (hat, cape, etc). Face features on head. "
        "Style: blocky paper-doll look. Head is a Block with small detail parts for eyes/mouth. "
        "Torso is a slightly wider Block, arms and legs are thin rotated Blocks. "
        "Add character through pose — one arm raised, slight lean, head tilt. "
        "Accessories (hat, scarf, tool) add personality. Use contrasting colors for clothing vs skin. "
        "Suggest animation: idle_bob or breathe."
    ),
    "vehicle": (
        "Vehicle or transport. Wheels, wings, or propulsion on bottom/sides. Elongated body. "
        "6-8 studs tall, 12-16 studs long. Functional details (windows, doors). "
        "Style: angular, faceted body like a paper airplane or cardboard car. "
        "Use Wedge parts for hood, windshield angles, and tail fins. "
        "Cylinders for wheels/exhaust only. Windows are thin inset Blocks in a darker color. "
        "Add Foil material for chrome/metallic trim accents. "
        "Suggest animation: idle_bob for floating vehicles, none for grounded."
    ),
    "building": (
        "Architecture or structure. Flat bottom, vertical walls, roof. Door opening suggested. "
        "15-20 studs tall. Can include windows, chimney, details. "
        "Style: like a paper pop-up card. Walls are flat Blocks, roof uses angled Wedge parts. "
        "Door is a darker recessed Block. Windows are small contrasting-color Blocks inset slightly. "
        "Add a chimney, awning, or sign for character. Use warm colors (cream, tan, terracotta). "
        "Suggest animation: none or breathe for magical buildings."
    ),
    "tool": (
        "Handheld tool or weapon-like item the player will hold. 3-5 studs total size. "
        "IMPORTANT: center the model at [0,0,0] with the grip/handle at the bottom (negative Y) "
        "and the functional end at the top (positive Y). This will be converted to a Roblox Tool. "
        "Style: bold, chunky shapes — should read clearly even when small. "
        "Handle is a thin Block at bottom, head/blade/end is a wider Block or Wedge at top. "
        "Use Foil for metallic tool heads, SmoothPlastic for wooden handles. "
        "Add 1-2 small accent parts (rivets, wrapping, gems). "
        "Suggest animation: none (tool moves with player hand)."
    ),
    "hat": (
        "Wearable hat or headwear that sits on top of a player's head. 2-4 studs tall, 2-4 studs wide. "
        "IMPORTANT: center the model at [0,0,0] — the bottom of the hat (y=0) will sit on the head. "
        "Build upward from y=0. Keep it lightweight (5-15 parts). "
        "Style: playful, exaggerated proportions. A crown should have tall spikes, a top hat should be extra tall. "
        "Use Wedge parts for brims, curves, and decorative edges. "
        "Add small detail parts — feathers, gems, bands, buckles. "
        "Suggest animation: none (hat moves with player head)."
    ),
    "prop": (
        "Decorative object or prop. 2-8 studs. Sits on ground or table. Detail-focused. "
        "Style: charming, detailed miniature. Pack detail into a small space. "
        "Use varied shapes — mix Blocks, Wedges, Cylinders, small Balls for roundness. "
        "Color should be vibrant and appealing. Add Neon for any glowing elements (gems, flames, screens). "
        "Suggest animation: spin_slow for showcase items, idle_bob for living props."
    ),
}
