# src/save_monitor_logic.py
import os
from PySide6.QtCore import QObject, Signal, QTimer # QObject and Signal for potential future enhancements
from .rust_cli_handler import RustCliHandler
from .boss_data_manager import BossDataManager
from .app_config import DEFAULT_MONITORING_INTERVAL_SEC, DEFAULT_BOSS_REFERENCE_FILENAME

class SaveMonitorLogic(QObject):
    # Signals for more decoupled communication if needed in the future
    monitoring_started = Signal(str, int) # char_name, interval
    monitoring_stopped = Signal()
    status_updated = Signal(str, str) # message, style
    boss_statuses_changed = Signal(dict) # new_statuses
    initial_boss_statuses_loaded = Signal(dict) # initial_statuses

    def __init__(self, rust_cli_handler: RustCliHandler, boss_data_manager: BossDataManager, parent=None):
        super().__init__(parent)
        self.rust_cli = rust_cli_handler
        self.boss_data_manager = boss_data_manager
        
        self.monitoring_timer = QTimer(self)
        self.monitoring_timer.timeout.connect(self.on_monitoring_timeout)
        self.monitoring_interval_sec = DEFAULT_MONITORING_INTERVAL_SEC
        
        self.current_save_file_path = ""
        self.current_slot_index = 0
        self.current_character_name = ""
        self.current_boss_statuses = {} # Stores {event_id_str: bool}

    def set_monitoring_interval(self, seconds: int):
        self.monitoring_interval_sec = seconds
        if self.monitoring_timer.isActive():
            self.monitoring_timer.start(self.monitoring_interval_sec * 1000)
            self.status_updated.emit(f"Monitoring interval updated to {self.monitoring_interval_sec}s.", "blue")

    def start_monitoring(self, save_file_path: str, slot_index: int, character_name: str):
        self.stop_monitoring() # Ensure any previous monitoring is stopped

        self.current_save_file_path = save_file_path
        self.current_slot_index = slot_index
        self.current_character_name = character_name

        if not self.current_save_file_path or not os.path.exists(self.current_save_file_path):
            self.status_updated.emit("ERROR: Invalid save file path for monitoring.", "red")
            return False

        if not self.rust_cli.is_cli_available():
            self.status_updated.emit(f"ERROR: Rust CLI tool not found at: {self.rust_cli.cli_path}", "red")
            return False

        # Ensure boss definitions are loaded
        if not self.boss_data_manager.get_all_event_ids_to_monitor():
            loaded, msg = self.boss_data_manager.load_reference_boss_definitions()
            if not loaded:
                self.status_updated.emit(f"ERROR: Cannot start monitoring, failed to load boss definitions: {msg}", "red")
                return False
        
        all_event_ids = self.boss_data_manager.get_all_event_ids_to_monitor()
        if not all_event_ids:
            self.status_updated.emit("ERROR: No Event IDs defined for monitoring.", "red")
            return False

        # Perform initial scan
        initial_statuses, error_msg = self.rust_cli.get_event_flags(
            self.current_save_file_path,
            self.current_slot_index,
            all_event_ids
        )

        if error_msg or initial_statuses is None: # Check both error_msg and if initial_statuses is None
            self.status_updated.emit(f"ERROR: Initial save file scan failed. {error_msg or ''}", "red")
            return False
        
        self.current_boss_statuses = initial_statuses
        self.initial_boss_statuses_loaded.emit(self.current_boss_statuses) # Emit initial statuses

        self.monitoring_timer.start(self.monitoring_interval_sec * 1000)
        self.monitoring_started.emit(self.current_character_name, self.monitoring_interval_sec)
        self.status_updated.emit(f"Monitoring active: {self.current_character_name}", "blue")
        return True

    def stop_monitoring(self):
        if self.monitoring_timer.isActive():
            self.monitoring_timer.stop()
            self.monitoring_stopped.emit()
            self.status_updated.emit("Monitoring stopped.", "orange")
            # Reset monitoring-specific state if desired
            # self.current_save_file_path = ""
            # self.current_slot_index = 0
            # self.current_character_name = ""
            # self.current_boss_statuses = {}

    def on_monitoring_timeout(self):
        if not self.current_save_file_path or not self.monitoring_timer.isActive():
            return

        all_event_ids = self.boss_data_manager.get_all_event_ids_to_monitor()
        if not all_event_ids:
            self.status_updated.emit("ERROR: No Event IDs for monitoring during timeout.", "red")
            self.stop_monitoring() # Stop if configuration is bad
            return

        new_statuses, error_msg = self.rust_cli.get_event_flags(
            self.current_save_file_path,
            self.current_slot_index,
            all_event_ids
        )

        if error_msg or new_statuses is None:
            self.status_updated.emit(f"ERROR: Save file scan failed during monitoring. {error_msg or ''}", "red")
            # Optionally stop monitoring on repeated errors, or implement a retry mechanism
            return

        changes_found = False
        for event_id_str, new_status_bool in new_statuses.items():
            if self.current_boss_statuses.get(event_id_str) != new_status_bool:
                changes_found = True
                break
        
        if changes_found:
            self.status_updated.emit("Change detected! Updating boss statuses...", "green")
            self.current_boss_statuses = new_statuses
            self.boss_statuses_changed.emit(self.current_boss_statuses) # Emit new statuses
            
         
        else:
            pass # print(f"No changes detected for {self.current_character_name}")

    def is_monitoring_active(self):
        return self.monitoring_timer.isActive()