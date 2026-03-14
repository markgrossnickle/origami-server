import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
API_KEY = os.environ.get("API_KEY", "")

# Model config
MAX_TOKENS = 4096
API_TIMEOUT = 30  # seconds

# Model selection map: short name -> (provider, model_id, fallback_model_id or None)
MODELS = {
    "haiku": ("anthropic", "claude-haiku-4-5-20251001", None),
    "sonnet": ("anthropic", "claude-sonnet-4-20250514", None),
    "opus": ("anthropic", "claude-opus-4-6", None),
    "flash_lite": ("google", "gemini-2.5-flash-lite", None),
    "gpt4o_mini": ("openai", "gpt-4o-mini", None),
}

# Rate limiting
RATE_LIMIT_BURST_SECONDS = 1  # 1 request per N seconds
RATE_LIMIT_HOURLY = 20  # max requests per hour per player

# Category prompt additions — describe structure/anatomy, NOT construction technique (style prompt handles that)
CATEGORY_PROMPTS = {
    "creature": (
        "Animal or fantasy creature. 8-12 studs in its longest dimension. "
        "Orient the creature naturally — horizontal animals (dogs, worms, fish) along the X axis, "
        "upright creatures (jellyfish, penguins, owls) along the Y axis, etc. Match how it looks in real life.\n\n"
        "PART NAMING IS CRITICAL — the game animates parts based on their name prefix:\n"
        "- Body segments: seg_1, seg_2, seg_3... (body animation)\n"
        "- Wings: wing_L_1, wing_L_2, wing_R_1, wing_R_2 (flapping). Position at Z offsets (+Z = left, -Z = right).\n"
        "- Tail: tail_1, tail_2, tail_3 (swaying). Extend from the rear.\n"
        "- Jaw: jaw_lower (open/close). Below the head.\n"
        "- Legs: leg_FL_1, leg_FR_1, leg_BL_1, leg_BR_1 (walking). FL=front-left, FR=front-right, BL=back-left, BR=back-right.\n"
        "- Eyes and details: eye_L, eye_R, horn_1, etc. (no animation, attached to head).\n"
        "Every creature MUST have seg_* body parts. Add wing_*, tail_*, leg_*, jaw_* as appropriate for the creature type.\n\n"
        "Suggest animation: idle_bob for calm creatures, wobble for nervous ones, flutter if it has wings.\n"
        "LOCOMOTION (required): set the \"locomotion\" field to one of: walk, slither, fly, float, hop, stationary. "
        "Examples: worm/snake → slither, dog/horse → walk, bird/dragon → fly, ghost/jellyfish → float, frog/rabbit → hop, coral/plant → stationary."
    ),
    "avatar": (
        "Complete character model that replaces the player's entire avatar and animates with their movement.\n"
        "Build a full humanoid-shaped figure, 8-10 studs tall.\n\n"
        "BODY PART MAPPING — each part MUST have a \"body_part\" field matching a Roblox body part so it moves with the player:\n"
        "  Head, UpperTorso, LowerTorso, LeftUpperArm, LeftLowerArm, LeftHand, "
        "RightUpperArm, RightLowerArm, RightHand, LeftUpperLeg, LeftLowerLeg, LeftFoot, "
        "RightUpperLeg, RightLowerLeg, RightFoot\n\n"
        "POSITIONING — parts are positioned RELATIVE to their body_part, NOT world-center:\n"
        "- Keep offsets small (within 1-2 studs of [0,0,0]) since they're relative to the body part.\n\n"
        "STRUCTURE:\n"
        "- Head: 2-4 parts\n"
        "- UpperTorso: 2-4 parts\n"
        "- LowerTorso: 1-2 parts\n"
        "- Each arm segment: 1-2 parts\n"
        "- Each leg segment: 1-2 parts\n"
        "- Total: 20-35 parts\n\n"
        "Suggest animation: none (animates with player's movement).\n\n"
        "Example part with body_part field:\n"
        "{\"name\": \"chest\", \"shape\": \"Block\", \"position\": [0, 0, 0], \"size\": [2.5, 2, 1.5], "
        "\"rotation\": [0, 0, 0], \"color\": [160, 80, 60], \"material\": \"SmoothPlastic\", "
        "\"transparency\": 0, \"body_part\": \"UpperTorso\"}"
    ),
    "vehicle": (
        "Rideable vehicle or transport the player will sit in and drive. "
        "Center at [0,0,0]. Leave a gap near center for invisible driver seat (game adds it). "
        "6-8 studs tall, 12-16 long. Suggest animation: none.\n\n"
        "ATTRIBUTES (set in \"attributes\" dict):\n"
        "- Speed (number 10-120): top speed in studs/sec. Default 50. Fast car=100, slow cart=20.\n"
        "- Torque (number 10-100): acceleration force. Default 40.\n"
        "- TurnSpeed (number 2-15): steering responsiveness. Default 8.\n"
        "- CanFly (bool): true if vehicle can fly. Adds vertical thrust on jump key.\n"
        "- FlySpeed (number 10-60): vertical climb speed when flying. Default 30.\n\n"
        "Example: a rocket ship → Speed=100, Torque=80, CanFly=true, FlySpeed=50\n"
        "Example: a wooden cart → Speed=20, Torque=15, TurnSpeed=5"
    ),
    "building": (
        "Architecture or structure. Flat bottom, vertical build. "
        "15-20 studs tall. "
        "Suggest animation: none or breathe for magical buildings."
    ),
    "tool": (
        "Handheld tool or item the player holds. 3-5 studs total. "
        "Center at [0,0,0], grip at bottom (negative Y), functional end at top (positive Y). "
        "Suggest animation: none.\n\n"
        "ATTRIBUTES (set in \"attributes\" dict):\n"
        "- Cooldown (number 0.1-3): seconds between clicks. Default 0.5.\n"
        "- OnClick (list of action dicts): what happens when clicked. Actions execute in order.\n\n"
        "AVAILABLE ACTIONS:\n"
        "- {action:'spawn', shape:'Ball'|'Block'|'Cylinder', size:0.2-2, color:[r,g,b], material:'Neon'|'Glass'|'SmoothPlastic', "
        "transparency:0-0.8, speed:20-200, count:1-8, spread:0-30, lifetime:1-5, gravity:true|false}\n"
        "  Fires projectile(s). count>1 fires a burst. spread = cone angle in degrees. gravity=false for lasers.\n"
        "- {action:'raycast', range:5-50}  Hit-scan (invisible). Sets the target for following actions.\n"
        "- {action:'destroy', radius:0-8}  Break the target. radius>0 = area effect.\n"
        "- {action:'force', magnitude:10-200, direction:'forward'|'up'|'away'}  Push target.\n"
        "- {action:'recolor', color:[r,g,b], material:'Ice'|'Neon'|'Glass'|...}  Change target appearance.\n"
        "- {action:'anchor', freeze:true|false}  Freeze or unfreeze target in place.\n"
        "- {action:'resize', scale:0.3-3}  Grow or shrink target.\n\n"
        "EXAMPLES:\n"
        "Hammer: OnClick=[{action:'raycast',range:10},{action:'destroy',radius:3}], Cooldown=0.3\n"
        "Squirt gun: OnClick=[{action:'spawn',shape:'Ball',size:0.3,color:[100,180,255],material:'Glass',transparency:0.3,speed:80,count:5,spread:15,lifetime:2,gravity:true}]\n"
        "Freeze ray: OnClick=[{action:'raycast',range:30},{action:'anchor',freeze:true},{action:'recolor',color:[150,220,255],material:'Ice'}]\n"
        "Gravity gun: OnClick=[{action:'raycast',range:30},{action:'force',magnitude:150,direction:'up'}]\n"
        "Magic wand: OnClick=[{action:'spawn',shape:'Ball',size:0.5,color:[255,200,50],material:'Neon',speed:100,count:1,lifetime:5,gravity:false},{action:'destroy',radius:2}]\n"
        "Growth ray: OnClick=[{action:'raycast',range:40},{action:'resize',scale:2}]\n"
        "Paint gun: OnClick=[{action:'spawn',shape:'Ball',size:0.3,color:[255,50,50],material:'SmoothPlastic',speed:120,count:1,lifetime:3,gravity:true},{action:'recolor',color:[255,50,50]}]"
    ),
    "hat": (
        "Wearable hat on player's head. 1-2 studs tall, 2-3 studs wide. "
        "Center at [0,0,0], all parts y>=0. 5-12 parts. Suggest animation: none.\n\n"
        "ATTRIBUTES (set in \"attributes\" dict) — optional interactive behavior:\n"
        "- HatEffect (string): 'fly' (upward force on key hold), 'speed' (run faster while worn), 'glow' (parts emit light on key)\n"
        "- EffectKey (string): key that activates effect: 'Space', 'E', 'Q'. Default 'Space'.\n"
        "- FlyForce (number 10-80): upward force for fly effect. Default 40.\n"
        "- SpeedBoost (number 1.2-3.0): walk speed multiplier for speed effect. Default 1.5.\n"
        "- SpinParts (string): name prefix of parts that spin when effect active (e.g. 'propeller').\n"
        "- SpinSpeed (number 90-1440): degrees per second for spinning parts. Default 720.\n\n"
        "Example: propeller hat → HatEffect='fly', FlyForce=40, EffectKey='Space', SpinParts='propeller', SpinSpeed=720\n"
        "Example: speed crown → HatEffect='speed', SpeedBoost=1.8\n"
        "Not every hat needs an effect — a top hat or cowboy hat can be purely cosmetic (no attributes needed)."
    ),
    "prop": (
        "Decorative object or prop. 2-8 studs. Sits on ground or table. "
        "Suggest animation: spin_slow for showcase items, idle_bob for living props."
    ),
    "animation": (
        "ANIMATION MODE — You are generating a keyframe animation for an R15 humanoid mannequin, NOT a 3D model.\n"
        "Return ONLY a JSON object in this exact format (no parts array, no model data):\n"
        "{\n"
        '  "name": "Animation Name",\n'
        '  "duration": 2.0,\n'
        '  "loop": false,\n'
        '  "keyframes": [\n'
        '    { "time": 0, "joints": { "RightShoulder": [0, 0, 0] } },\n'
        '    { "time": 1.0, "joints": { "RightShoulder": [0, 0, -90] } }\n'
        "  ]\n"
        "}\n\n"
        "AVAILABLE JOINTS and what their [X, Y, Z] degree rotations mean:\n"
        "- Neck: X=nod down(+)/up(-), Y=turn left(+)/right(-), Z=tilt left(+)/right(-)\n"
        "- Waist: X=lean forward(+)/back(-), Y=twist left(+)/right(-), Z=side lean left(+)/right(-)\n"
        "- RightShoulder: X=raise forward(+)/back(-), Y=rotate inward(+)/outward(-), Z=raise sideways up(-)/down(+)\n"
        "- LeftShoulder: X=raise forward(+)/back(-), Y=rotate outward(+)/inward(-), Z=raise sideways up(+)/down(-)\n"
        "- RightElbow: X=bend(+), Y=0, Z=0\n"
        "- LeftElbow: X=bend(-), Y=0, Z=0\n"
        "- RightHip: X=kick forward(-)/back(+), Y=rotate inward(+)/outward(-), Z=spread outward(-)/inward(+)\n"
        "- LeftHip: X=kick forward(-)/back(+), Y=rotate outward(+)/inward(-), Z=spread outward(+)/inward(-)\n"
        "- RightKnee: X=bend back(+), Y=0, Z=0\n"
        "- LeftKnee: X=bend back(+), Y=0, Z=0\n"
        "- RightAnkle: X=flex up(-)/point down(+), Y=0, Z=0\n"
        "- LeftAnkle: X=flex up(-)/point down(+), Y=0, Z=0\n\n"
        "RULES:\n"
        "- Rest pose is all zeros [0, 0, 0]\n"
        "- Keep animations between 1-4 seconds duration\n"
        "- Use 4-8 keyframes for smooth motion\n"
        "- First keyframe should be at time 0\n"
        "- Last keyframe time should equal the duration\n"
        "- Set loop: true for repeating animations (dance, idle, breathing) and loop: false for one-shots (wave, bow, punch)\n"
        "- Use realistic joint angle ranges: shoulders -180 to 180, elbows 0-140, knees 0-140, neck -40 to 40\n"
        "- Animate multiple joints together for natural-looking motion\n"
        "- For walking/dancing, alternate left and right sides with phase offsets\n"
        "- Return to rest pose (or near it) at the end for non-looping animations\n"
        "- The name field should describe the animation (e.g. 'Wave Hello', 'Happy Dance', 'Idle Breathing')\n"
    ),
}

# Style prompts — layered on top of base system prompt to change construction aesthetics
STYLE_PROMPTS = {
    "origami": (
        "STYLE — Origami (paper folds):\n"
        "Build using ACCORDION-FOLD CHAINS of Wedge parts — the signature origami technique.\n"
        "- Chain segments along the X axis, spaced ~0.55-0.7 studs apart\n"
        "- Alternate every other segment's Z-rotation between 0° and 180° for the zigzag fold look\n"
        "- Taper segments from head (scale 1.0) to tail (scale ~0.6)\n"
        "- Give segments a Z-wave: offset Z position by sin(index * 0.7) * 0.3 for organic curvature\n"
        "- Leave small gaps (0.2-0.5 studs) between segments — NOT a solid mass\n"
        "- Pick TWO close shades of the same hue and alternate per segment (e.g. [160,190,140] and [140,180,120])\n"
        "- Muted pastel paper colors: sage greens, warm tans, dusty pinks, soft blues\n"
        "- Transparency 0.06 on all parts for paper translucency\n"
        "- SmoothPlastic material everywhere. Ball parts only for tiny details (eyes, nostrils)\n\n"
        "Example worm:\n"
        '{"name":"Worm","category":"creature","parts":['
        '{"name":"seg_1","shape":"Wedge","position":[0,0.6,0],"size":[0.72,0.6,0.72],"rotation":[0,0,0],"color":[160,190,140],"material":"SmoothPlastic","transparency":0.06},'
        '{"name":"seg_2","shape":"Wedge","position":[-0.66,0.6,0.2],"size":[0.69,0.57,0.69],"rotation":[0,0,180],"color":[140,180,120],"material":"SmoothPlastic","transparency":0.06},'
        '{"name":"seg_3","shape":"Wedge","position":[-1.32,0.6,0.28],"size":[0.65,0.54,0.65],"rotation":[0,0,0],"color":[160,190,140],"material":"SmoothPlastic","transparency":0.06},'
        '{"name":"eye_L","shape":"Ball","position":[0.2,0.9,0.2],"size":[0.24,0.24,0.24],"rotation":[0,0,0],"color":[20,20,20],"material":"SmoothPlastic"}'
        '],"animation":"idle_bob","locomotion":"slither","description":"A segmented paper worm with accordion folds"}\n'
        "Apply accordion chains to all subjects: creatures get body chains + wing/tail/leg chains as needed. "
        "Buildings use vertical Wedge stacking. Vehicles get body chains for the hull."
    ),
    "lowpoly": (
        "STYLE — Low Poly (faceted geometric):\n"
        "Build with a mix of Wedge and Block parts to create flat-shaded, faceted surfaces like a low-poly 3D model. "
        "Build solid-looking forms from angled flat faces — each surface facet is a separate Wedge or Block tilted at slight angles. "
        "Colors: earthy, natural tones — forest greens [60,120,50], warm browns [140,100,60], stone grays [130,130,120], "
        "clay oranges [180,110,60]. Use 2-3 close shades per model. SmoothPlastic material. Transparency 0. "
        "The look should feel like a stylized PS1-era 3D model — chunky, geometric, but recognizable."
    ),
    "voxel": (
        "STYLE — Voxel (blocky cubes):\n"
        "Build ONLY with Block parts, all the SAME SIZE: [1, 1, 1] studs. Minecraft-style blocky look. "
        "Stack and arrange cubes on a grid — every position should be integer coordinates. No rotation on any block (all [0,0,0]). "
        "Use 20-40 blocks. Colors: saturated primary palette — bright red [220,50,50], blue [50,80,220], green [50,180,50], "
        "yellow [240,220,50], white [240,240,240], black [30,30,30]. "
        "SmoothPlastic material. Transparency 0. Think pixel art in 3D — chunky, simple, iconic silhouettes."
    ),
    "balloon": (
        "STYLE — Balloon (inflated, round, bouncy):\n"
        "ONLY use Ball and Cylinder shapes — NO Block, NO Wedge. Every single part must be Ball or Cylinder. "
        "Balls for body segments, heads, paws, round features. Cylinders for limbs, tubes, and connecting joints. "
        "Sizes should be generous and rounded — nothing thin or sharp. Use 15-30 parts. "
        "Colors: bright candy palette — hot pink [255,100,150], sky blue [100,180,255], sunny yellow [255,220,80], "
        "mint green [100,220,170], lavender [180,140,255]. SmoothPlastic material. Transparency 0. "
        "Parts should slightly overlap to look like twisted balloon segments."
    ),
    "wireframe": (
        "STYLE — Wireframe (skeletal edge outlines):\n"
        "Build using ONLY thin Cylinder parts as edges/struts — like a wireframe 3D render. "
        "Each cylinder should be very thin: size [0.15, LENGTH, 0.15] where LENGTH varies. "
        "Rotate cylinders to form edges of cubes, triangles, and polygons outlining the subject's shape. "
        "Use 20-40 cylinders. Material: Neon for all edge cylinders (they glow). "
        "Colors: monochrome base — white [230,230,240] or light gray [180,180,190] for most edges. "
        "Add 3-5 accent edges in a single bright color: cyan [0,220,255] or magenta [255,0,200]. "
        "Transparency 0. The result should look like a glowing wireframe hologram."
    ),
    "crystal": (
        "STYLE — Crystal (sharp angular gems):\n"
        "Build with Wedge and Block parts arranged as sharp, angular crystal formations. "
        "Rotate parts at dramatic angles (30, 45, 60 degrees) to create jutting facets and shard-like protrusions. "
        "Use Glass material on most parts. Set transparency to 0.3-0.5 on glass parts. "
        "Use 15-30 parts. Colors: cool gem tones — deep purple [100,40,160], sapphire blue [40,80,200], "
        "teal [40,180,180], amethyst [140,60,180], ice white [200,220,240]. "
        "Add 2-3 small Neon parts inside as inner glow cores (transparency 0, bright color). "
        "The overall shape should look like a crystalline/geode formation of the subject."
    ),
    "plastic": (
        "STYLE — Plastic (smooth toy figurine):\n"
        "Build to look like a glossy plastic toy or action figure — clean surfaces, bold shapes, slightly stylized proportions. "
        "Use SmoothPlastic material on ALL parts. Mix Block, Ball, and Cylinder shapes for clean geometric construction. "
        "Use 15-30 parts. Edges should feel manufactured and precise, not organic. "
        "Colors: saturated toy-box palette — bright red [220,40,40], royal blue [30,80,200], "
        "sunny yellow [250,210,40], vivid green [40,180,60], clean white [240,240,240], jet black [30,30,30]. "
        "Transparency 0. Think LEGO, Playmobil, vinyl toy — smooth, shiny, collectible."
    ),
    "steampunk": (
        "STYLE — Steampunk (industrial Victorian):\n"
        "Build with Cylinder and Block parts to create mechanical, gear-and-pipe aesthetic. "
        "Cylinders for pipes, smokestacks, pistons, gear shafts. Blocks for boiler plates and frames. "
        "Use Foil or Metal material on structural parts (brass/copper look). SmoothPlastic for accent panels. "
        "Use 20-35 parts. Colors: brass [180,140,60], copper [190,100,50], dark brown [80,50,30], "
        "iron gray [90,90,100], aged bronze [140,120,70]. "
        "Transparency 0. Add small Cylinder parts as rivets (size [0.3, 0.15, 0.3]). "
        "Include pipes, gauges, and gear-like circular elements. Victorian industrial machinery vibe."
    ),
    "pixel": (
        "STYLE — Pixel Art (flat 2D sprite):\n"
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
        "STYLE — Neon (cyberpunk glow):\n"
        "Build with Block and Cylinder parts. The base/body uses dark SmoothPlastic (near-black [20,20,30]). "
        "Add glowing outlines, trim, and accent parts using Neon material in bright colors. "
        "For every dark structural part, add 1-2 thin Neon parts along its edges as glow strips. "
        "Neon strips: thin Blocks [LENGTH, 0.15, 0.15] or thin Cylinders. "
        "Use 25-40 parts (roughly half dark base, half neon accents). "
        "Neon colors: hot pink [255,0,150], electric cyan [0,255,255], neon purple [180,0,255], "
        "lime green [0,255,100]. Pick 1-2 neon colors per model. "
        "Transparency 0. Neon material handles the glow. Tron/cyberpunk feel."
    ),
    "freestyle": (
        "STYLE — Freestyle (your choice):\n"
        "You have full creative freedom over shapes, materials, colors, and construction technique. "
        "Favor Block, Ball, and Cylinder parts — only use Wedge if the subject specifically needs angled/sloped surfaces. "
        "Pick materials and colors that look good for this specific subject. "
        "Build the shape that best captures the subject — round things should be round, "
        "boxy things should be boxy, translucent things should use Glass. Trust your judgment."
    ),
}
