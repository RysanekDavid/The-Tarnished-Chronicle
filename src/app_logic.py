# src/app_logic.py

import os
import json
import time
import hashlib
import tempfile
import subprocess
import requests
import threading
import ctypes
from PySide6.QtWidgets import QFileDialog, QMessageBox, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer, QMetaObject, Q_ARG, Signal, QObject
from .ui.widgets.location_section import LocationSectionWidget
from .ui.dialogs.boss_stats_dialog import BossStatsDialog
from .ui.dialogs.location_dialog import LocationDialog
from .config.app_config import LOCATION_PROGRESSION_ORDER, GAME_PHASE_HEADINGS

class AppLogic:
    def __init__(self, app):
        self.app = app
        self.last_known_stats = {}
        self.last_killed_boss_info = None
        self.is_game_running = False
        self.last_play_time_snapshot = -1
        self.last_snapshot_real_time = -1
        self._actual_save_file_path = ""  # Store the real path without UI decorations
        # Expansion state of location sections, keyed by location name.
        # Loaded lazily from QSettings (self.app.settings does not exist yet here).
        self._expansion_states = None

    def browse_for_save_file(self):
        """Opens a file dialog to select the Elden Ring save file with improved logic."""
        start_dir = ""
        # Use the actual file path if available, otherwise try to extract from display text
        current_path = self._actual_save_file_path if self._actual_save_file_path else self.app.save_file_path_label.text()
        
        # 1. If a path is already selected, start there.
        if current_path and os.path.exists(os.path.dirname(current_path)):
            start_dir = os.path.dirname(current_path)
        else:
            # 2. If not, try the default Elden Ring save location.
            appdata_path = os.getenv('APPDATA')
            if appdata_path:
                elden_ring_path = os.path.join(appdata_path, 'EldenRing')
                if os.path.isdir(elden_ring_path):
                    start_dir = elden_ring_path
                else:
                    # 3. Fallback to the user's home directory.
                    start_dir = os.path.expanduser("~")
            else:
                start_dir = os.path.expanduser("~")

        file_path, _ = QFileDialog.getOpenFileName(
            parent=self.app,
            caption="Select Elden Ring Save File",
            dir=start_dir,
            filter="Elden Ring Save Files (*.sl2 *.co2);;Vanilla Save (*.sl2);;Seamless Coop Save (*.co2)"
        )
        if file_path:
            self.on_save_file_path_changed(file_path)

    def on_save_file_path_changed(self, new_path):
        """Handles the event when a new save file path is selected."""
        # Detect if this is a Seamless Coop save file
        is_seamless_coop = new_path.lower().endswith('.co2')
        
        # First load characters to check if the file is valid
        self._actual_save_file_path = new_path  # Store the actual path
        success = self._load_characters_for_save_file(new_path)
        
        if success:
            # Update the path display with mode indicator
            if is_seamless_coop:
                display_path = f"🔗 {new_path} (Seamless Coop)"
            else:
                display_path = f"⚔️ {new_path} (Vanilla)"
            
            self.app.save_file_path_label.setText(display_path)
            self.app.settings.setValue("saveFilePath", new_path)
            self.app.update_onboarding_state("select_character")
            
            # Show success icon and hide it after 3 seconds
            self.app.save_file_success_icon.setVisible(True)
            QTimer.singleShot(3000, lambda: self.app.save_file_success_icon.setVisible(False))
        else:
            # Keep the old path display if loading failed
            pass

    def _load_characters_for_save_file(self, save_file_path):
        """Loads character data from the save file and populates the combobox.
        Returns True if successful, False otherwise."""
        self.app.character_slot_combobox.clear()
        self.app.character_slot_combobox.addItem("Select a character", userData=None)
        
        characters, err = self.app.rust_cli_handler.list_characters(save_file_path)
        
        if err:
            # Check if this is a wrong file type error
            if "ZSTD" in err or "DCX" in err or "SaveParserError" in err or "BND4" in err or "Buckets" in err:
                QMessageBox.warning(
                    self.app, 
                    "Incompatible Save File Format", 
                    "This save file appears to be from an older or incompatible version of Elden Ring.\n\n"
                    "Common causes:\n"
                    "• Old pirated/cracked game version saves\n"
                    "• Outdated save file format\n"
                    "• Wrong Steam ID folder\n\n"
                    "Solutions:\n"
                    "1. Try the OTHER numbered folder in %APPDATA%\\EldenRing\\\n"
                    "   (Different folders = different game versions)\n\n"
                    "2. If you have multiple folders, use the one where other save editors work\n\n"
                    "3. For old saves: Use 'Elden Ring Save Manager' from Nexus Mods to\n"
                    "   convert your save to the current format first\n\n"
                    "Supported formats: ER0000.sl2 (Vanilla) or ER0000.co2 (Seamless Coop)"
                )
            else:
                QMessageBox.warning(self.app, "Error", f"Failed to read characters:\n{err}")
            self.app.character_slot_combobox.setEnabled(False)
            return False
            
        if not characters:
            self.app.character_slot_combobox.setEnabled(False)
            return False

        self.app.character_slot_combobox.setEnabled(True)
        for char in sorted(characters, key=lambda x: x.get('slot_index', 0)):
            char_name = char.get('character_name', f"Slot {char.get('slot_index')}")
            level = char.get('character_level', '??')
            self.app.character_slot_combobox.addItem(f"{char_name} (Level {level})", userData=char)
            
        # Always default to "Select a character" (index 0) when loading a new save file
        # The user must explicitly choose a character
        self.app.character_slot_combobox.setCurrentIndex(0)
        return True

    def handle_character_selection_change(self, index):
        """Handles the event when a new character is selected."""
        self.app.save_monitor_logic.stop_monitoring()
        selected_data = self.app.character_slot_combobox.itemData(index)
        
        if index == 0 or selected_data is None:
            self.stop_ui_timer()
            self.last_killed_boss_info = None
            self.app.footer.update_monitoring_status(False)
            self.app.footer.update_stats({})
            self.update_main_boss_area(clear=True)
            self.app.overlay_manager.update_text({})
            self.app.stats_section.update_stats({})
            self.app.update_onboarding_state("select_character")
            self.app.character_warning_label.setVisible(False) # Hide warning on deselect
            return
        
        self.app.settings.setValue("lastCharacterIndex", index)
        self.app.character_warning_label.setVisible(False) # Hide warning on new selection
        
        save_file_path = self._actual_save_file_path
        slot_index = selected_data["slot_index"]
        all_event_ids = self.app.boss_data_manager.get_all_event_ids_to_monitor()
        
        initial_data, err = self.app.rust_cli_handler.get_full_status(save_file_path, slot_index, all_event_ids)

        if err or not initial_data:
            print(f"Failed to get initial status: {err}")
            return
            
        char_name = selected_data.get("character_name")
        # --- Improved Last Boss Logic ---
        all_timestamps = self.app.timestamp_manager.get_timestamps_for_character(char_name)
        self.last_killed_boss_info = None # Reset before checking

        if all_timestamps:
            # Prioritize timestamp data if it exists
            last_boss_id = max(all_timestamps, key=all_timestamps.get)
            last_boss_time = all_timestamps[last_boss_id]
            boss_name = self.app.boss_data_manager.get_boss_name_by_id(last_boss_id)
            if boss_name:
                self.last_killed_boss_info = {"name": boss_name, "time": last_boss_time}
        
        # Fallback: If no timestamps, find the last defeated boss in the progression order
        if not self.last_killed_boss_info:
            boss_statuses = initial_data.get("boss_statuses", {})
            all_boss_defs = self.app.boss_data_manager.get_all_boss_definitions()
            
            # Create a map of event_id to boss name for quick lookup
            event_id_to_name = {str(b['event_id']): b['name'] for b in all_boss_defs if 'event_id' in b}

            last_defeated_boss_name = None
            # Iterate in reverse through the canonical progression order
            for location in reversed(LOCATION_PROGRESSION_ORDER):
                # This part needs access to the full boss data, not just statuses
                bosses_in_location = self.app.boss_data_manager.get_bosses_for_location(location)
                if not bosses_in_location: continue
                
                for boss in reversed(bosses_in_location):
                    event_id = str(boss.get("event_id"))
                    if event_id and boss_statuses.get(event_id, False):
                        last_defeated_boss_name = boss.get("name")
                        # We found the last one, so we can break out of all loops
                        break
                if last_defeated_boss_name:
                    break
            
            if last_defeated_boss_name:
                # We don't have a timestamp, so we'll use 0 as a placeholder
                self.last_killed_boss_info = {"name": last_defeated_boss_name, "time": 0}
            
        self.handle_stats_update(initial_data)
        self.app.update_onboarding_state("done")
        
        self.app.save_monitor_logic.start_monitoring(
            save_file_path,
            slot_index,
            selected_data["character_name"],
            initial_data=initial_data,
        )

    def handle_content_filter_change(self):
        """Handles changes to the Content Filter (Base/DLC/All)."""
        filter_mode = self.app.content_filter_combobox.currentData()
        print(f"Content filter changed to: {filter_mode}")

        self.app.settings.setValue("filters/contentMode", filter_mode)

        self.app.boss_data_manager.set_content_filter(filter_mode)

        self._refresh_after_filter_change()

    def _refresh_after_filter_change(self):
        current_index = self.app.character_slot_combobox.currentIndex()
        if current_index > 0:
            self.handle_character_selection_change(current_index)
        else:
            self.update_main_boss_area()

    def handle_type_filter_change(self):
        """Handles changes to the Boss Type Filter (all/no_minidungeon/main/custom)."""
        type_mode = self.app.type_filter_combobox.currentData()
        print(f"Boss type filter changed to: {type_mode}")

        self.app.settings.setValue("filters/typeMode", type_mode)
        self.app.edit_custom_filter_button.setVisible(type_mode == "custom")

        self.app.boss_data_manager.set_type_filter(type_mode)
        self._refresh_after_filter_change()

    def open_custom_filter_dialog(self):
        """Opens the dialog for picking a custom set of bosses."""
        from .ui.dialogs.custom_boss_filter_dialog import CustomBossFilterDialog

        manager = self.app.boss_data_manager
        dialog = CustomBossFilterDialog(
            manager.get_unfiltered_locations(),
            manager.get_custom_preset(),
            self.app,
        )
        if not dialog.exec():
            return

        selected_ids = dialog.selected_event_ids()
        self.app.settings.setValue(
            "filters/customPresetIds", json.dumps(sorted(selected_ids))
        )
        manager.set_custom_preset(selected_ids)
        if self.app.type_filter_combobox.currentData() == "custom":
            self._refresh_after_filter_change()

    def handle_status_filter_change(self):
        """Handles the 'Hide Defeated Bosses' checkbox."""
        is_checked = self.app.hide_defeated_checkbox.isChecked()
        print(f"Hide defeated filter changed to: {is_checked}")
        
        self.app.settings.setValue("filters/hideDefeated", is_checked)
        
        for section_widget in self.app.location_widgets.values():
            section_widget.apply_status_filter(is_checked)

    def on_search_text_changed(self, text):
        """Filters the displayed bosses based on the search text."""
        for section_widget in self.app.location_widgets.values():
            location_name = section_widget.location_name.lower()
            
            if text.lower() in location_name:
                section_widget.show()
                for row in range(section_widget.boss_table.rowCount()):
                    section_widget.boss_table.setRowHidden(row, False)
            else:
                any_boss_matches = False
                for row in range(section_widget.boss_table.rowCount()):
                    boss_name_item = section_widget.boss_table.item(row, 0)
                    boss_name = boss_name_item.text().lower()
                    
                    if text.lower() in boss_name:
                        section_widget.boss_table.setRowHidden(row, False)
                        any_boss_matches = True
                    else:
                        section_widget.boss_table.setRowHidden(row, True)
                
                section_widget.setVisible(any_boss_matches)

    def on_boss_defeated(self, boss_event_id: str, play_time: int):
        """Slot to handle a newly defeated boss."""
        all_boss_data = self.app.boss_data_manager.get_boss_data_by_location()
        character_name = self.app.character_slot_combobox.currentData().get("character_name")

        if not character_name:
            return

        for location, bosses in all_boss_data.items():
            for boss_info in bosses:
                event_ids = boss_info.get("event_id", [])
                if not isinstance(event_ids, list):
                    event_ids = [event_ids]
                
                if str(boss_event_id) in [str(eid) for eid in event_ids]:
                    boss_name = boss_info.get("name")
                    self.app.timestamp_manager.add_timestamp(character_name, int(boss_event_id), play_time)
                    
                    self.last_killed_boss_info = {"name": boss_name, "time": play_time}
                    print(f"New last killed boss: {self.last_killed_boss_info}")
                    
                    return

    def handle_stats_update(self, data: dict):
        """
        Processes new data, checks for character mismatch, and updates the entire UI.
        """
        stats_from_rust = data.get("stats", {})
        boss_statuses = data.get("boss_statuses", {})

        # --- Character Mismatch Check ---
        active_char_name = stats_from_rust.get("character_name")
        selected_char_data = self.app.character_slot_combobox.currentData()
        
        if not selected_char_data:
            return

        selected_char_name = selected_char_data.get("character_name")

        if active_char_name and selected_char_name and active_char_name != selected_char_name:
            warning_text = f"Warning: Playing as '{active_char_name}' but '{selected_char_name}' is selected in the app."
            self.app.character_warning_label.setText(warning_text)
            self.app.character_warning_label.setVisible(True)
            if self.app.ui_timer.isActive():
                self.app.ui_timer.stop()
            return
        else:
            self.app.character_warning_label.setVisible(False)
        
        self.app.boss_data_manager.update_boss_statuses(boss_statuses)
        boss_counts = self.app.boss_data_manager.get_boss_counts()

        final_stats_payload = stats_from_rust.copy()
        final_stats_payload['boss_counts'] = boss_counts
        final_stats_payload['defeated'] = boss_counts['total']['defeated']
        final_stats_payload['total'] = boss_counts['total']['total']

        self.last_play_time_snapshot = final_stats_payload.get('seconds_played', -1)
        self.last_snapshot_real_time = time.time()
        
        if self.is_game_running and self.last_play_time_snapshot >= 0 and not self.app.ui_timer.isActive():
            self.app.ui_timer.start()
        
        self.last_known_stats = {
            "stats": final_stats_payload,
            "boss_statuses": boss_statuses,
            "last_kill": self.last_killed_boss_info
        }
        
        self.app.footer.update_stats(final_stats_payload)
        self.app.overlay_manager.update_text(self.last_known_stats)
        self.app.obs_manager.update_obs_files(self.last_known_stats)
        
        self.update_main_boss_area()
        self.app.stats_section.update_stats(final_stats_payload)


    def _handle_monitoring_started(self, char_name, interval):
        self.app.footer.update_monitoring_status(True, text=f"Monitoring: {char_name}")

    def _handle_monitoring_stopped(self):
        self.app.footer.update_monitoring_status(False)

    def on_game_process_status_changed(self, is_running: bool):
        """Starts or stops the smooth UI timer based on game process status."""
        self.is_game_running = is_running
        print(f"[AppLogic] Slot on_game_process_status_changed received: {is_running}") # DEBUG
        if is_running:
            print("[AppLogic] Game process detected. Starting UI timer.") # DEBUG
            self.last_snapshot_real_time = time.time()
            self.app.ui_timer.start()
        else:
            print("Game process stopped. Stopping UI timer.")
            if self.last_play_time_snapshot > 0 and self.last_snapshot_real_time > 0:
                elapsed = time.time() - self.last_snapshot_real_time
                self.last_play_time_snapshot += elapsed
            self.app.ui_timer.stop()

    def stop_ui_timer(self):
        """Stops the UI timer and resets time snapshots."""
        if self.app.ui_timer.isActive():
            self.app.ui_timer.stop()
        self.last_play_time_snapshot = -1
        self.last_snapshot_real_time = -1
        self.is_game_running = False
        self.app.footer.update_time(-1)
        self.app.overlay_manager.update_text(self._get_current_stats_payload())

    def update_live_timer(self):
        """
        This slot is called every second to create a smooth ticking timer.
        """
        if self.last_play_time_snapshot < 0:
            return

        real_time_elapsed = time.time() - self.last_snapshot_real_time
        
        live_play_time = self.last_play_time_snapshot + real_time_elapsed
        
        # Update the main stats section, the OBS time file and the overlay
        self.app.stats_section.update_playtime(int(live_play_time))
        self.app.obs_manager.update_time_file(int(live_play_time))

        if self.app.overlay_manager.overlay_window.isVisible():
            stats = self.last_known_stats.get("stats", {}).copy()
            stats['seconds_played'] = int(live_play_time)
            temp_payload = self.last_known_stats.copy()
            temp_payload['stats'] = stats
            self.app.overlay_manager.update_text(temp_payload)

    def force_stats_update_for_obs(self):
       """Forces a manual recalculation and pushes the latest data to OBS files."""
       if self.last_known_stats:
           self.app.obs_manager.update_obs_files(self.last_known_stats)

    def _get_current_stats_payload(self) -> dict:
        """Constructs the current payload of stats for the overlay."""
        if not self.last_known_stats:
            return {}
        
        live_play_time = self.last_play_time_snapshot
        if self.is_game_running and self.last_snapshot_real_time > 0:
            live_play_time += time.time() - self.last_snapshot_real_time

        stats = self.last_known_stats.get("stats", {}).copy()
        stats['seconds_played'] = int(live_play_time)
        
        payload = self.last_known_stats.copy()
        payload['stats'] = stats
        return payload

    def toggle_overlay_settings(self):
        """Toggles the visibility of the overlay settings panel."""
        # If the overlay panel is already visible, hide the stack.
        if self.app.settings_stack.currentIndex() == 1:
            self.app.settings_stack.setCurrentIndex(0)
            self.app.settings_stack.setVisible(False)
        else:
            # Otherwise, show the overlay panel (this will automatically hide OBS panel).
            self.app.settings_stack.setCurrentIndex(1)
            self.app.settings_stack.setVisible(True)

    def toggle_obs_settings(self):
        """Toggles the visibility of the OBS settings panel."""
        # If the OBS panel is already visible, hide the stack.
        if self.app.settings_stack.currentIndex() == 2:
            self.app.settings_stack.setCurrentIndex(0)
            self.app.settings_stack.setVisible(False)
        else:
            # Otherwise, show the OBS panel (this will automatically hide overlay panel).
            self.app.settings_stack.setCurrentIndex(2)
            self.app.settings_stack.setVisible(True)

    def show_boss_details_dialog(self, boss_data):
        """Shows a dialog with detailed boss stats."""
        dialog = BossStatsDialog(boss_data, self.app)
        dialog.exec()

    def show_location_dialog(self, boss_data):
        """Shows a dialog with the boss's location."""
        # --- DEBUG MODE ---
        print(f"DEBUG: app_logic.show_location_dialog called for boss: {boss_data.get('name')}")
        dialog = LocationDialog(boss_data, self.app)
        dialog.exec()

    def _load_expansion_states(self):
        """Returns the persistent expansion-state dict, loading it from
        QSettings on first use. Surviving rebuilds (including clear=True
        sequences) is what keeps sections expanded across save-file refreshes."""
        if self._expansion_states is None and hasattr(self.app, "settings"):
            saved = self.app.settings.value("ui/expandedSections", "") or ""
            self._expansion_states = {name: True for name in saved.split("|") if name}
        return self._expansion_states if self._expansion_states is not None else {}

    def _on_section_expansion_changed(self, location_name: str, expanded: bool):
        states = self._load_expansion_states()
        states[location_name] = expanded
        if hasattr(self.app, "settings"):
            expanded_names = "|".join(sorted(n for n, e in states.items() if e))
            self.app.settings.setValue("ui/expandedSections", expanded_names)

    def update_main_boss_area(self, clear: bool = False):
        """Updates the main boss area with the current boss data."""
        expanded_states = self._load_expansion_states()
        for name, widget in self.app.location_widgets.items():
            expanded_states[name] = widget.is_expanded
        self._clear_boss_area()

        if clear:
            self.app.footer.update_stats({})
            return

        # Reset the set of added headers for each full refresh
        self._added_headers = set()

        sorted_base_game_items, sorted_dlc_items = self._get_sorted_boss_data()
        self._create_boss_widgets(sorted_base_game_items, expanded_states)
        self._create_boss_widgets(sorted_dlc_items, expanded_states, is_dlc=True)

        # Rebuilding loses per-row visibility, so the hide-defeated filter
        # has to be applied again to the fresh widgets
        if self.app.hide_defeated_checkbox.isChecked():
            for widget in self.app.location_widgets.values():
                widget.apply_status_filter(True)

    def _clear_boss_area(self):
        """Clears the main boss area of all widgets."""
        layout = self.app.main_boss_area_widget.widget().layout()
        while layout.count() > 1:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.app.location_widgets.clear()

    def _get_sorted_boss_data(self):
        """
        Gets and sorts the boss data based on the current content filter.
        It respects the LOCATION_PROGRESSION_ORDER for sorting base game items
        and sorts DLC items alphabetically.
        """
        boss_data = self.app.boss_data_manager.get_boss_data_by_location()
        dlc_location_names = self.app.boss_data_manager.get_dlc_location_names()

        base_game_items = []
        # Iterate through the master progression order to maintain sorting,
        # but only include locations that are actually in the filtered data.
        for loc in LOCATION_PROGRESSION_ORDER:
            if loc in boss_data:
                base_game_items.append((loc, boss_data[loc]))

        # Process DLC locations, sorting them alphabetically.
        dlc_items = []
        
        # Get a sorted list of all known DLC locations that are in the filtered data.
        sorted_dlc_names = sorted([loc for loc in dlc_location_names if loc in boss_data])

        for loc in sorted_dlc_names:
            # The check 'if loc in boss_data' is now implicit
            dlc_items.append((loc, boss_data[loc]))
        
        return base_game_items, dlc_items

    def _create_boss_widgets(self, boss_items, expanded_states, is_dlc=False):
        """Creates and adds the boss widgets and phase headers to the main area."""
        if not boss_items:
            return

        layout = self.app.main_boss_area_widget.widget().layout()
        character_name = self.app.character_slot_combobox.currentData().get("character_name") if self.app.character_slot_combobox.currentIndex() > 0 else None
        char_timestamps = self.app.timestamp_manager.get_timestamps_for_character(character_name) if character_name else {}

        # Special handling for the DLC header
        if is_dlc and "dlc_header" not in self._added_headers:
            header_info = GAME_PHASE_HEADINGS.get("dlc_header")
            if header_info:
                header_label = QLabel(header_info["text"])
                header_label.setObjectName("gamePhaseHeader")
                header_label.setProperty("phase", header_info["property"])
                header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.insertWidget(layout.count() - 1, header_label)
                self._added_headers.add("dlc_header")

        for loc, bosses in boss_items:
            # Check if this location should trigger a new game phase header
            if not is_dlc and loc in GAME_PHASE_HEADINGS and loc not in self._added_headers:
                header_info = GAME_PHASE_HEADINGS[loc]
                header_label = QLabel(header_info["text"])
                header_label.setObjectName("gamePhaseHeader")
                header_label.setProperty("phase", header_info["property"])
                header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.insertWidget(layout.count() - 1, header_label)
                self._added_headers.add(loc)

            # The boss data is now fully enriched, so we can pass it directly.
            section_widget = LocationSectionWidget(loc, bosses, self.app)
            section_widget.boss_details_requested.connect(self.show_boss_details_dialog)
            section_widget.boss_location_requested.connect(self.show_location_dialog)
            section_widget.expansion_changed.connect(self._on_section_expansion_changed)
            layout.insertWidget(layout.count() - 1, section_widget)
            self.app.location_widgets[loc] = section_widget
            if expanded_states.get(loc):
                section_widget.set_expanded(True)
    
    def start_update_download(self, manifest_data: dict):
        """
        Spustí proces aktualizace v samostatném vlákně s progress dialogem.
        """
        from src.ui.dialogs.download_progress import DownloadProgressDialog
        
        # Create and show progress dialog
        self.progress_dialog = DownloadProgressDialog(self.app)
        self.progress_dialog.show()
        
        # Start download thread
        update_thread = threading.Thread(target=self._perform_update, args=(manifest_data,))
        update_thread.daemon = True
        update_thread.start()
    
    def _perform_update(self, manifest_data: dict):
            """
            Stáhne, ověří a spustí nový instalátor.
            Tato metoda běží ve vedlejším vlákně.
            """
            url = manifest_data.get("url")
            expected_hash = manifest_data.get("sha256")
    
            if not url or not expected_hash:
                self._show_update_error("Manifest is missing required fields (url or sha256).")
                return
    
            try:
                # 1. Stažení souboru
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, os.path.basename(url))
                
                print(f"Downloading update from {url} to {installer_path}...")
                
                # Better error handling for download with UI progress
                try:
                    response = requests.get(url, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    # Update dialog status
                    QMetaObject.invokeMethod(
                        self.progress_dialog,
                        "update_status",
                        Qt.ConnectionType.QueuedConnection,
                        Q_ARG(str, "Downloading update...")
                    )
                    
                    with open(installer_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if hasattr(self, 'progress_dialog') and self.progress_dialog.is_cancelled():
                                print("Download cancelled by user")
                                return
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0:
                                    progress = (downloaded / total_size) * 100
                                    print(f"Download progress: {progress:.1f}%")
                                    # Update UI progress
                                    QMetaObject.invokeMethod(
                                        self.progress_dialog,
                                        "update_progress",
                                        Qt.ConnectionType.QueuedConnection,
                                        Q_ARG(int, int(progress))
                                    )
                                    QMetaObject.invokeMethod(
                                        self.progress_dialog,
                                        "update_size",
                                        Qt.ConnectionType.QueuedConnection,
                                        Q_ARG(int, downloaded),
                                        Q_ARG(int, total_size)
                                    )
                    
                    print("Download complete.")
                    QMetaObject.invokeMethod(
                        self.progress_dialog,
                        "update_status",
                        Qt.ConnectionType.QueuedConnection,
                        Q_ARG(str, "Verifying file integrity...")
                    )
                except requests.exceptions.RequestException as e:
                    print(f"Download failed: {e}")
                    if hasattr(self, 'progress_dialog'):
                        self.progress_dialog.close()
                    self._show_update_error(f"Failed to download update: {e}")
                    return
    
                # 2. Ověření hashe
                print("Verifying file integrity...")
                sha256_hash = hashlib.sha256()
                file_size = os.path.getsize(installer_path)
                verified = 0

                with open(installer_path, "rb") as f:
                    # Zvětšit buffer na 8MB pro rychlejší čtení velkých souborů
                    while True:
                        # Check if cancelled during verification
                        if hasattr(self, 'progress_dialog') and self.progress_dialog.is_cancelled():
                            print("Verification cancelled by user")
                            os.remove(installer_path)  # Clean up downloaded file
                            return

                        byte_block = f.read(8388608)  # 8MB chunks
                        if not byte_block:
                            break
                        sha256_hash.update(byte_block)
                        verified += len(byte_block)

                        # Update progress for verification
                        if file_size > 0:
                            verify_progress = (verified / file_size) * 100
                            QMetaObject.invokeMethod(
                                self.progress_dialog,
                                "update_progress",
                                Qt.ConnectionType.QueuedConnection,
                                Q_ARG(int, int(verify_progress))
                            )

                calculated_hash = sha256_hash.hexdigest()
    
                if calculated_hash.lower() != expected_hash.lower():
                    error_msg = f"Hash mismatch! Expected {expected_hash}, but got {calculated_hash}."
                    self._show_update_error(error_msg)
                    os.remove(installer_path) # Smazat nebezpečný soubor
                    return
                
                print("File integrity verified.")
    
                # 3. Spuštění instalátoru jako správce a ukončení aplikace
                print(f"Update downloaded. Waiting for user to click 'Install Now'...")
                try:
                    # Update dialog to show completion
                    if hasattr(self, 'progress_dialog'):
                        QMetaObject.invokeMethod(
                            self.progress_dialog,
                            "set_completed",
                            Qt.ConnectionType.QueuedConnection
                        )
                        
                        # Wait for dialog to be closed (user clicks "Install Now")
                        import time
                        while hasattr(self, 'progress_dialog') and self.progress_dialog.isVisible():
                            time.sleep(0.1)
                        
                        # Only launch installer after user clicks "Install Now"
                        if not self.progress_dialog.is_cancelled():
                            print(f"Starting installer as administrator: {installer_path}")
                            self._launch_installer(installer_path)
                        else:
                            print("Update cancelled by user")
                except Exception as e:
                    print(f"Failed to start installer: {e}")
                    if hasattr(self, 'progress_dialog'):
                        self.progress_dialog.close()
                    self._show_update_error(f"Failed to start installer: {e}")
    
            except Exception as e:
                self._show_update_error(f"An error occurred during the update process: {e}")
    
    def _launch_installer(self, installer_path):
        """Launch installer and close application"""
        try:
            # Start installer as administrator
            result = ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",  # Run as administrator
                installer_path,
                None,
                None,
                1  # Show window
            )
            
            if result > 32:  # Success
                print("Installer launched successfully. Closing application...")
                # Close progress dialog
                if hasattr(self, 'progress_dialog'):
                    self.progress_dialog.close()
                
                # Force close the application immediately after installer starts
                # We need to use QMetaObject to safely close from thread
                import time
                time.sleep(1)  # Give installer time to start
                
                # Use QMetaObject to safely call quit from thread
                QMetaObject.invokeMethod(
                    QApplication.instance(),
                    "quit",
                    Qt.ConnectionType.QueuedConnection
                )
            else:
                print(f"Failed to start installer as admin. Error code: {result}")
                raise Exception(f"ShellExecute failed with code {result}")
        except Exception as e:
            print(f"Failed to start installer: {e}")
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.close()
            self._show_update_error(f"Failed to start installer: {e}")
    
    def _force_close_app(self):
        """Force close the application"""
        if hasattr(self, 'app') and self.app:
            print("Closing application now...")
            self.app.quit()
            # Force exit if quit doesn't work
            import sys
            sys.exit(0)
    
    def _show_update_error(self, message: str):
            """Zobrazí chybovou hlášku v hlavním vlákně UI."""
            print(f"Update Error: {message}")
            QMetaObject.invokeMethod(
                self.app,
                "show_update_error_dialog",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, message)
            )
