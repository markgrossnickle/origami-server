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
        "Suggest animation: idle_bob for calm creatures, wobble for nervous ones, flutter if it has wings.\n"
        "LOCOMOTION (required): set the \"locomotion\" field to one of: walk, slither, fly, float, hop, stationary. "
        "Pick the one that matches how this creature naturally moves. "
        "Examples: worm/snake → slither, dog/horse → walk, bird/dragon → fly, ghost/jellyfish → float, frog/rabbit → hop, coral/plant → stationary."
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

# Style prompts — layered on top of base system prompt to change construction aesthetics
STYLE_PROMPTS = {
    "origami": (
        "STYLE OVERRIDE — Origami (paper folds):\n"
        "Use the accordion-fold Wedge chain technique exactly as described in the base instructions. "
        "This IS the default style. Muted pastel paper colors: sage greens, warm tans, dusty pinks, soft blues. "
        "Transparency 0.06 on all parts for paper translucency. SmoothPlastic material everywhere. "
        "Leave gaps between segments for the folded-paper look."
    ),
    "lowpoly": (
        "STYLE OVERRIDE — Low Poly (faceted geometric):\n"
        "Build with a mix of Wedge and Block parts to create flat-shaded, faceted surfaces like a low-poly 3D model. "
        "Do NOT use accordion chains — instead, build solid-looking forms from angled flat faces. "
        "Use 15-30 parts. Each surface facet is a separate Wedge or Block tilted at slight angles to catch light differently. "
        "Colors: earthy, natural tones — forest greens [60,120,50], warm browns [140,100,60], stone grays [130,130,120], "
        "clay oranges [180,110,60]. Use 2-3 close shades per model. SmoothPlastic material. Transparency 0. "
        "The look should feel like a stylized PS1-era 3D model — chunky, geometric, but recognizable."
    ),
    "voxel": (
        "STYLE OVERRIDE — Voxel (blocky cubes):\n"
        "Build ONLY with Block parts, all the SAME SIZE: [1, 1, 1] studs. This creates a Minecraft-style blocky look. "
        "Stack and arrange cubes on a grid — every position should be integer coordinates. No rotation on any block (all [0,0,0]). "
        "Use 20-40 blocks. Colors: saturated primary palette — bright red [220,50,50], blue [50,80,220], green [50,180,50], "
        "yellow [240,220,50], white [240,240,240], black [30,30,30]. "
        "SmoothPlastic material. Transparency 0. Think pixel art in 3D — chunky, simple, iconic silhouettes."
    ),
    "balloon": (
        "STYLE OVERRIDE — Balloon (inflated, round, bouncy):\n"
        "Build primarily with Ball and Cylinder parts to create inflated, puffy, balloon-animal shapes. "
        "No Wedge parts. Balls for body segments, heads, paws. Cylinders for limbs and connecting tubes. "
        "Sizes should be generous and rounded — nothing thin or sharp. Use 15-30 parts. "
        "Colors: bright candy palette — hot pink [255,100,150], sky blue [100,180,255], sunny yellow [255,220,80], "
        "mint green [100,220,170], lavender [180,140,255]. SmoothPlastic material. Transparency 0. "
        "Parts should slightly overlap (touching/intersecting) to look like twisted balloon segments."
    ),
    "wireframe": (
        "STYLE OVERRIDE — Wireframe (skeletal edge outlines):\n"
        "Build shapes using ONLY thin Cylinder parts as edges/struts — like a wireframe 3D render. "
        "Each cylinder should be very thin: size [0.15, LENGTH, 0.15] where LENGTH varies. "
        "Rotate cylinders to form edges of cubes, triangles, and polygons outlining the subject's shape. "
        "Use 20-40 cylinders. Material: Neon for all edge cylinders (they glow). "
        "Colors: monochrome base — white [230,230,240] or light gray [180,180,190] for most edges. "
        "Add 3-5 accent edges in a single bright color: cyan [0,220,255] or magenta [255,0,200]. "
        "Transparency 0. The result should look like a glowing wireframe hologram."
    ),
    "crystal": (
        "STYLE OVERRIDE — Crystal (sharp angular gems):\n"
        "Build with Wedge and Block parts arranged as sharp, angular crystal formations. "
        "Rotate parts at dramatic angles (30°, 45°, 60°) to create jutting facets and shard-like protrusions. "
        "Use Glass material on most parts for transparency. Set transparency to 0.3-0.5 on glass parts. "
        "Use 15-30 parts. Colors: cool gem tones — deep purple [100,40,160], sapphire blue [40,80,200], "
        "teal [40,180,180], amethyst [140,60,180], ice white [200,220,240]. "
        "Add 2-3 small Neon parts inside as inner glow cores (transparency 0, bright color). "
        "The overall shape should look like a crystalline/geode formation of the subject."
    ),
    "plush": (
        "STYLE OVERRIDE — Plush (soft stuffed animal):\n"
        "Build with Ball parts for main body segments and rounded Block parts for connecting pieces. "
        "Everything should look soft, puffy, and huggable — generous sizes, no sharp edges. "
        "No Wedge parts. Use Fabric material on all parts for a soft textile look. "
        "Use 15-30 parts. Colors: warm pastels — soft pink [240,180,190], cream [250,240,220], "
        "baby blue [170,200,230], light lavender [210,190,230], peach [250,210,180]. "
        "Transparency 0. Add small Ball parts for button eyes (dark [30,30,30], size ~0.4 studs). "
        "Parts should overlap slightly to look stuffed and plump. Think teddy bear, plushie, Squishmallow."
    ),
    "steampunk": (
        "STYLE OVERRIDE — Steampunk (industrial Victorian):\n"
        "Build with Cylinder and Block parts to create mechanical, gear-and-pipe aesthetic. "
        "Cylinders for pipes, smokestacks, pistons, and gear shafts. Blocks for boiler plates and frames. "
        "Use Foil or Metal material on structural parts (brass/copper look). SmoothPlastic for accent panels. "
        "Use 20-35 parts. Colors: brass [180,140,60], copper [190,100,50], dark brown [80,50,30], "
        "iron gray [90,90,100], aged bronze [140,120,70]. "
        "Transparency 0. Add small Cylinder parts as rivets (size [0.3, 0.15, 0.3]). "
        "Include pipes, gauges, and gear-like circular elements. The vibe is Victorian industrial machinery."
    ),
    "pixel": (
        "STYLE OVERRIDE — Pixel Art (flat 2D sprite):\n"
        "Build a FLAT, billboard-like sprite using thin Block parts arranged like pixels. "
        "All blocks face the same direction (thin on Z axis): size [PIXEL_SIZE, PIXEL_SIZE, 0.3] where PIXEL_SIZE is 0.6-0.8. "
        "Arrange blocks on a grid in the XY plane — like pixel art on a canvas. Use 25-40 blocks. "
        "Z positions should all be 0 (or very close). The model should look like a 2D sprite standing upright. "
        "SmoothPlastic material. Transparency 0. "
        "Colors: retro 8-bit palette — limited to 8-10 distinct colors per model. Use strong contrast. "
        "Example palette: black [20,20,20], white [240,240,240], red [220,50,50], blue [50,80,220], "
        "green [50,180,50], yellow [240,220,50], skin [240,190,150], brown [140,80,40]."
    ),
    "neon": (
        "STYLE OVERRIDE — Neon (cyberpunk glow):\n"
        "Build with Block and Cylinder parts. The base/body uses dark SmoothPlastic (near-black [20,20,30]). "
        "Add glowing outlines, trim, and accent parts using Neon material in bright colors. "
        "For every dark structural part, add 1-2 thin Neon parts along its edges as glow strips. "
        "Neon strips: thin Blocks [LENGTH, 0.15, 0.15] or thin Cylinders. "
        "Use 25-40 parts (roughly half dark base, half neon accents). "
        "Neon colors: hot pink [255,0,150], electric cyan [0,255,255], neon purple [180,0,255], "
        "lime green [0,255,100]. Pick 1-2 neon colors per model. "
        "Dark parts: transparency 0. Neon parts: transparency 0 (Neon material handles the glow). "
        "The overall look should feel like a Tron/cyberpunk object glowing in the dark."
    ),
    "freestyle": (
        "STYLE OVERRIDE — Freestyle (LLM's choice):\n"
        "IGNORE the accordion-fold and Wedge chain instructions from the base prompt. "
        "You have full creative freedom over shapes, materials, colors, and construction technique. "
        "Use whatever combination of Block, Ball, Cylinder, and Wedge parts best represents the subject. "
        "Pick materials (SmoothPlastic, Neon, Foil, Glass, Fabric) and colors that look good for this specific subject. "
        "The only rules: use 15-40 parts, follow the naming conventions (seg_*, wing_*, tail_*, leg_*, jaw_*, eye_*), "
        "and make it look great. Build the shape that best captures the subject — round things should be round, "
        "sharp things should be sharp, translucent things should use Glass. Trust your judgment."
    ),
}
