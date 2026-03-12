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
        "Color: pick two close shades and alternate per segment (e.g. [160,190,140] and [140,180,120]). "
        "Set transparency: 0.06 on all segments for paper translucency. "
        "Head is segment 1 (rightmost, largest). Tail is the last segment (leftmost, smallest). "
        "DO NOT build upright like a tower. The creature should lie FLAT and HORIZONTAL like a real animal. "
        "\n"
        "PART NAMING IS CRITICAL — the game animates parts based on their name prefix:\n"
        "- Body segments: seg_1, seg_2, seg_3... (accordion fold animation)\n"
        "- Wings: wing_L_1, wing_L_2, wing_R_1, wing_R_2 (flapping animation). "
        "Build each wing as 2-3 Wedge parts chaining outward from the body. Position wings at Z offsets (positive Z = left, negative Z = right).\n"
        "- Tail: tail_1, tail_2, tail_3 (swaying animation). Chain of 2-4 small tapering Wedges extending from the last body segment.\n"
        "- Jaw: jaw_lower (open/close animation). A single Wedge below the head segment.\n"
        "- Legs: leg_FL_1, leg_FR_1, leg_BL_1, leg_BR_1 (walking cycle). Small Wedges below the body. FL=front-left, FR=front-right, BL=back-left, BR=back-right.\n"
        "- Eyes and details: eye_L, eye_R, horn_1, etc. (no animation, stay attached to head).\n"
        "Every creature should have seg_* body parts. Add wing_*, tail_*, leg_*, jaw_* as appropriate for the creature type. "
        "A bird needs wing_L/R parts. A dog needs leg parts and tail parts. A dragon needs wings + tail + jaw. "
        "Suggest animation: idle_bob for calm creatures, wobble for nervous ones, flutter if it has wings."
    ),
    "avatar": (
        "Complete character model that replaces the player's entire avatar and animates with their movement.\n"
        "Build a full humanoid-shaped origami figure, 8-10 studs tall.\n\n"
        "BODY PART MAPPING — each part MUST have a \"body_part\" field matching a Roblox body part so it moves with the player:\n"
        "  Head, UpperTorso, LowerTorso, LeftUpperArm, LeftLowerArm, LeftHand, "
        "RightUpperArm, RightLowerArm, RightHand, LeftUpperLeg, LeftLowerLeg, LeftFoot, "
        "RightUpperLeg, RightLowerLeg, RightFoot\n\n"
        "POSITIONING — parts are positioned RELATIVE to their body_part, NOT world-center:\n"
        "- Head parts: position near [0, 0, 0] (offset from head center)\n"
        "- UpperTorso parts: position near [0, 0, 0] (offset from chest center)\n"
        "- LeftUpperArm parts: small offset from arm center\n"
        "- etc. Keep offsets small (within 1-2 studs of [0,0,0]) since they're relative to the body part.\n\n"
        "STRUCTURE:\n"
        "- Head: 2-4 parts (main head block/wedge + eyes + helmet/horns/hair)\n"
        "- UpperTorso: 2-4 parts (chest, shoulder plates, back plate)\n"
        "- LowerTorso: 1-2 parts (belt/waist area)\n"
        "- Each arm segment: 1-2 parts (upper arm, forearm, hand)\n"
        "- Each leg segment: 1-2 parts (thigh, shin, foot)\n"
        "- Total: 20-35 parts\n\n"
        "Style: bold, expressive origami character. Use angled Wedge parts for shoulders, knees, elbows. "
        "Give it personality — helmet, cape, armor plates, glowing eyes, tail, wings, whatever fits. "
        "Use 2-3 color shades for depth. Alternate shades on adjacent body parts.\n"
        "Suggest animation: none (animates with player's movement).\n\n"
        "Example part with body_part field:\n"
        "{\"name\": \"chest_plate\", \"shape\": \"Block\", \"position\": [0, 0, 0], \"size\": [2.5, 2, 1.5], "
        "\"rotation\": [0, 0, 0], \"color\": [160, 80, 60], \"material\": \"SmoothPlastic\", "
        "\"transparency\": 0.06, \"body_part\": \"UpperTorso\"}"
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
