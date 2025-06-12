# src/timestamp_manager.py
import os
import json

class TimestampManager:
    def __init__(self, filename="timestamps.json"):
        self.filepath = self._get_data_filepath(filename)
        self.timestamps = self._load()

    def _get_data_filepath(self, filename):
        """Constructs the full path to the data file."""
        # This places the timestamps.json file in the user's home directory
        # inside a dedicated folder, which is robust.
        app_data_dir = os.path.join(os.path.expanduser("~"), ".TheTarnishedChronicle")
        os.makedirs(app_data_dir, exist_ok=True)
        return os.path.join(app_data_dir, filename)

    def _load(self):
        """Loads timestamps from the JSON file."""
        if not os.path.exists(self.filepath):
            return {}
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading timestamps file: {e}")
            return {}

    def _save(self):
        """Saves the current timestamps to the JSON file."""
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.timestamps, f, indent=4)
        except IOError as e:
            print(f"Error saving timestamps file: {e}")

    def add_timestamp(self, character_id: str, boss_name: str, play_time_seconds: int):
        """Adds a timestamp for a defeated boss and saves the file."""
        if character_id not in self.timestamps:
            self.timestamps[character_id] = {}
        
        # Only add if it doesn't exist, to not overwrite the first kill time
        if boss_name not in self.timestamps[character_id]:
            print(f"Recording kill for '{boss_name}' at {play_time_seconds}s for char '{character_id}'")
            self.timestamps[character_id][boss_name] = play_time_seconds
            self._save()

    def get_timestamps_for_character(self, character_id: str) -> dict:
        """Gets all timestamps for a specific character."""
        return self.timestamps.get(character_id, {})