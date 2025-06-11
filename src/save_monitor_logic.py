# src/save_monitor_logic.py
import os
import time
from PySide6.QtCore import QObject, Signal, QTimer
from .rust_cli_handler import RustCliHandler
from .boss_data_manager import BossDataManager
from .app_config import DEFAULT_MONITORING_INTERVAL_SEC

class SaveMonitorLogic(QObject):
    monitoring_started = Signal(str, int)
    monitoring_stopped = Signal()
    stats_updated = Signal(dict)
    
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
        """Načte kompletní data ze souboru jedním voláním a porovná je."""
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

        if new_data != self.last_known_data:
            self.last_known_data = new_data
            self.stats_updated.emit(new_data)