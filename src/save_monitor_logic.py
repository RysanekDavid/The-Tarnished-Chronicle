# src/save_monitor_logic.py
import os
import time
import json
import psutil # <--- NEW IMPORT
from PySide6.QtCore import QObject, Signal, QTimer
from .rust_cli_handler import RustCliHandler
from .boss_data_manager import BossDataManager
from .app_config import DEFAULT_MONITORING_INTERVAL_SEC

class SaveMonitorLogic(QObject):
    monitoring_started = Signal(str, int)
    monitoring_stopped = Signal()
    stats_updated = Signal(dict)
    boss_defeated = Signal(str, int)
    game_process_status = Signal(bool) # <--- NEW SIGNAL (is_running)
    
    def __init__(self, rust_cli_handler: RustCliHandler, boss_data_manager: BossDataManager, parent=None):
        super().__init__(parent)
        self.rust_cli = rust_cli_handler
        self.boss_data_manager = boss_data_manager
        
        self.monitoring_timer = QTimer(self)
        self.monitoring_timer.timeout.connect(self.on_monitoring_timeout)
        self.monitoring_interval_sec = DEFAULT_MONITORING_INTERVAL_SEC
        
        self.current_save_file_path = ""
        self.current_slot_index = -1
        self.last_known_data = None
        self.game_process_is_running = False # <--- NEW STATE VARIABLE

    def _is_game_running(self):
        """Checks if eldenring.exe is a running process."""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'].lower() == "eldenring.exe":
                return True
        return False

    def start_monitoring(self, save_file_path: str, slot_index: int, character_name: str):
        self.stop_monitoring()
        self.current_save_file_path = save_file_path
        self.current_slot_index = slot_index
        
        self.on_monitoring_timeout()
        
        self.monitoring_timer.start(self.monitoring_interval_sec * 1000)
        self.monitoring_started.emit(character_name, self.monitoring_interval_sec)

    def stop_monitoring(self):
        if self.monitoring_timer.isActive():
            self.monitoring_timer.stop()
            self.current_slot_index = -1
            self.last_known_data = None
            self.monitoring_stopped.emit()

    def on_monitoring_timeout(self):
        """Loads full data from the file and compares it."""
        # --- NEW PROCESS CHECK ---
        is_running = self._is_game_running()
        if is_running != self.game_process_is_running:
            self.game_process_is_running = is_running
            self.game_process_status.emit(is_running)
        
        # If the game isn't running, we don't need to read the save file
        if not is_running:
            return
        # --- END NEW PROCESS CHECK ---

        if self.current_slot_index == -1:
            return

        all_event_ids = self.boss_data_manager.get_all_event_ids_to_monitor()
        if not all_event_ids:
            return

        new_data, err = self.rust_cli.get_full_status(
            self.current_save_file_path,
            self.current_slot_index,
            all_event_ids
        )

        if err or new_data is None:
            print(f"Monitoring Error: {err or 'No data returned'}")
            return

        # Check for newly defeated bosses before emitting the general update
        if self.last_known_data:
            old_statuses = self.last_known_data.get("boss_statuses", {})
            new_statuses = new_data.get("boss_statuses", {})
            current_play_time = new_data.get("stats", {}).get("seconds_played", 0)

            for boss_id, is_defeated in new_statuses.items():
                # If the boss is now defeated but wasn't before
                if is_defeated and not old_statuses.get(boss_id, False):
                    # We need to find the boss name from its ID.
                    # This is a bit tricky here. We will emit the ID and let the GUI find the name.
                    self.boss_defeated.emit(boss_id, current_play_time)

        # --- ROBUST COMPARISON FIX ---
        # Convert dictionaries to sorted JSON strings for a reliable, order-independent comparison.
        new_data_str = json.dumps(new_data, sort_keys=True)
        last_data_str = json.dumps(self.last_known_data, sort_keys=True) if self.last_known_data else ""

        if new_data_str != last_data_str:
            print("Change detected in save data. Emitting update.")
            self.last_known_data = new_data
            self.stats_updated.emit(new_data)