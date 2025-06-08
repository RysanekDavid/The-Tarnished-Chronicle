# src/app_config.py

# Default overlay styles
DEFAULT_OVERLAY_BG_COLOR_STR = "rgba(100, 100, 100, 220)"
DEFAULT_OVERLAY_TEXT_COLOR_STR = "lightblue"
DEFAULT_OVERLAY_FONT_SIZE_STR = "15pt"

# Monitoring settings
DEFAULT_MONITORING_INTERVAL_SEC = 5

# Rust CLI settings
RUST_CLI_TOOL_PATH_PLACEHOLDER = "RUST_CLI_TOOL_PATH_PLACEHOLDER"
DEFAULT_BOSS_REFERENCE_FILENAME = "boss_ids_reference.json"

# Definuje vlastní pořadí lokací podle postupu hrou.
# Názvy v tomto seznamu se nyní přesně shodují s klíči z vašich dat.
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
# UPRAVENÁ ČÁST: Nyní slovník obsahuje text i název "property" pro QSS
GAME_PHASE_HEADINGS = {
    "Limgrave": {
        "text": "Early Game: (Level 1 - 40)",
        "property": "early"
    },
    "Liurnia of the Lakes": {
        "text": "Mid Game: (Level 40 - 100)",
        "property": "mid"
    },
    "Forbidden Lands": {
        "text": "Late Game: (Level 100 - 150+)",
        "property": "late"
    }
}