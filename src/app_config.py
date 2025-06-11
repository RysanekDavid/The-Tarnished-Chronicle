# src/app_config.py

# Verze aplikace
APP_VERSION = "1.0.0"

# Default overlay styles
DEFAULT_OVERLAY_BG_COLOR_STR = "rgba(100, 100, 100, 220)"
DEFAULT_OVERLAY_TEXT_COLOR_STR = "lightblue"
DEFAULT_OVERLAY_FONT_SIZE_STR = "15pt"

# Monitoring settings
DEFAULT_MONITORING_INTERVAL_SEC = 5

# Rust CLI settings
RUST_CLI_TOOL_PATH_PLACEHOLDER = "RUST_CLI_TOOL_PATH_PLACEHOLDER"
DEFAULT_BOSS_REFERENCE_FILENAME = "boss_ids_reference.json"
DLC_BOSS_REFERENCE_FILENAME = "boss_ids_reference_DLC.json" 


# Lokace, které v tomto seznamu nebudou, se automaticky zařadí na konec.
LOCATION_PROGRESSION_ORDER = [
    # Early Game (cca Level 1-40)
    "Limgrave",
    "Weeping Peninsula",
    "Stormveil Castle",

    # Mid Game (cca Level 40-90)
    "Liurnia of the Lakes",
    "Academy of Raya Lucaria",
    "Siofra River",
    "Ainsel River",
    "Caelid",
    "Altus Plateau",
    "Dragonbarrow",
    "Mt. Gelmir",
    "Capital Outskirts",
    "Nokron, Eternal City",
    "Deeproot Depths",
    "Lake of Rot",
    "Leyndell, Royal Capital",

    # Late Game / End Game (cca Level 100+)
    "Forbidden Lands",
    "Mountaintops of the Giants",
    "Consecrated Snowfield",
    "Moonlight Altar (Liurnia)",
    "Mohgwyn Dynasty Mausoleum",
    "Crumbling Farum Azula",
    "Miquella's Haligtree",
    "Leyndell, Ashen Capital",
    "Elden Throne",
]
GAME_PHASE_HEADINGS = {
    "Limgrave": {
        "text": "Early Game: (Levels 1-40)",
        "property": "early"
    },
    "Liurnia of the Lakes": {
        "text": "Mid Game: (Levels 40-90)",
        "property": "mid"
    },
    "Forbidden Lands": {
        "text": "Late Game: (Levels 100+)",
        "property": "late"
    },
    # --- ADDED SECTION ---
    "dlc_header": {
        "text": "DLC: Shadow of the Erdtree",
        "property": "dlc"
    }
    # --- END ADDED SECTION ---
}