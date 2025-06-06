import sys
import json 
import os 
import subprocess
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTreeWidget, QTreeWidgetItem, QFileDialog, QHeaderView,
    QLineEdit, QSpinBox, QCheckBox, QSizePolicy # Added QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont 
from styles import apply_app_styles, DEFEATED_TEXT_COLOR, NOT_DEFEATED_TEXT_COLOR, LOCATION_TEXT_COLOR, BOSS_NAME_TEXT_COLOR, LOCATION_ITEM_BG_COLOR, BOSS_ITEM_BG_COLOR
from overlay_window import OverlayWindow
from ui_components import create_file_slot_layout, create_monitoring_controls_layout, create_boss_tree_widget, create_overlay_settings_panel_layout # Renamed import

class BossChecklistApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Tarnished's Chronicle")
        self.setGeometry(150, 150, 1000, 750) 

        self.boss_data_by_location = {} 
        self.all_event_ids_to_monitor = [] 
        self.current_boss_statuses = {} 
        
        self.monitoring_timer = QTimer(self)
        self.monitoring_timer.timeout.connect(self.on_monitoring_timeout)
        self.monitoring_interval_sec = 5 # Default monitoring interval

        self.current_save_file_path_for_monitoring = ""
        self.current_slot_index_for_monitoring = 0    
        
        self.RUST_CLI_TOOL_PATH = self.detect_rust_cli_path()
 
        self.init_ui()
        self.load_initial_data()
        apply_app_styles(self)
        # Define default overlay styles
        overlay_background_color = "rgba(30, 30, 30, 220)"  # Darker, slightly more opaque
        overlay_text_color = "lightblue"
        overlay_font_size = "10pt"
        self.overlay_window = OverlayWindow(
            self,
            background_color=overlay_background_color,
            text_color=overlay_text_color,
            font_size=overlay_font_size
        )
        
        if self.save_file_path_input.text():
            self.on_save_file_path_changed(self.save_file_path_input.text())

    def detect_rust_cli_path(self, placeholder="RUST_CLI_TOOL_PATH_PLACEHOLDER"):
        path_to_check = placeholder 
        if path_to_check == placeholder: 
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(script_dir)
                default_path = os.path.join(project_root, "flag_extractor_cli", "target", "release", "flag_extractor_cli")
                if os.name == 'nt':
                    default_path += ".exe"
                
                if os.path.exists(default_path):
                    print(f"Automaticky nastavena cesta k Rust CLI: {default_path}")
                    return default_path
                else:
                    print(f"CHYBA: Rust CLI nástroj nebyl automaticky nalezen na: {default_path}")
                    return "" 
            except Exception as e:
                print(f"CHYBA při automatické detekci cesty k Rust CLI: {e}")
                return ""
        return path_to_check

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        file_slot_layout = create_file_slot_layout(self)
        self.browse_button.clicked.connect(self.browse_for_save_file)
        self.save_file_path_input.setText("C:\\Users\\dawel\\AppData\\Roaming\\EldenRing\\76561198082650286\\ER0000.sl2")
        self.save_file_path_input.textChanged.connect(self.on_save_file_path_changed)
        self.character_slot_combobox.currentIndexChanged.connect(self.handle_character_selection_change)
        main_layout.addLayout(file_slot_layout)

        # --- Overlay Control Buttons ---
        overlay_buttons_layout = QHBoxLayout()
        self.toggle_overlay_button = QPushButton("Toggle Overlay", self)
        self.toggle_overlay_button.clicked.connect(self.toggle_overlay)
        overlay_buttons_layout.addWidget(self.toggle_overlay_button, 4) # 80% stretch factor (4 out of 5 parts)

        self.overlay_settings_button = QPushButton("Overlay Settings", self)
        self.overlay_settings_button.clicked.connect(self.toggle_overlay_settings_panel)
        overlay_buttons_layout.addWidget(self.overlay_settings_button, 1) # 20% stretch factor (1 out of 5 parts)
        main_layout.addLayout(overlay_buttons_layout)

        # --- Overlay Settings Panel (initially hidden) ---
        self.overlay_settings_panel = create_overlay_settings_panel_layout(self) # This now returns a QWidget
        self.overlay_settings_panel.setVisible(False) # Initially hidden
        main_layout.addWidget(self.overlay_settings_panel)
        self.apply_overlay_settings_button.clicked.connect(self.apply_overlay_settings)
 
        self.status_label = QLabel("Připraven.", self)
        main_layout.addWidget(self.status_label)
 
        self.total_boss_count_label = QLabel("Celkový počet bossů: N/A", self)
        main_layout.addWidget(self.total_boss_count_label)

        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search bosses/locations...")
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        main_layout.addWidget(self.search_bar)
        
        self.boss_tree = create_boss_tree_widget(self)
        main_layout.addWidget(self.boss_tree)
 
        self.setLayout(main_layout)

    def toggle_overlay(self):
        if self.overlay_window.isVisible():
            self.overlay_window.hide_overlay()
        else:
            defeated_boss_count = sum(1 for loc_bosses in self.boss_data_by_location.values() if isinstance(loc_bosses, list) for b in loc_bosses if isinstance(b, dict) and b.get("is_defeated"))
            total_bosses = sum(len(loc_bosses) for loc_bosses in self.boss_data_by_location.values() if isinstance(loc_bosses, list))
            if total_bosses > 0 : 
                 self.overlay_window.set_text(f"Bosses Defeated: {defeated_boss_count}/{total_bosses}")
            else:
                 self.overlay_window.set_text("Bosses: N/A") 
            self.overlay_window.show_overlay()

    def on_save_file_path_changed(self, new_path):
        self.stop_monitoring_if_active()

        if os.path.exists(new_path) and os.path.isfile(new_path):
            self.load_characters_for_save_file(new_path)
        else:
            self.character_slot_combobox.clear()
            self.character_slot_combobox.setEnabled(False) 
            self.character_slot_combobox.setPlaceholderText("Select Character (invalid path)")
            self.status_label.setText("Neplatná cesta k save souboru.")
            self.status_label.setStyleSheet("color: orange;")
            self.stop_monitoring_if_active() 

    def load_characters_for_save_file(self, save_file_path):
        self.character_slot_combobox.clear()
        self.character_slot_combobox.setEnabled(False)
        self.character_slot_combobox.setPlaceholderText("Loading characters...")

        if not self.RUST_CLI_TOOL_PATH or not os.path.exists(self.RUST_CLI_TOOL_PATH):
            self.status_label.setText(f"CHYBA: Rust CLI tool not found at: {self.RUST_CLI_TOOL_PATH}")
            self.status_label.setStyleSheet("color: red;")
            self.character_slot_combobox.setPlaceholderText("CLI Error")
            return

        command = [
            self.RUST_CLI_TOOL_PATH,
            "list-characters", 
            "--save-file-path", save_file_path
        ]
        
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            if process.returncode != 0:
                self.status_label.setText(f"Error listing characters (Rust CLI): {process.stderr[:100]}...")
                self.status_label.setStyleSheet("color: red;")
                self.character_slot_combobox.setPlaceholderText("Error Listing")
                print(f"Rust CLI Error (list-characters): {process.stderr}")
                return

            if not process.stdout.strip():
                self.status_label.setText("No character data from Rust CLI.")
                self.status_label.setStyleSheet("color: orange;")
                self.character_slot_combobox.setPlaceholderText("No Characters")
                return

            characters_data = json.loads(process.stdout)
            if characters_data:
                for char_info in characters_data:
                    character_name = char_info.get("character_name")
                    if character_name and character_name != "Error decoding name":
                        character_level = char_info.get("character_level") 
                        
                        if character_level is not None:
                            display_name = f"{character_name} (Level {character_level})"
                        else:
                            display_name = f"{character_name} (Level N/A)"
                        
                        self.character_slot_combobox.addItem(display_name, userData=char_info['slot_index'])
                self.character_slot_combobox.setEnabled(True)
                self.character_slot_combobox.setPlaceholderText("Select Character")
                if self.character_slot_combobox.count() > 0:
                    self.character_slot_combobox.setCurrentIndex(0)
            else:
                self.character_slot_combobox.setPlaceholderText("No Characters Found")
                self.status_label.setText("No characters found in save file.")

        except FileNotFoundError:
            self.status_label.setText("Rust CLI not found during character listing.")
            self.status_label.setStyleSheet("color: red;")
            self.character_slot_combobox.setPlaceholderText("CLI Not Found")
        except json.JSONDecodeError:
            self.status_label.setText("Error parsing character data from Rust CLI.")
            self.status_label.setStyleSheet("color: red;")
            self.character_slot_combobox.setPlaceholderText("Parse Error")
            print(f"JSON Decode Error from list-characters output: {process.stdout}")
        except Exception as e:
            self.status_label.setText(f"Error loading characters: {e}")
            self.status_label.setStyleSheet("color: red;")
            self.character_slot_combobox.setPlaceholderText("Load Error")
            print(f"General error in load_characters_for_save_file: {e}")
  
    def browse_for_save_file(self):
        current_path = self.save_file_path_input.text()
        start_dir = os.path.dirname(current_path) if os.path.exists(current_path) else ""
        
        filepath, _ = QFileDialog.getOpenFileName(self, "Vyberte Elden Ring save file (ER0000.sl2)", start_dir, "SL2 Files (*.sl2);;All Files (*)")
        if filepath:
            self.save_file_path_input.setText(filepath)

    def load_initial_data(self, reference_json_filename="boss_ids_reference.json"):
        """Loads reference boss definitions on startup."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            full_reference_path = os.path.join(project_root, "data", "Bosses", reference_json_filename)
            
            if os.path.exists(full_reference_path):
                self.load_reference_boss_definitions(full_reference_path)
            else:
                self.status_label.setText(f"CHYBA: Referenční JSON '{reference_json_filename}' nenalezen na '{full_reference_path}'.")
                self.status_label.setStyleSheet("color: red;")
        except Exception as e:
            self.status_label.setText(f"CHYBA při přípravě cesty k referenčnímu JSON: {e}")
            self.status_label.setStyleSheet("color: red;")

    def load_reference_boss_definitions(self, filepath):
        self.status_label.setText(f"Načítám referenční definice z: {os.path.basename(filepath)}...")
        self.status_label.setStyleSheet("")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f) 
            
            if not isinstance(data, dict):
                self.status_label.setText(f"CHYBA formátu v {os.path.basename(filepath)}: Očekáván slovník.")
                self.status_label.setStyleSheet("color: red;")
                return False

            all_ids = set()
            for _location_name, bosses_in_location in data.items():
                if isinstance(bosses_in_location, list):
                    for boss_info in bosses_in_location:
                        if isinstance(boss_info, dict):
                            event_id_value = boss_info.get("event_id")
                            if event_id_value is not None:
                                if isinstance(event_id_value, list): 
                                    for eid in event_id_value:
                                        try: all_ids.add(int(str(eid)))
                                        except ValueError: print(f"Varování: Neplatné event_id '{eid}' pro '{boss_info.get('name')}' v referenčních datech.")
                                else: 
                                    try: all_ids.add(int(str(event_id_value)))
                                    except ValueError: print(f"Varování: Neplatné event_id '{event_id_value}' pro '{boss_info.get('name')}' v referenčních datech.")
            
            self.all_event_ids_to_monitor = list(all_ids)
            self.boss_data_by_location = data
            self.populate_boss_tree() 
            self.status_label.setText(f"Načteno {len(self.all_event_ids_to_monitor)} unikátních Event ID pro monitoring. Referenční data zobrazena.")
            self.status_label.setStyleSheet("color: green;")
            return True
        except FileNotFoundError:
            self.status_label.setText(f"CHYBA: Referenční soubor '{os.path.basename(filepath)}' nenalezen.")
            self.status_label.setStyleSheet("color: red;")
        except json.JSONDecodeError:
            self.status_label.setText(f"CHYBA: Chyba při parsování referenčního JSON souboru: {os.path.basename(filepath)}.")
            self.status_label.setStyleSheet("color: red;")
        except Exception as e:
            self.status_label.setText(f"CHYBA při načítání referenčních definic: {e}")
            self.status_label.setStyleSheet("color: red;")
        
        self.all_event_ids_to_monitor = []
        self.boss_data_by_location = {}
        self.populate_boss_tree()
        return False

    def handle_character_selection_change(self, index):
        """Handles changes in character selection to start/stop monitoring."""
        self.stop_monitoring_if_active() 
        
        if index != -1 and self.character_slot_combobox.currentData() is not None:
            self.initiate_monitoring_for_current_selection()
        else:
            self.status_label.setText("Vyberte postavu pro spuštění monitoringu.")
            self.status_label.setStyleSheet("color: orange;")

    def stop_monitoring_if_active(self):
        """Stops the monitoring timer if it's active and updates UI."""
        if self.monitoring_timer.isActive():
            self.monitoring_timer.stop()
            self.status_label.setText("Monitoring zastaven.")
            self.status_label.setStyleSheet("color: orange;")

    def initiate_monitoring_for_current_selection(self):
        """Starts monitoring for the currently selected save file and character."""
        self.current_save_file_path_for_monitoring = self.save_file_path_input.text()
        selected_slot_data = self.character_slot_combobox.currentData()

        if selected_slot_data is None:
            self.status_label.setText("CHYBA: Pro monitoring není vybrána žádná postava.")
            self.status_label.setStyleSheet("color: red;")
            return
        self.current_slot_index_for_monitoring = selected_slot_data
        
        char_name = self.character_slot_combobox.currentText()

        if not self.current_save_file_path_for_monitoring or not os.path.exists(self.current_save_file_path_for_monitoring):
            self.status_label.setText("CHYBA: Zadejte platnou cestu k save filu.")
            self.status_label.setStyleSheet("color: red;")
            return

        if not self.RUST_CLI_TOOL_PATH or not os.path.exists(self.RUST_CLI_TOOL_PATH):
            self.status_label.setText(f"CHYBA: Rust CLI nástroj nebyl nalezen na: {self.RUST_CLI_TOOL_PATH}")
            self.status_label.setStyleSheet("color: red;")
            return

        if not self.all_event_ids_to_monitor:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            default_reference_path = os.path.join(project_root, "data", "Bosses", "boss_ids_reference.json")
            if not self.load_reference_boss_definitions(default_reference_path):
                self.status_label.setText("CHYBA: Nelze spustit monitoring, chybí definice bossů.")
                self.status_label.setStyleSheet("color: red;")
                return
        
        if not self.all_event_ids_to_monitor: 
            self.status_label.setText("CHYBA: Nejsou definována žádná Event ID ke sledování.")
            self.status_label.setStyleSheet("color: red;")
            return

        initial_statuses = self._get_statuses_via_rust_cli()
        if initial_statuses is None:
            self.status_label.setText("CHYBA: Selhal první sken savefilu. Zkontrolujte Rust CLI a cestu k savefilu.")
            self.status_label.setStyleSheet("color: red;")
            return
        
        self.current_boss_statuses = initial_statuses
        self._update_gui_from_statuses(self.current_boss_statuses, initial_scan=True)

        self.monitoring_timer.start(self.monitoring_interval_sec * 1000)
        self.status_label.setText(f"Monitoring aktivní: '{char_name}' (interval: {self.monitoring_interval_sec}s).")
        self.status_label.setStyleSheet("color: blue;")

    def on_monitoring_timeout(self):
        if not self.current_save_file_path_for_monitoring or not self.monitoring_timer.isActive():
            return
        
        new_statuses = self._get_statuses_via_rust_cli()

        if new_statuses is None:
            self.status_label.setText("CHYBA: Analýza během monitoringu selhala.") 
            self.status_label.setStyleSheet("color: red;")
            return

        changes_found = False
        for event_id_str, new_status_bool in new_statuses.items():
            if self.current_boss_statuses.get(event_id_str) != new_status_bool:
                changes_found = True
        
        if changes_found:
            self.status_label.setText("Změna detekována! Aktualizuji GUI...")
            self.status_label.setStyleSheet("color: green;")
            self.current_boss_statuses = new_statuses
            self._update_gui_from_statuses(self.current_boss_statuses)
            
            selected_char_name = self.character_slot_combobox.currentText()
            status_update_text = f"Monitoring aktivní pro: {selected_char_name} (interval: {self.monitoring_interval_sec}s)."
            QTimer.singleShot(2000, lambda: self.status_label.setText(status_update_text) if self.monitoring_timer.isActive() else None)
            QTimer.singleShot(2000, lambda: self.status_label.setStyleSheet("color: blue;") if self.monitoring_timer.isActive() else None) 
        else:
            pass 

    def _get_statuses_via_rust_cli(self):
        if not self.all_event_ids_to_monitor:
            return {} 
        if not self.RUST_CLI_TOOL_PATH or not os.path.exists(self.RUST_CLI_TOOL_PATH):
            print(f"CHYBA: Rust CLI tool path not valid: {self.RUST_CLI_TOOL_PATH}")
            return None
        if not self.current_save_file_path_for_monitoring or not os.path.exists(self.current_save_file_path_for_monitoring):
            print(f"CHYBA: Save file path not valid for Rust CLI: {self.current_save_file_path_for_monitoring}")
            return None

        event_ids_str_list = [str(eid) for eid in self.all_event_ids_to_monitor]
        command = [
            self.RUST_CLI_TOOL_PATH,
            "get-event-flags", 
            "--save-file-path", self.current_save_file_path_for_monitoring,
            "--slot-index", str(self.current_slot_index_for_monitoring),
            "--event-ids", ",".join(event_ids_str_list)
        ]
        
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

            if process.returncode != 0:
                print(f"CHYBA: Rust CLI selhal (kód {process.returncode}): {process.stderr}")
                return None
            
            if not process.stdout.strip():
                print("CHYBA: Rust CLI nevrátil žádný výstup.")
                return None
                
            return json.loads(process.stdout) 
        except FileNotFoundError: 
            print(f"CHYBA: Rust CLI nebyl nalezen při pokusu o spuštění: {self.RUST_CLI_TOOL_PATH}")
            return None
        except json.JSONDecodeError as e:
            print(f"CHYBA: Nepodařilo se dekódovat JSON z Rust CLI: {e}. Výstup: '{process.stdout}'")
            return None
        except Exception as e:
            print(f"CHYBA při volání Rust CLI nebo parsování výstupu: {e}")
            return None

    def _update_gui_from_statuses(self, statuses_dict, initial_scan=False):
        if not self.boss_data_by_location : 
            if initial_scan: 
                print("DEBUG: _update_gui_from_statuses - chybí referenční data, pokus o načtení.")
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(script_dir)
                default_reference_path = os.path.join(project_root, "data", "Bosses", "boss_ids_reference.json")
                if not self.load_reference_boss_definitions(default_reference_path):
                    self.status_label.setText("CHYBA: Chybí referenční data bossů pro aktualizaci GUI.")
                    return
            else: 
                self.status_label.setText("CHYBA: Chybí referenční data bossů pro aktualizaci GUI (po inicializaci).")
                return

        for _location, bosses_in_location in self.boss_data_by_location.items():
            if isinstance(bosses_in_location, list):
                for boss_info in bosses_in_location:
                    if not isinstance(boss_info, dict): continue

                    event_id_value = boss_info.get("event_id")
                    if event_id_value is None: continue

                    ids_for_this_boss_entry = []
                    if isinstance(event_id_value, list):
                        ids_for_this_boss_entry = [str(eid) for eid in event_id_value]
                    else:
                        ids_for_this_boss_entry.append(str(event_id_value))
                    
                    new_is_defeated_state = False
                    for eid_str in ids_for_this_boss_entry:
                        if statuses_dict.get(eid_str) is True:
                            new_is_defeated_state = True
                            break
                    boss_info["is_defeated"] = new_is_defeated_state
        
        self.populate_boss_tree()
        self.update_overlay_text_if_visible() 
 
    def update_overlay_text_if_visible(self):
        if hasattr(self, 'overlay_window') and self.overlay_window.isVisible():
            defeated_boss_count = sum(1 for loc_bosses in self.boss_data_by_location.values() if isinstance(loc_bosses, list) for b in loc_bosses if isinstance(b, dict) and b.get("is_defeated"))
            total_bosses = sum(len(loc_bosses) for loc_bosses in self.boss_data_by_location.values() if isinstance(loc_bosses, list))
            self.overlay_window.set_text(f"Bosses Defeated: {defeated_boss_count}/{total_bosses}")

    def toggle_overlay_settings_panel(self):
        self.overlay_settings_panel.setVisible(not self.overlay_settings_panel.isVisible())
        self.overlay_settings_button.setText("Hide Settings" if self.overlay_settings_panel.isVisible() else "Overlay Settings")


    def apply_overlay_settings(self):
        bg_color = self.overlay_bg_color_input.text()
        text_color = self.overlay_text_color_input.text()
        font_size = self.overlay_font_size_input.text()

        # Validate inputs (basic validation, can be improved)
        if not bg_color: bg_color = "rgba(30, 30, 30, 220)" # Default if empty
        if not text_color: text_color = "lightblue"
        if not font_size: font_size = "10pt"

        self.overlay_window.update_styles(
            background_color=bg_color,
            text_color=text_color,
            font_size=font_size
        )
        
        # If the overlay is visible, its appearance should update automatically
        # due to the self.update() call in OverlayWindow.update_styles.
        # If not, the new styles will apply the next time it's shown.

        self.status_label.setText("Overlay settings applied.")
        self.status_label.setStyleSheet("color: green;")
        QTimer.singleShot(3000, lambda: self.status_label.setText("Připraven.") if not self.monitoring_timer.isActive() else None)
        QTimer.singleShot(3000, lambda: self.status_label.setStyleSheet("") if not self.monitoring_timer.isActive() else None)


    def populate_boss_tree(self):
        self.boss_tree.clear()

        if not self.boss_data_by_location:
            return

        total_bosses_overall = 0
        sorted_locations = sorted(self.boss_data_by_location.items())

        for location_name, bosses_in_location in sorted_locations:
            location_item = QTreeWidgetItem(self.boss_tree)
            
            boss_count_in_location = 0
            defeated_count_in_location = 0
            if isinstance(bosses_in_location, list):
                boss_count_in_location = len(bosses_in_location)
                total_bosses_overall += boss_count_in_location 
                for boss_info_count in bosses_in_location:
                    if isinstance(boss_info_count, dict) and boss_info_count.get("is_defeated", False):
                        defeated_count_in_location +=1
            
            display_location_name = f"🌍 {location_name} ({defeated_count_in_location}/{boss_count_in_location})"
            location_item.setText(1, display_location_name)
            location_item.setForeground(1, LOCATION_TEXT_COLOR)
            location_item.setBackground(0, LOCATION_ITEM_BG_COLOR)
            location_item.setBackground(1, LOCATION_ITEM_BG_COLOR)
            location_item.setBackground(2, LOCATION_ITEM_BG_COLOR) 

            # Add a disabled QCheckBox as a widget for column 2 - Reverting to the container method for visuals
            location_complete_checkbox = QCheckBox()
            is_complete = boss_count_in_location > 0 and defeated_count_in_location == boss_count_in_location
            location_complete_checkbox.setChecked(is_complete)
            location_complete_checkbox.setEnabled(False) # This makes the checkbox non-interactive

            # Set the checkbox directly as the item widget
            self.boss_tree.setItemWidget(location_item, 2, location_complete_checkbox)

            font = location_item.font(1)
            font.setBold(True)
            location_item.setFont(1, font)
            location_item.setFont(0, font)

            self.boss_tree.addTopLevelItem(location_item)

            if isinstance(bosses_in_location, list):
                def get_boss_name_for_sort(boss_dict):
                    name = boss_dict.get("name", "")
                    return str(name) if name is not None else ""
                sorted_bosses = sorted(bosses_in_location, key=get_boss_name_for_sort)

                for boss_info in sorted_bosses:
                    if not isinstance(boss_info, dict):
                        child = QTreeWidgetItem(location_item, ["", "Nevalidní data bosse"])
                        child.setBackground(0, BOSS_ITEM_BG_COLOR)
                        child.setBackground(1, BOSS_ITEM_BG_COLOR)
                        continue

                    is_defeated = boss_info.get("is_defeated", False)
                    status_icon = "✔" if is_defeated else "❌"
                    status_text_label = "Defeated" if is_defeated else "Not Defeated" 
                    
                    boss_name_text = boss_info.get("name", "N/A")
                    
                    boss_list_item = QTreeWidgetItem(location_item)
                    boss_list_item.setText(0, f"{status_icon} {status_text_label}")
                    boss_list_item.setForeground(0, DEFEATED_TEXT_COLOR if is_defeated else NOT_DEFEATED_TEXT_COLOR)
                    
                    boss_list_item.setText(1, f"💀 {boss_name_text}")
                    boss_list_item.setForeground(1, BOSS_NAME_TEXT_COLOR)

                    boss_list_item.setBackground(0, BOSS_ITEM_BG_COLOR)
                    boss_list_item.setBackground(1, BOSS_ITEM_BG_COLOR)

                    # location_item.setExpanded(True) # Ensure this is removed for collapsed default
            else:
                 child = QTreeWidgetItem(location_item, ["", "Chybný formát bossů pro tuto lokaci"])
                 child.setBackground(0, BOSS_ITEM_BG_COLOR)
                 child.setBackground(1, BOSS_ITEM_BG_COLOR)

        self.total_boss_count_label.setText(f"Celkový počet bossů: {total_bosses_overall}")

        # self.boss_tree.expandAll() # Ensure this is removed for collapsed default

        self.boss_tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) 
        self.boss_tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)       
        self.boss_tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) 
        self.boss_tree.resizeColumnToContents(2) 


    def on_search_text_changed(self, text):
        """Filters the boss tree based on the search text."""
        search_term = text.lower()
        
        for i in range(self.boss_tree.topLevelItemCount()):
            location_item = self.boss_tree.topLevelItem(i)
            location_text_to_search = location_item.text(1).lower() 
            
            any_child_visible = False

            for j in range(location_item.childCount()):
                boss_item = location_item.child(j)
                boss_name_to_search = boss_item.text(1).lower() 
                
                if search_term in boss_name_to_search:
                    boss_item.setHidden(False)
                    any_child_visible = True
                else:
                    boss_item.setHidden(True)
            
            if search_term in location_text_to_search or any_child_visible:
                location_item.setHidden(False)
            else:
                location_item.setHidden(True)

def main():
    app = QApplication(sys.argv)
    window = BossChecklistApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()