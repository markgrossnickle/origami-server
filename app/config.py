import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_KEY = os.environ.get("API_KEY", "")

# Model config
MODEL = "claude-haiku-4-5-20251001"
FALLBACK_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
API_TIMEOUT = 30  # seconds

# Rate limiting
RATE_LIMIT_BURST_SECONDS = 10  # 1 request per N seconds
RATE_LIMIT_HOURLY = 20  # max requests per hour per player

# Category prompt additions
CATEGORY_PROMPTS = {
    "creature": (
        "Animal or fantasy creature. Build HORIZONTALLY along the X axis, low to the ground (2-4 studs tall, 8-12 studs long). "
        "Body: chain of 8-12 Wedge segments spaced ~0.6 studs apart along X. "
        "CRITICAL: alternate every other segment's Z-rotation between 0° and 180° for the accordion-fold zigzag. "
        "CRITICAL: taper segments from head (scale 1.0) to tail (scale 0.6) — each segment slightly smaller than the last. "
        "Give segments a Z-wave: offset each segment's Z position by sin(index * 0.7) * 0.3 for organic curvature. "
        "Name segments sequentially: seg_1, seg_2, seg_3, etc. "
        "Color: pick two close shades and alternate per segment (e.g. [160,190,140] and [140,180,120]). "
        "Set transparency: 0.06 on all segments for paper translucency. "
        "Head is segment 1 (rightmost, largest). Tail is the last segment (leftmost, smallest). "
        "Limbs (legs, wings, fins) are short sub-chains of 2-3 smaller Wedges branching off the body. "
        "Eyes: tiny Ball parts (~0.24 studs, dark [20,20,20]) on the head segment. "
        "DO NOT build upright like a tower. The creature should lie FLAT and HORIZONTAL like a real animal. "
        "Suggest animation: idle_bob for calm creatures, wobble for nervous ones, flutter if it has wings."
    ),
    "avatar": (
        "Complete character model that replaces the player's entire avatar. "
        "Build a full humanoid-shaped origami figure centered at [0,0,0], 8-10 studs tall. "
        "The model will be welded to the player's invisible body, so it must look like a complete character on its own. "
        "Include a head, torso, arms, and legs as separate parts — but name them creatively (not Roblox body part names). "
        "Style: bold, expressive origami character. Use angled Wedge parts for shoulders, knees, elbows, and facial features. "
        "Give it personality — a helmet, cape, armor plates, glowing eyes, tail, wings, whatever fits the theme. "
        "Use 2-3 color shades for depth. Add small detail parts (eyes, buttons, belt, claws). "
        "Suggest animation: none (moves with the player's character)."
    ),
    "vehicle": (
        "Rideable vehicle or transport the player will sit in and drive. "
        "IMPORTANT: center the model at [0,0,0]. Leave a gap/opening near the center for "
        "an invisible driver seat (don't create the seat — the game adds it automatically). "
        "Body should surround where a seated player would be. 6-8 studs tall, 12-16 studs long. "
        "Wheels, wings, or propulsion on bottom/sides. Functional details (windows, doors). "
        "Style: angular, faceted body like a paper airplane or cardboard car. "
        "Use Wedge parts for hood, windshield angles, and tail fins. "
        "Cylinders for wheels only. Windows are thin inset Blocks in a darker color. "
        "Add Foil material for chrome/metallic trim accents. "
        "Suggest animation: none (vehicle is physics-driven by the player)."
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
        "Wearable hat that sits on top of a player's head. Keep it SMALL: 1-2 studs tall, 2-3 studs wide max. "
        "The player's head is only ~1.2 studs wide, so the hat must be proportional. "
        "IMPORTANT: center at [0,0,0]. ALL parts must be at y >= 0 (nothing below the head). "
        "Build upward from y=0. Keep it lightweight (5-12 parts). "
        "Style: compact, recognizable silhouette. Brims should be thin (0.2-0.3 studs thick). "
        "Use Wedge parts for brims and decorative edges. "
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
