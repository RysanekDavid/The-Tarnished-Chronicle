# src/achievement_manager.py

import json
from PySide6.QtCore import QSettings

class AchievementManager:
    def __init__(self, achievements_file):
        self.achievements_file = achievements_file
        self.achievements = self._load_achievements()
        self.settings = QSettings("TheTarnishedChronicle", "App")

    def _load_achievements(self):
        """Loads achievement definitions from the JSON file."""
        try:
            with open(self.achievements_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("achievements", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading achievements file: {e}")
            return []

    def get_all_achievements(self):
        """Returns the list of all available achievements."""
        return self.achievements

    def get_unlocked_achievements(self, character_name):
        """
        Gets the set of unlocked achievement names for a specific character.
        """
        if not character_name:
            return set()
        
        self.settings.beginGroup(f"achievements/{character_name}")
        unlocked = self.settings.value("unlocked", [], type=list)
        self.settings.endGroup()
        return set(unlocked)

    def _save_unlocked_achievements(self, character_name, unlocked_set):
        """
        Saves the set of unlocked achievement names for a specific character.
        """
        if not character_name:
            return
            
        self.settings.beginGroup(f"achievements/{character_name}")
        self.settings.setValue("unlocked", list(unlocked_set))
        self.settings.endGroup()

    def check_and_update_achievements(self, character_name, defeated_bosses):
        """
        Checks for newly unlocked achievements and updates the character's record.
        Returns a list of newly unlocked achievements.
        """
        if not character_name:
            return []

        unlocked_achievements = self.get_unlocked_achievements(character_name)
        newly_unlocked = []
        
        defeated_boss_names = {boss['name'] for boss in defeated_bosses}

        for achievement in self.achievements:
            name = achievement.get("name")
            required_bosses = set(achievement.get("bosses", []))
            
            if name in unlocked_achievements:
                continue

            if required_bosses.issubset(defeated_boss_names):
                unlocked_achievements.add(name)
                newly_unlocked.append(achievement)

        if newly_unlocked:
            self._save_unlocked_achievements(character_name, unlocked_achievements)
            
        return newly_unlocked