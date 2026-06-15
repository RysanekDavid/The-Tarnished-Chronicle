# src/boss_data_manager.py
import json
import copy
import re
from PySide6.QtCore import QFile, QIODevice
from .stats_manager import StatsManager


def _normalize_name(text: str) -> str:
    return "".join(filter(str.isalnum, text)).lower()


# Remembrance bosses + mandatory story bosses (the path from Morgott to the
# Elden Beast is fixed: Draconic Tree Sentinel, Godfrey's shade, Godskin Duo
# and Gideon must all be defeated) — exact names as in the data files
MAIN_BOSS_NAMES = {
    "Margit, the Fell Omen",
    "Draconic Tree Sentinel",
    "Godfrey, First Elden Lord",
    "Godskin Duo",
    "Sir Gideon Ofnir, the All-Knowing",
    "Godrick the Grafted",
    "Rennala, Queen of the Full Moon",
    "Starscourge Radahn",
    "Morgott, the Omen King",
    "Rykard, Lord of Blasphemy",
    "Malenia, Blade of Miquella",
    "Mohg, Lord of Blood",
    "Maliketh, the Black Blade",
    "Fire Giant",
    "Godfrey, First Elden Lord (Hoarah Loux)",
    "Radagon of the Golden Order & Elden Beast",
    "Dragonlord Placidusax",
    "Astel, Naturalborn of the Void",
    "Regal Ancestor Spirit",
    "Lichdragon Fortissax",
    # DLC remembrances
    "Divine Beast Dancing Lion",
    "Rellana, Twin Moon Knight",
    "Putrescent Knight",
    "Messmer the Impaler",
    "Romina, Saint of the Bud",
    "Scadutree Avatar",
    "Commander Gaius",
    "Midra Lord of Frenzied Flame",
    "Metyr, Mother of Fingers",
    "Bayle the Dread",
    "Promised Consort Radahn",
}
_MAIN_BOSS_KEYS = {_normalize_name(n) for n in MAIN_BOSS_NAMES}

# Event flag IDs encode the map: 8-digit IDs with these prefixes are
# catacombs/caves/tunnels/divine towers and the DLC gaols/forges/caves
_MINI_DUNGEON_ID_PREFIXES = ("30", "31", "32", "34", "39", "40", "41", "43")


def get_boss_category(boss_info: dict) -> str:
    """Returns 'main', 'overworld', 'minidungeon' or 'legacy'.

    Derived from the boss name (remembrances) and the event flag ID,
    whose leading digits encode the in-game map. 10-digit IDs are
    open-world map tiles; 8-digit IDs are dungeon maps.
    """
    if _normalize_name(boss_info.get("name", "")) in _MAIN_BOSS_KEYS:
        return "main"
    event_id = boss_info.get("event_id")
    if isinstance(event_id, list):
        event_id = event_id[0] if event_id else None
    id_str = str(event_id) if event_id is not None else ""
    if len(id_str) >= 10:
        return "overworld"
    if id_str[:2] in _MINI_DUNGEON_ID_PREFIXES:
        return "minidungeon"
    return "legacy"


class BossDataManager:
    def __init__(self, base_filename="boss_ids_reference.json", dlc_filename="boss_ids_reference_DLC.json", descriptions_filename="boss_descriptions.json", dlc_descriptions_filename="boss_descriptions_DLC.json"):
        self.base_filename = base_filename
        self.dlc_filename = dlc_filename
        self.descriptions_filename = descriptions_filename
        self.dlc_descriptions_filename = dlc_descriptions_filename
        self.stats_manager = StatsManager()
        
        # Internal storage for raw, unfiltered data
        self._base_data = {}
        self._dlc_data = {}
        self._boss_descriptions = {}
        self._dlc_boss_descriptions = {}
        
        # This holds the combined data based on the current filter ('all', 'base', 'dlc')
        # It serves as a clean template before character-specific statuses are applied.
        self._active_data_template = {}
        
        # This is the primary data structure for the UI, containing the template
        # merged with the current character's defeated statuses.
        self.boss_data_by_location = {}
        
        self.all_event_ids_to_monitor = []

        # Filters applied when building the active template
        self._content_filter = "base"
        self._type_filter = "all"  # all | no_minidungeon | main | custom
        self._custom_preset_ids = set()  # event IDs (as str) for the custom preset


    def _load_json_file(self, filename):
        """Loads and validates a single JSON file from the Qt Resource System."""
        # Construct the resource path
        filepath = f":/data/Bosses/{filename}"
        
        qfile = QFile(filepath)
        if not qfile.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
            print(f"Error: Cannot open resource file '{filepath}'")
            return {}
            
        try:
            content = qfile.readAll().data().decode('utf-8')
            data = json.loads(content)
            if not isinstance(data, dict):
                print(f"ERROR: Data in resource '{filename}' is not a dictionary.")
                return {}
            return data
        except Exception as e:
            print(f"ERROR loading resource '{filename}': {e}")
            return {}
        finally:
            qfile.close()

    def load_definitions(self):
        """Loads base and DLC definitions into internal storage."""
        print("Loading base game boss definitions...")
        self._base_data = self._load_json_file(self.base_filename)
        
        print("Loading DLC boss definitions...")
        self._dlc_data = self._load_json_file(self.dlc_filename)
        
        print("Loading boss descriptions...")
        self._boss_descriptions = self._load_json_file(self.descriptions_filename)
        
        print("Loading DLC boss descriptions...")
        self._dlc_boss_descriptions = self._load_json_file(self.dlc_descriptions_filename)

        # This will be set properly by the GUI on startup
        self.boss_data_by_location = {} # Clear character-specific data
        self._active_data_template = {} # Clear the template
        
        return True, "Definitions loaded."

    def set_content_filter(self, filter_mode: str):
        """Sets the content filter ('all', 'base', 'dlc') and rebuilds the template."""
        print(f"Setting content filter to: {filter_mode}")
        self._content_filter = filter_mode
        self._rebuild_template()

    def set_type_filter(self, type_mode: str):
        """Sets the boss type filter ('all', 'no_minidungeon', 'main', 'custom')
        and rebuilds the template."""
        print(f"Setting boss type filter to: {type_mode}")
        self._type_filter = type_mode
        self._rebuild_template()

    def set_custom_preset(self, event_ids):
        """Sets the event IDs for the custom preset. Rebuilds only when the
        custom filter is active."""
        self._custom_preset_ids = {str(eid) for eid in event_ids}
        if self._type_filter == "custom":
            self._rebuild_template()

    def get_custom_preset(self):
        return set(self._custom_preset_ids)

    def get_unfiltered_locations(self):
        """Returns {location: [boss, ...]} for base + DLC data, ignoring all
        filters. Used by the custom preset dialog."""
        combined = copy.deepcopy(self._base_data)
        for location, dlc_bosses in self._dlc_data.items():
            combined.setdefault(location, []).extend(copy.deepcopy(dlc_bosses))
        return combined

    def _rebuild_template(self):
        """Builds the active template from content filter + boss type filter."""
        filter_mode = self._content_filter
        final_data = {}

        if filter_mode == "all":
            final_data = copy.deepcopy(self._base_data)
            if self._dlc_data:
                for location, dlc_bosses in self._dlc_data.items():
                    if location in final_data:
                        final_data[location].extend(dlc_bosses)
                    else:
                        final_data[location] = dlc_bosses
        elif filter_mode == "dlc":
            final_data = copy.deepcopy(self._dlc_data)
        else: # Default to "base"
            final_data = copy.deepcopy(self._base_data)

        final_data = self._apply_type_filter(final_data)

        # Store the merged data as the clean template for the current view
        self._active_data_template = self._merge_descriptions(self._merge_stats_into_boss_data(final_data))

        # The character-specific data is now stale, so we clear it.
        # It will be rebuilt when a character is loaded or statuses are updated.
        self.boss_data_by_location = {}

        self._recalculate_event_ids()
        print(f"Data template updated. Total event IDs: {len(self.all_event_ids_to_monitor)}")

    def _apply_type_filter(self, boss_data):
        """Filters bosses by the active type filter; drops empty locations."""
        mode = self._type_filter
        if mode == "all":
            return boss_data

        filtered = {}
        for location, bosses in boss_data.items():
            kept = []
            for boss_info in bosses:
                if mode == "custom":
                    event_id = boss_info.get("event_id")
                    ids = event_id if isinstance(event_id, list) else [event_id]
                    if any(str(eid) in self._custom_preset_ids for eid in ids):
                        kept.append(boss_info)
                    continue

                category = get_boss_category(boss_info)
                if mode == "no_minidungeon" and category != "minidungeon":
                    kept.append(boss_info)
                elif mode == "main" and category == "main":
                    kept.append(boss_info)
            if kept:
                filtered[location] = kept
        return filtered

    def _normalize_key(self, text: str) -> str:
        """Creates a simplified, consistent key from a string by keeping only alphanumeric characters."""
        return "".join(filter(str.isalnum, text)).lower()

    def _merge_stats_into_boss_data(self, boss_data):
        """
        Merges stats from StatsManager into the boss data using location-specific lookups.
        This ensures that bosses with the same name in different locations get the correct stats.
        """
        all_stats_by_location = self.stats_manager.get_all_stats()
        
        # Create a lookup table of normalized location keys from the stats data
        stats_location_keys = {self._normalize_key(loc): loc for loc in all_stats_by_location.keys()}

        for location_name, bosses in boss_data.items():
            norm_location_name = self._normalize_key(location_name)
            
            # Find the corresponding location key in the stats data
            matched_stats_key = stats_location_keys.get(norm_location_name)
            
            if not matched_stats_key:
                # print(f"Debug: No stats location found for '{location_name}' (Normalized: '{norm_location_name}')")
                continue

            location_stats = all_stats_by_location.get(matched_stats_key, {})
            if not location_stats:
                # print(f"Debug: Empty stats for location '{matched_stats_key}'")
                continue

            for boss_info in bosses:
                boss_name = boss_info.get("name")
                if not boss_name:
                    continue
                
                norm_boss_name = self._normalize_key(boss_name)
                
                # Find the stats using the normalized boss name within the matched location
                boss_stats = location_stats.get(norm_boss_name)
                
                if boss_stats:
                    boss_info["stats"] = boss_stats
                # else:
                    # print(f"Debug: No stats found for boss '{boss_name}' (Normalized: '{norm_boss_name}') in location '{location_name}'")

        return boss_data

    def _merge_descriptions(self, boss_data):
        """Merges descriptions from both base and DLC files into the boss data."""
        # Combine base and DLC descriptions, with DLC taking precedence
        all_descriptions = copy.deepcopy(self._boss_descriptions)
        for loc, descs in self._dlc_boss_descriptions.items():
            if loc in all_descriptions:
                all_descriptions[loc].extend(descs)
            else:
                all_descriptions[loc] = descs

        # Create a lookup table with normalized location names for robustness
        desc_location_keys = {self._normalize_key(loc): loc for loc in all_descriptions.keys()}

        for location, bosses in boss_data.items():
            norm_location = self._normalize_key(location)
            matched_desc_key = desc_location_keys.get(norm_location)

            if matched_desc_key:
                descriptions_for_location = all_descriptions[matched_desc_key]
                for boss_info in bosses:
                    boss_event_id = boss_info.get("event_id")
                    if boss_event_id is None: continue

                    # Find the first matching description entry
                    for desc_entry in descriptions_for_location:
                        # Both boss_event_id and desc_entry event_id can be single or list
                        boss_ids = set(boss_event_id if isinstance(boss_event_id, list) else [boss_event_id])
                        desc_ids = set(desc_entry.get("event_id", []) if isinstance(desc_entry.get("event_id", []), list) else [desc_entry.get("event_id")])
                        
                        # Check for any intersection between the two sets of IDs
                        if boss_ids.intersection(desc_ids):
                            boss_info["description"] = desc_entry.get("description", "")
                            break  # Stop after finding the first match
        return boss_data

    def _recalculate_event_ids(self):
        """Recalculates all event IDs based on the current `_active_data_template`."""
        all_ids = set()
        # Use the template for recalculation to ensure all possible IDs are included
        for bosses_in_location in self._active_data_template.values():
            if isinstance(bosses_in_location, list):
                for boss_info in bosses_in_location:
                    if isinstance(boss_info, dict):
                        event_id_value = boss_info.get("event_id")
                        if event_id_value is not None:
                            ids_to_add = event_id_value if isinstance(event_id_value, list) else [event_id_value]
                            for eid in ids_to_add:
                                try:
                                    all_ids.add(int(str(eid)))
                                except ValueError:
                                    print(f"Warning: Invalid event_id '{eid}' for '{boss_info.get('name')}'")
        self.all_event_ids_to_monitor = list(all_ids)

    def get_boss_data_by_location(self):
        return self.boss_data_by_location

    def get_all_event_ids_to_monitor(self):
        return self.all_event_ids_to_monitor

    def get_dlc_location_names(self):
        """Returns a list of location names that are from the DLC file."""
        if self._dlc_data:
            return self._dlc_data.keys()
        return []

    def get_all_boss_definitions(self):
        """
        Returns a flat list of all boss definition dictionaries from the active template.
        """
        all_bosses = []
        if not self._active_data_template:
            return all_bosses
        
        for bosses_in_location in self._active_data_template.values():
            if isinstance(bosses_in_location, list):
                all_bosses.extend(bosses_in_location)
        return all_bosses

    def update_boss_statuses(self, statuses_dict):
        """
        Applies the given boss statuses to a fresh copy of the data template.
        This is the correct way to generate the character-specific `boss_data_by_location`.
        """
        if not self._active_data_template:
            print("Warning: update_boss_statuses called before data template was created.")
            return False

        # Create a deep copy of the template to ensure we're not modifying the base data.
        # This is the key to ensuring a clean slate for every character update.
        self.boss_data_by_location = copy.deepcopy(self._active_data_template)

        for bosses_in_location in self.boss_data_by_location.values():
            if isinstance(bosses_in_location, list):
                for boss_info in bosses_in_location:
                    if not isinstance(boss_info, dict): continue
                    
                    # Set default defeated status to False
                    boss_info["is_defeated"] = False
                    
                    event_id_value = boss_info.get("event_id")
                    if event_id_value is None: continue
                    
                    ids_for_this_boss = [str(eid) for eid in event_id_value] if isinstance(event_id_value, list) else [str(event_id_value)]
                    
                    # If any of the boss's event IDs are marked as True in the status dict,
                    # then the boss is considered defeated.
                    if any(statuses_dict.get(eid_str) for eid_str in ids_for_this_boss):
                        boss_info["is_defeated"] = True
        return True

    def get_boss_counts(self):
        """
        Calculates detailed boss counts based on the currently filtered data.
        Returns a dictionary with counts for base, dlc, and total.
        """
        counts = {
            "base": {"defeated": 0, "total": 0, "live": 0},
            "dlc": {"defeated": 0, "total": 0, "live": 0},
            "total": {"defeated": 0, "total": 0, "live": 0}
        }
        if not self.boss_data_by_location:
            return counts

        dlc_locations = self.get_dlc_location_names()

        for loc, bosses in self.boss_data_by_location.items():
            is_dlc = loc in dlc_locations
            key = "dlc" if is_dlc else "base"
            
            for boss in bosses:
                if isinstance(boss, dict):
                    counts[key]["total"] += 1
                    counts["total"]["total"] += 1
                    if boss.get("is_defeated", False):
                        counts[key]["defeated"] += 1
                        counts["total"]["defeated"] += 1
        
        # Calculate live counts
        for key in ["base", "dlc", "total"]:
            counts[key]["live"] = counts[key]["total"] - counts[key]["defeated"]
            
        return counts

    def get_defeated_bosses_for_character(self, character_name: str):
        """
        Returns a list of defeated boss dictionaries for the current data set.
        This does not depend on the character, but on the loaded data,
        which is updated per character.
        """
        defeated_bosses = []
        if not self.boss_data_by_location:
            return defeated_bosses
        
        for bosses_in_location in self.boss_data_by_location.values():
            if isinstance(bosses_in_location, list):
                for boss in bosses_in_location:
                    if isinstance(boss, dict) and boss.get("is_defeated", False):
                        defeated_bosses.append(boss)
        return defeated_bosses

    def get_boss_name_by_id(self, boss_id_to_find: str) -> str:
        """Finds a boss's name by their event ID across all loaded data."""
        boss_id_to_find = str(boss_id_to_find) # Ensure comparison is string-to-string
        for location_data in self.boss_data_by_location.values():
            for boss_info in location_data:
                event_ids = boss_info.get("event_id", [])
                if not isinstance(event_ids, list):
                    event_ids = [event_ids]
                
                if boss_id_to_find in [str(eid) for eid in event_ids]:
                    return boss_info.get("name", "Unknown Boss")
        return "Unknown Boss"

    def get_bosses_for_location(self, location_name: str):
        """Returns a list of boss dictionaries for a specific location."""
        return self.boss_data_by_location.get(location_name, [])