# Finální verze souboru: src/boss_data_manager.py
import os
import json

class BossDataManager:
    def __init__(self, reference_json_filename="boss_ids_reference.json"):
        self.reference_json_filename = reference_json_filename
        self.boss_data_by_location = {}
        self.all_event_ids_to_monitor = []

    def _get_reference_data_path(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            return os.path.join(project_root, "data", "Bosses", self.reference_json_filename)
        except Exception as e:
            print(f"ERROR preparing path to reference JSON: {e}")
            return None

    def load_reference_boss_definitions(self):
        filepath = self._get_reference_data_path()
        if not filepath:
            return False, "Could not determine reference data path."
        print(f"Loading reference definitions from: {os.path.basename(filepath)}...")
        try:
            if not os.path.exists(filepath):
                return False, f"ERROR: Reference file '{os.path.basename(filepath)}' not found."
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return False, f"ERROR in format of {os.path.basename(filepath)}: Expected a dictionary."
            all_ids = set()
            for bosses_in_location in data.values():
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
            self.boss_data_by_location = data
            success_message = f"Loaded {len(self.all_event_ids_to_monitor)} unique Event IDs."
            print(success_message)
            return True, success_message
        except Exception as e:
            return False, f"ERROR loading reference definitions: {e}"

    def get_boss_data_by_location(self):
        return self.boss_data_by_location

    def get_all_event_ids_to_monitor(self):
        return self.all_event_ids_to_monitor

    def update_boss_statuses(self, statuses_dict):
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