# src/gui.py
import sys
import os
import time
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QLineEdit, QCheckBox, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QTimer, QSettings

from .styles import apply_app_styles
from .overlay_window import OverlayWindow
from .overlay_manager import OverlayManager
from .ui_components import (
    create_file_slot_layout, create_main_boss_area,
    create_overlay_settings_panel_layout, LocationSectionWidget, FooterWidget,
    create_obs_panel_layout
)
from .app_config import (
    RUST_CLI_TOOL_PATH_PLACEHOLDER,
    DEFAULT_BOSS_REFERENCE_FILENAME,
    DLC_BOSS_REFERENCE_FILENAME,
    LOCATION_PROGRESSION_ORDER,
    GAME_PHASE_HEADINGS
)
from .rust_cli_handler import RustCliHandler
from .boss_data_manager import BossDataManager
from .save_monitor_logic import SaveMonitorLogic
from .obs_manager import ObsManager
from .timestamp_manager import TimestampManager

class BossChecklistApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Tarnished's Chronicle")
        self.setGeometry(150, 150, 1000, 750)

        self.settings = QSettings("TheTarnishedChronicle", "App")
        
        # UPRAVENO: Inicializujeme manažer s oběma soubory
        self.boss_data_manager = BossDataManager(
            base_filename=DEFAULT_BOSS_REFERENCE_FILENAME,
            dlc_filename=DLC_BOSS_REFERENCE_FILENAME
        )
        self.rust_cli_handler = RustCliHandler(RUST_CLI_TOOL_PATH_PLACEHOLDER)
        self.save_monitor_logic = SaveMonitorLogic(self.rust_cli_handler, self.boss_data_manager, self)
        self.last_known_stats = {}
        self.location_widgets = {}
        self.timestamp_manager = TimestampManager()
        self.last_killed_boss_info = None

        # --- NEW TIMER ATTRIBUTES ---
        # This timer will tick every second to update the UI smoothly
        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(1000) # 1 second interval

        # These will store the last known play time from the save file
        # and the real-world time we received it.
        self.last_play_time_snapshot = -1
        self.last_snapshot_real_time = -1
        self.is_game_running = False # <--- NEW STATE VARIABLE
        # --- END NEW TIMER ATTRIBUTES ---

        self.init_ui()
        
        # Load and apply saved filter settings on startup
        self.load_and_apply_filters()

        self.overlay_manager = OverlayManager(
            main_app_ref=self,
            overlay_window_ref=self.overlay_window,
            settings_panel_ref=self.overlay_settings_panel,
            text_color_button_ref=self.overlay_text_color_button,
            font_size_combobox_ref=self.overlay_font_size_combobox,
            settings_button_ref=self.overlay_settings_button,
            show_bosses_ref=self.overlay_show_bosses,
            show_deaths_ref=self.overlay_show_deaths,
            show_time_ref=self.overlay_show_time,
            show_seconds_ref=self.overlay_show_seconds,
            show_last_boss_ref=self.overlay_show_last_boss # <--- NOVÁ REFERENCE
        )
        self.obs_manager = ObsManager(
            main_app_ref=self,
            obs_panel_ref=self.obs_panel,
            settings_button_ref=self.obs_settings_button,
            enable_toggle_ref=self.obs_enable_toggle,
            folder_label_ref=self.obs_folder_path_label,
            browse_button_ref=self.obs_browse_button,
            instructions_button_ref=self.obs_instructions_button,
            bosses_enabled_ref=self.obs_bosses_enabled,
            bosses_format_ref=self.obs_bosses_format,
            deaths_enabled_ref=self.obs_deaths_enabled,
            deaths_format_ref=self.obs_deaths_format,
            time_enabled_ref=self.obs_time_enabled,
            time_format_ref=self.obs_time_format,
            last_boss_enabled_ref=self.obs_last_boss_enabled,
            last_boss_format_ref=self.obs_last_boss_format,
            obs_reset_deaths_button_ref=self.obs_reset_deaths_button,
            obs_undo_reset_button_ref=self.obs_undo_reset_button,
            character_slot_combobox_ref=self.character_slot_combobox
        )

        self._load_initial_boss_data()
        apply_app_styles(self)
        self.connect_signals()
    
    def init_ui(self):
        overall_layout = QVBoxLayout(self)
        overall_layout.setContentsMargins(0, 0, 0, 0)
        overall_layout.setSpacing(0)
        
        self.footer = FooterWidget()

        top_part_widget = QWidget()
        main_h_layout = QHBoxLayout(top_part_widget)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar")
        sidebar_frame.setFixedWidth(300)
        
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(15, 15, 15, 15)
        sidebar_layout.setSpacing(10)
        self.file_slot_layout = create_file_slot_layout(self)
        sidebar_layout.addLayout(self.file_slot_layout)
        
        sidebar_layout.addStretch()

        content_widget = QWidget()
        content_widget.setObjectName("mainContent")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 10, 15, 10)
        content_layout.setSpacing(10)
        
        self.overlay_window = OverlayWindow(self)
        
        top_buttons_layout = QHBoxLayout()
        self.toggle_overlay_button = QPushButton("Toggle Overlay")
        self.toggle_overlay_button.setCheckable(True)
        top_buttons_layout.addWidget(self.toggle_overlay_button)
        self.overlay_settings_button = QPushButton("Overlay Settings")
        top_buttons_layout.addWidget(self.overlay_settings_button)
        self.obs_settings_button = QPushButton("OBS Overlay")
        top_buttons_layout.addWidget(self.obs_settings_button)
        content_layout.addLayout(top_buttons_layout)
        
        self.overlay_settings_panel = create_overlay_settings_panel_layout(self)
        self.overlay_settings_panel.setVisible(False)
        content_layout.addWidget(self.overlay_settings_panel)
        
        self.obs_panel = create_obs_panel_layout(self)
        self.obs_panel.setVisible(False)
        content_layout.addWidget(self.obs_panel)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a boss or location...")
        content_layout.addWidget(self.search_bar)
        self.main_boss_area_widget = create_main_boss_area(self)
        content_layout.addWidget(self.main_boss_area_widget)

        main_h_layout.addWidget(sidebar_frame)
        main_h_layout.addWidget(content_widget)

        overall_layout.addWidget(top_part_widget)
        overall_layout.addWidget(self.footer)
        self.setLayout(overall_layout)
        
        saved_path = self.settings.value("saveFilePath", "")
        self.save_file_path_label.setText(saved_path or "Please select a save file...")
        if os.path.exists(saved_path):
            self.on_save_file_path_changed(saved_path)

    def connect_signals(self):
        self.save_monitor_logic.monitoring_started.connect(self._handle_monitoring_started)
        self.save_monitor_logic.monitoring_stopped.connect(self._handle_monitoring_stopped)
        self.save_monitor_logic.stats_updated.connect(self.handle_stats_update)
        
        self.browse_button.clicked.connect(self.browse_for_save_file)
        self.character_slot_combobox.currentIndexChanged.connect(self.handle_character_selection_change)
        self.character_slot_combobox.currentIndexChanged.connect(self.obs_manager.on_character_changed)
        
        # --- NEW/MODIFIED SIGNAL CONNECTIONS ---
        self.content_filter_combobox.currentIndexChanged.connect(self.handle_content_filter_change)
        self.hide_defeated_checkbox.stateChanged.connect(self.handle_status_filter_change)
        # --- END NEW/MODIFIED ---
        
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        
        self.toggle_overlay_button.toggled.connect(self.overlay_manager.on_toggle_overlay)
        self.overlay_settings_button.clicked.connect(self.toggle_overlay_settings)
        self.obs_settings_button.clicked.connect(self.toggle_obs_settings)


        # --- NEW SIGNAL CONNECTION ---
        self.ui_timer.timeout.connect(self.update_live_timer)
        # --- END NEW ---

        # Connect to the new signal from the monitor
        self.save_monitor_logic.boss_defeated.connect(self.on_boss_defeated)
        self.save_monitor_logic.game_process_status.connect(self.on_game_process_status_changed) # <--- NEW CONNECTION

    def load_and_apply_filters(self):
        """Loads filter settings from QSettings and applies them to the UI controls."""
        # Content Filter
        saved_filter_mode = self.settings.value("filters/contentMode", "all", type=str)
        index = self.content_filter_combobox.findData(saved_filter_mode)
        if index != -1:
            self.content_filter_combobox.setCurrentIndex(index)
        
        # Hide Defeated Filter
        hide_defeated = self.settings.value("filters/hideDefeated", False, type=bool)
        self.hide_defeated_checkbox.setChecked(hide_defeated)

    def _load_initial_boss_data(self):
        """Loads definitions and sets the content filter based on the UI control."""
        self.boss_data_manager.load_definitions()
        # Set the initial data source based on the already-set combobox
        current_filter_mode = self.content_filter_combobox.currentData()
        self.boss_data_manager.set_content_filter(current_filter_mode)
        self.update_main_boss_area(clear=True)
    
    def handle_content_filter_change(self):
        """Handles changes to the Content Filter (Base/DLC/All)."""
        filter_mode = self.content_filter_combobox.currentData()
        print(f"Content filter changed to: {filter_mode}")
        
        # Save the setting
        self.settings.setValue("filters/contentMode", filter_mode)
        
        # Tell the data manager to update its data source
        self.boss_data_manager.set_content_filter(filter_mode)
        
        # Trigger a full refresh for the current character
        current_index = self.character_slot_combobox.currentIndex()
        if current_index > 0:
            self.handle_character_selection_change(current_index)
        else:
            self.update_main_boss_area() # Rebuild the empty UI

    def handle_status_filter_change(self):
        """Handles the 'Hide Defeated Bosses' checkbox."""
        is_checked = self.hide_defeated_checkbox.isChecked()
        print(f"Hide defeated filter changed to: {is_checked}")
        
        # Save the setting
        self.settings.setValue("filters/hideDefeated", is_checked)
        
        # Apply the filter visually without reloading all data
        for section_widget in self.location_widgets.values():
            section_widget.apply_status_filter(is_checked)
        
    def on_game_process_status_changed(self, is_running: bool):
        """Starts or stops the smooth UI timer based on game process status."""
        self.is_game_running = is_running
        if is_running:
            print("Game process detected. Starting UI timer.")
            # When resuming, reset the real-time marker to now
            self.last_snapshot_real_time = time.time()
            self.ui_timer.start()
        else:
            print("Game process stopped. Stopping UI timer.")
            # When pausing, update the snapshot with the time that just elapsed
            if self.last_play_time_snapshot > 0 and self.last_snapshot_real_time > 0:
                elapsed = time.time() - self.last_snapshot_real_time
                self.last_play_time_snapshot += elapsed
            self.ui_timer.stop()
            
    def stop_ui_timer(self):
        """Stops the UI timer and resets time snapshots."""
        if self.ui_timer.isActive():
            self.ui_timer.stop()
        self.last_play_time_snapshot = -1
        self.last_snapshot_real_time = -1
        self.is_game_running = False # <--- ADD THIS
        self.footer.update_time(-1)
        self.overlay_manager.update_text(self._get_current_stats_payload())

    def update_live_timer(self):
        """
        This slot is called every second to create a smooth ticking timer.
        """
        if self.last_play_time_snapshot < 0:
            return

        # Calculate the real-world seconds passed since our last data snapshot
        real_time_elapsed = time.time() - self.last_snapshot_real_time
        
        # Calculate the new, live play time
        live_play_time = self.last_play_time_snapshot + real_time_elapsed
        
        # Update the UI components
        self.footer.update_time(int(live_play_time))
        
        # Update overlay if it's visible
        if self.overlay_manager.overlay_window.isVisible():
            stats = self.last_known_stats.get("stats", {}).copy()
            stats['seconds_played'] = int(live_play_time)
            # Create a temporary payload for the overlay to prevent modifying the main one
            temp_payload = self.last_known_stats.copy()
            temp_payload['stats'] = stats
            self.overlay_manager.update_text(temp_payload)

    def _handle_monitoring_started(self, char_name, interval):
        self.footer.update_monitoring_status(True, text=f"Monitoring: {char_name}")

    def _handle_monitoring_stopped(self):
        self.footer.update_monitoring_status(False)

    def handle_stats_update(self, data: dict):
        """
        OPRAVENÁ VERZE: Zpracuje nová data, sjednotí je a aktualizuje celé UI najednou.
        """
        stats_from_rust = data.get("stats", {})
        boss_statuses = data.get("boss_statuses", {})

        self.boss_data_manager.update_boss_statuses(boss_statuses)
        defeated_count, total_count = self.boss_data_manager.get_boss_counts()

        final_stats_payload = stats_from_rust.copy()
        final_stats_payload['defeated'] = defeated_count
        final_stats_payload['total'] = total_count

        # --- TIMER LOGIC MODIFICATION ---
        # When we get fresh data, update our snapshots
        self.last_play_time_snapshot = final_stats_payload.get('seconds_played', -1)
        self.last_snapshot_real_time = time.time()
        # Start the timer ONLY if the game is already running
        if self.is_game_running and not self.ui_timer.isActive():
            self.ui_timer.start()
        # --- END TIMER LOGIC ---
        
        # Přidáme informaci o posledním zabití do celkového balíčku dat
        self.last_known_stats = {
            "stats": final_stats_payload,
            "boss_statuses": boss_statuses,
            "last_kill": self.last_killed_boss_info # <--- PŘIDÁNO
        }
        
        # This will now update the timer to the snapshot value instantly
        self.footer.update_stats(final_stats_payload)
        self.overlay_manager.update_text(self.last_known_stats)
        self.obs_manager.update_obs_files(self.last_known_stats)
        
        self.update_main_boss_area()

    def handle_character_selection_change(self, index):
        self.save_monitor_logic.stop_monitoring()
        selected_data = self.character_slot_combobox.itemData(index)
        
        if index == 0 or selected_data is None:
            self.stop_ui_timer()
            self.last_killed_boss_info = None # <--- Resetujeme při odhlášení postavy
            self.footer.update_monitoring_status(False)
            self.footer.update_stats({})
            self.update_main_boss_area(clear=True)
            self.overlay_manager.update_text({})
            return
        
        self.settings.setValue("lastCharacterIndex", index)
        
        save_file_path = self.save_file_path_label.text()
        slot_index = selected_data["slot_index"]
        all_event_ids = self.boss_data_manager.get_all_event_ids_to_monitor()
        
        initial_data, err = self.rust_cli_handler.get_full_status(save_file_path, slot_index, all_event_ids)

        if err or not initial_data:
            print(f"Failed to get initial status: {err}")
            return
            
        # --- PŘIDÁNO: Zjištění posledního zabitého bosse pro načtenou postavu ---
        char_name = selected_data.get("character_name")
        all_timestamps = self.timestamp_manager.get_timestamps_for_character(char_name)
        if all_timestamps:
            # Najdeme bosse s nejvyšší (poslední) časovou značkou
            last_boss_name = max(all_timestamps, key=all_timestamps.get)
            last_boss_time = all_timestamps[last_boss_name]
            self.last_killed_boss_info = {"name": last_boss_name, "time": last_boss_time}
        else:
            self.last_killed_boss_info = None
        # --- KONEC PŘIDANÉ ČÁSTI ---
            
        self.handle_stats_update(initial_data)
        
        self.save_monitor_logic.start_monitoring(
            save_file_path,
            slot_index,
            selected_data["character_name"]
        )

    def force_stats_update_for_obs(self):
       """Forces a manual recalculation and pushes the latest data to OBS files."""
       if self.last_known_stats:
           self.obs_manager.update_obs_files(self.last_known_stats)

    def on_boss_defeated(self, boss_event_id: str, play_time: int):
        """Slot to handle a newly defeated boss."""
        # We need to find which boss corresponds to this event ID
        all_boss_data = self.boss_data_manager.get_boss_data_by_location()
        # --- FIX IS HERE ---
        # The key is 'character_name', not 'character_id'
        character_name = self.character_slot_combobox.currentData().get("character_name")

        if not character_name:
            return

        for location, bosses in all_boss_data.items():
            for boss_info in bosses:
                event_ids = boss_info.get("event_id", [])
                if not isinstance(event_ids, list):
                    event_ids = [event_ids]
                
                if str(boss_event_id) in [str(eid) for eid in event_ids]:
                    boss_name = boss_info.get("name")
                    self.timestamp_manager.add_timestamp(character_name, boss_name, play_time)
                    
                    # --- PŘIDÁNO: Aktualizujeme informaci o posledním zabití ---
                    self.last_killed_boss_info = {"name": boss_name, "time": play_time}
                    print(f"New last killed boss: {self.last_killed_boss_info}")
                    # --- KONEC PŘIDANÉ ČÁSTI ---
                    
                    return # Exit once found

    def update_main_boss_area(self, clear: bool = False):
        # --- PRESERVE EXPANDED STATE ---
        expanded_states = {
            name: widget.is_expanded
            for name, widget in self.location_widgets.items()
        }
        
        # ... (The robust clearing logic remains the same) ...
        layout = self.main_boss_area_widget.widget().layout()
        while layout.count() > 1:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.location_widgets.clear()
        # ...

        if clear:
            self.footer.update_stats({})
            return
        
        # ... (The logic for getting and sorting boss data remains the same) ...
        boss_data = self.boss_data_manager.get_boss_data_by_location()
        if not boss_data: return
        dlc_location_names = self.boss_data_manager.get_dlc_location_names()
        
        base_game_items = []
        dlc_items = []
        for loc, bosses in boss_data.items():
            if loc in dlc_location_names:
                dlc_items.append((loc, bosses))
            else:
                base_game_items.append((loc, bosses))

        order_map = {location: i for i, location in enumerate(LOCATION_PROGRESSION_ORDER)}
        sorted_base_game_items = sorted(base_game_items, key=lambda item: (order_map.get(item[0], float('inf')), item[0]))
        sorted_dlc_items = sorted(dlc_items, key=lambda item: item[0])

        # --- FIX IS HERE ---
        # When retrieving timestamps, we must use the SAME key we used for saving: 'character_name'
        character_name = self.character_slot_combobox.currentData().get("character_name") if self.character_slot_combobox.currentIndex() > 0 else None
        char_timestamps = self.timestamp_manager.get_timestamps_for_character(character_name) if character_name else {}
        # --- END FIX ---
        
        def enrich_boss_list(bosses_list):
            for boss in bosses_list:
                boss['timestamp'] = char_timestamps.get(boss.get('name'))
            return bosses_list

        # --- UI Building Phase ---
        # (This entire section is almost the same, we just add one line)
        
        # 1. Add all base game widgets
        for location_name, bosses_list in sorted_base_game_items:
            # ... (header logic is unchanged)
            if location_name in GAME_PHASE_HEADINGS:
                header_data = GAME_PHASE_HEADINGS[location_name]
                header_label = QLabel(header_data["text"])
                header_label.setObjectName("gamePhaseHeader")
                header_label.setAlignment(Qt.AlignCenter)
                header_label.setProperty("phase", header_data["property"])
                layout.insertWidget(layout.count() - 1, header_label)
            section = LocationSectionWidget(location_name, enrich_boss_list(bosses_list), self.main_boss_area_widget.widget())
            layout.insertWidget(layout.count() - 1, section)
            self.location_widgets[location_name] = section
            # --- RESTORE STATE ---
            if expanded_states.get(location_name):
                section.set_expanded(True)

        # 2. Add the DLC section
        current_filter_mode = self.content_filter_combobox.currentData()
        if current_filter_mode in ["all", "dlc"] and sorted_dlc_items:
            # ... (dlc header logic)
            dlc_header_data = GAME_PHASE_HEADINGS['dlc_header']
            dlc_header_label = QLabel(dlc_header_data["text"])
            dlc_header_label.setObjectName("gamePhaseHeader")
            dlc_header_label.setAlignment(Qt.AlignCenter)
            dlc_header_label.setProperty("phase", dlc_header_data["property"])
            layout.insertWidget(layout.count() - 1, dlc_header_label)
            for location_name, bosses_list in sorted_dlc_items:
                section = LocationSectionWidget(location_name, enrich_boss_list(bosses_list), self.main_boss_area_widget.widget())
                layout.insertWidget(layout.count() - 1, section)
                self.location_widgets[location_name] = section
                # --- RESTORE STATE ---
                if expanded_states.get(location_name):
                    section.set_expanded(True)

        self.handle_status_filter_change()
        
    def on_save_file_path_changed(self, new_path):
        self.save_monitor_logic.stop_monitoring()
        if os.path.exists(new_path) and os.path.isfile(new_path):
            self._load_characters_for_save_file(new_path)
        else:
            self.character_slot_combobox.clear()
            self.character_slot_combobox.setEnabled(False)

    def _load_characters_for_save_file(self, save_file_path):
        self.character_slot_combobox.blockSignals(True)
        self.character_slot_combobox.clear()
        self.character_slot_combobox.setEnabled(False)
        self.character_slot_combobox.addItem("Select Character...", userData=None)
        
        characters_data, _ = self.rust_cli_handler.list_characters(save_file_path)
        if not characters_data:
            self.character_slot_combobox.blockSignals(False)
            return
            
        for char_info in characters_data:
            if char_info.get("character_name"):
                display_name = f"{char_info['character_name']} (Level {char_info['character_level']})"
                self.character_slot_combobox.addItem(display_name, userData=char_info)
        
        self.character_slot_combobox.setEnabled(True)
        
        last_index = self.settings.value("lastCharacterIndex", 0, type=int)
        if not (0 <= last_index < self.character_slot_combobox.count()):
            last_index = 0
        self.character_slot_combobox.setCurrentIndex(last_index)
        self.character_slot_combobox.blockSignals(False)

        if last_index > 0:
            QTimer.singleShot(0, lambda: self.handle_character_selection_change(last_index))

    def browse_for_save_file(self):
        current_path = self.save_file_path_label.text()
        start_dir = os.path.dirname(current_path) if os.path.isdir(current_path) else ""
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Elden Ring Save File", start_dir, "SL2 Files (*.sl2)")
        if filepath:
            self.save_file_path_label.setText(filepath)
            self.settings.setValue("saveFilePath", filepath)
            self.on_save_file_path_changed(filepath)

    def on_search_text_changed(self, text):
        search_term = text.lower().strip()
        for section in self.location_widgets.values():
            location_matches = search_term in section.location_name.lower()
            boss_matches = any(search_term in b.get("name", "").lower() for b in section.bosses_data)
            section.setVisible(location_matches or boss_matches or not search_term)

    def _get_current_stats_payload(self) -> dict:
        return self.last_known_stats or {
            "stats": {"deaths": "--", "seconds_played": -1},
            "boss_statuses": {}
        }

    def toggle_overlay_settings(self):
        """Toggles the visibility of the overlay settings panel, ensuring the OBS panel is hidden."""
        # Hide the other panel first
        if self.obs_panel.isVisible():
            self.obs_panel.setVisible(False)
            self.obs_settings_button.setText("OBS Settings")

        # Toggle the desired panel
        is_visible = not self.overlay_settings_panel.isVisible()
        self.overlay_settings_panel.setVisible(is_visible)
        self.overlay_settings_button.setText("Hide Overlay Settings" if is_visible else "Overlay Settings")

    def toggle_obs_settings(self):
        """Toggles the visibility of the OBS settings panel, ensuring the overlay panel is hidden."""
        # Hide the other panel first
        if self.overlay_settings_panel.isVisible():
            self.overlay_settings_panel.setVisible(False)
            self.overlay_settings_button.setText("Overlay Settings")

        # Toggle the desired panel
        is_visible = not self.obs_panel.isVisible()
        self.obs_panel.setVisible(is_visible)
        self.obs_settings_button.setText("Hide OBS Settings" if is_visible else "OBS Settings")

def main():
    app = QApplication(sys.argv)
    window = BossChecklistApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()