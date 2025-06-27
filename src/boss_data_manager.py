# src/boss_data_manager.py
import os
import json
import copy

class BossDataManager:
    def __init__(self, base_filename="boss_ids_reference.json", dlc_filename="boss_ids_reference_DLC.json"):
        self.base_filename = base_filename
        self.dlc_filename = dlc_filename
        
        # Interní úložiště pro nesloučená data
        self._base_data = {}
        self._dlc_data = {}
        
        # Veřejná data, se kterými pracuje zbytek aplikace
        self.boss_data_by_location = {}
        self.all_event_ids_to_monitor = []
        

    def _get_reference_data_path(self, filename):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            return os.path.join(project_root, "data", "Bosses", filename)
        except Exception as e:
            print(f"ERROR preparing path to reference JSON '{filename}': {e}")
            return None

    def _load_json_file(self, filename):
        """Pomocná metoda pro načtení a validaci jednoho JSON souboru."""
        filepath = self._get_reference_data_path(filename)
        if not (filepath and os.path.exists(filepath)):
            print(f"Warning: Data file '{filename}' not found.")
            return {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                print(f"ERROR: Data in '{filename}' is not a dictionary.")
                return {}
            return data
        except Exception as e:
            print(f"ERROR loading '{filename}': {e}")
            return {}

    def load_definitions(self):
        """Loads base and DLC definitions into internal storage."""
        print("Loading base game boss definitions...")
        self._base_data = self._load_json_file(self.base_filename)
        
        print("Loading DLC boss definitions...")
        self._dlc_data = self._load_json_file(self.dlc_filename)
        
        # This will be set properly by the GUI on startup
        self.boss_data_by_location = {}
        
        return True, "Definitions loaded."

    def set_content_filter(self, filter_mode: str):
        """
        Builds the final boss data based on the selected filter mode ('all', 'base', 'dlc').
        This replaces the old set_dlc_inclusion method.
        """
        print(f"Setting content filter to: {filter_mode}")
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
        
        self.boss_data_by_location = final_data
        self._recalculate_event_ids()
        print(f"Data source updated. Total event IDs: {len(self.all_event_ids_to_monitor)}")

    def _recalculate_event_ids(self):
        """Přepočítá všechny event ID na základě aktuálního `boss_data_by_location`."""
        all_ids = set()
        for bosses_in_location in self.boss_data_by_location.values():
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

    def update_boss_statuses(self, statuses_dict):
        # Tato metoda zůstává beze změny, pracuje s aktuálními daty
        if not self.boss_data_by_location:
            return False
        for bosses_in_location in self.boss_data_by_location.values():
            if isinstance(bosses_in_location, list):
                for boss_info in bosses_in_location:
                    if not isinstance(boss_info, dict): continue
                    event_id_value = boss_info.get("event_id")
                    if event_id_value is None: continue
                    ids_for_this_boss = [str(eid) for eid in event_id_value] if isinstance(event_id_value, list) else [str(event_id_value)]
                    boss_info["is_defeated"] = any(statuses_dict.get(eid_str) for eid_str in ids_for_this_boss)
        return True

    def get_boss_counts(self):
        # Tato metoda zůstává beze změny
        defeated = 0
        total = 0
        if not self.boss_data_by_location:
            return defeated, total
        for bosses_in_location in self.boss_data_by_location.values():
            if isinstance(bosses_in_location, list):
                for boss in bosses_in_location:
                    if isinstance(boss, dict):
                        total += 1
                        if boss.get("is_defeated", False):
                            defeated += 1
        return defeated, total

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