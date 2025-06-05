import sys
import json 
import os 
import subprocess
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTreeWidget, QTreeWidgetItem, QFileDialog, QHeaderView,
    QLineEdit, QSpinBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont # QColor will be imported from styles
from .styles import apply_app_styles, DEFEATED_TEXT_COLOR, NOT_DEFEATED_TEXT_COLOR, LOCATION_TEXT_COLOR, BOSS_NAME_TEXT_COLOR, LOCATION_ITEM_BG_COLOR, BOSS_ITEM_BG_COLOR
from .overlay_window import OverlayWindow
from .ui_components import create_file_slot_layout, create_monitoring_controls_layout, create_boss_tree_widget

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

        self.current_save_file_path_for_monitoring = "" 
        self.current_slot_index_for_monitoring = 0    
        self.monitoring_interval_sec = 5             

        self.RUST_CLI_TOOL_PATH = self.detect_rust_cli_path() 

        self.init_ui()
        self.load_initial_data()
        apply_app_styles(self) # Use the imported function
        self.overlay_window = OverlayWindow(self) # Create instance of overlay

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
                    # self.status_label might not be initialized yet if called from __init__ before init_ui
                    # Consider passing status_label or handling this differently if it's an issue.
                    # For now, just print.
                    return "" 
            except Exception as e:
                print(f"CHYBA při automatické detekci cesty k Rust CLI: {e}")
                return ""
        return path_to_check

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # File and Slot selection
        file_slot_layout = create_file_slot_layout(self)
        # The create_file_slot_layout function now sets up self.browse_button
        self.browse_button.clicked.connect(self.browse_for_save_file)
        main_layout.addLayout(file_slot_layout)

        # Monitoring Controls
        monitoring_controls_layout = create_monitoring_controls_layout(self)
        # The create_monitoring_controls_layout function now sets up these buttons
        self.start_monitor_button.clicked.connect(self.start_monitoring)
        self.stop_monitor_button.clicked.connect(self.stop_monitoring)
        main_layout.addLayout(monitoring_controls_layout)

        # Load JSON Snapshot Button
        self.load_json_button = QPushButton("Manuálně načíst zpracovaná data bossů (JSON snapshot)", self)
        self.load_json_button.clicked.connect(self.on_load_json_snapshot_clicked)
        main_layout.addWidget(self.load_json_button)

        # Toggle Overlay Button
        self.toggle_overlay_button = QPushButton("Toggle Overlay", self)
        self.toggle_overlay_button.clicked.connect(self.toggle_overlay)
        main_layout.addWidget(self.toggle_overlay_button)
 
        # Status Label
        self.status_label = QLabel("Připraven.", self)
        # self.status_label.setStyleSheet("padding: 5px;") # Styling handled by QSS
        main_layout.addWidget(self.status_label)
 
        # Total Boss Count Label
        self.total_boss_count_label = QLabel("Celkový počet bossů: N/A", self)
        # self.total_boss_count_label.setStyleSheet("padding: 5px; font-weight: bold;") # Styling handled by QSS
        main_layout.addWidget(self.total_boss_count_label)
        
        # Boss Tree Widget
        self.boss_tree = create_boss_tree_widget(self)
        main_layout.addWidget(self.boss_tree)
 
        self.setLayout(main_layout)

    def toggle_overlay(self):
        if self.overlay_window.isVisible():
            self.overlay_window.hide_overlay()
        else:
            # You can customize the text shown in the overlay
            defeated_boss_count = sum(1 for loc_bosses in self.boss_data_by_location.values() if isinstance(loc_bosses, list) for b in loc_bosses if isinstance(b, dict) and b.get("is_defeated"))
            total_bosses = sum(len(loc_bosses) for loc_bosses in self.boss_data_by_location.values() if isinstance(loc_bosses, list))
            self.overlay_window.set_text(f"Bosses Defeated: {defeated_boss_count}/{total_bosses}")
            self.overlay_window.show_overlay()
 
    def browse_for_save_file(self):
        current_path = self.save_file_path_input.text()
        start_dir = os.path.dirname(current_path) if os.path.exists(current_path) else ""
        
        filepath, _ = QFileDialog.getOpenFileName(self, "Vyberte Elden Ring save file (ER0000.sl2)", start_dir, "SL2 Files (*.sl2);;All Files (*)")
        if filepath:
            self.save_file_path_input.setText(filepath)

    def load_initial_data(self, reference_json_filename="boss_ids_reference.json"): # CHANGED FILENAME
        """Loads reference boss definitions on startup."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            full_reference_path = os.path.join(project_root, "data", "Bosses", reference_json_filename) # Use passed filename
            
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
            for location_name, bosses_in_location in data.items():
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
            self.populate_boss_tree() # This will also update the total count
            self.status_label.setText(f"Načteno {len(self.all_event_ids_to_monitor)} unikátních Event ID pro monitoring. Referenční data zobrazena.")
            self.status_label.setStyleSheet("color: green;")
            return True
        except FileNotFoundError:
            self.status_label.setText(f"CHYBA: Referenční soubor '{os.path.basename(filepath)}' nenalezen.") # Use basename here
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

    def on_load_json_snapshot_clicked(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        default_dir = os.path.join(project_root, "data", "Bosses")
        # Default to the processed file if it exists, otherwise let user choose
        default_snapshot_file = os.path.join(default_dir, "reference_boss_ids_processed_via_er_save_lib_cli.json")
        if not os.path.exists(default_snapshot_file):
            default_snapshot_file = default_dir # Fallback to directory if specific file not found

        filepath, _ = QFileDialog.getOpenFileName(
            self, 
            "Vyberte zpracovaný JSON soubor s bossy (snapshot)", 
            default_snapshot_file,  
            "JSON Files (*.json)"
        )
        
        if filepath: 
            self.status_label.setText(f"Načítám snapshot z: {os.path.basename(filepath)}...")
            self.status_label.setStyleSheet("") 
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f) 
                
                if not isinstance(loaded_data, dict): 
                    self.status_label.setText(f"Chyba formátu snapshotu: Očekáván slovník lokací.")
                    self.status_label.setStyleSheet("color: red;")
                    return

                self.boss_data_by_location = loaded_data
                self.populate_boss_tree() # This will also update the total count
                self.status_label.setText(f"Snapshot '{os.path.basename(filepath)}' úspěšně načten.")
                self.status_label.setStyleSheet("color: green;")
            except Exception as e:
                self.status_label.setText(f"CHYBA při načítání snapshotu: {e}")
                self.status_label.setStyleSheet("color: red;")
        else:
            self.status_label.setText("Načítání snapshotu zrušeno.")
            self.status_label.setStyleSheet("color: orange;")


    def start_monitoring(self):
        self.current_save_file_path_for_monitoring = self.save_file_path_input.text()
        self.current_slot_index_for_monitoring = self.slot_index_spinbox.value()
        self.monitoring_interval_sec = self.interval_spinbox.value()

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
            default_reference_path = os.path.join(project_root, "data", "Bosses", "boss_ids_reference.json") # CHANGED FILENAME
            if not self.load_reference_boss_definitions(default_reference_path): 
                self.status_label.setText("CHYBA: Nelze spustit monitoring, chybí definice bossů.")
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
        self.start_monitor_button.setEnabled(False)
        self.stop_monitor_button.setEnabled(True)
        self.save_file_path_input.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.slot_index_spinbox.setEnabled(False)
        self.interval_spinbox.setEnabled(False)
        self.load_json_button.setEnabled(False) 
        self.status_label.setText(f"Monitoring spuštěn (interval: {self.monitoring_interval_sec}s).")
        self.status_label.setStyleSheet("color: blue;")

    def stop_monitoring(self):
        self.monitoring_timer.stop()
        self.start_monitor_button.setEnabled(True)
        self.stop_monitor_button.setEnabled(False)
        self.save_file_path_input.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.slot_index_spinbox.setEnabled(True)
        self.interval_spinbox.setEnabled(True)
        self.load_json_button.setEnabled(True)
        self.status_label.setText("Monitoring zastaven.")
        self.status_label.setStyleSheet("color: orange;")

    def on_monitoring_timeout(self):
        if not self.current_save_file_path_for_monitoring or not self.monitoring_timer.isActive():
            return

        print(f"Monitoring tick: Kontroluji {os.path.basename(self.current_save_file_path_for_monitoring)} slot {self.current_slot_index_for_monitoring}")
        
        new_statuses = self._get_statuses_via_rust_cli()

        if new_statuses is None:
            self.status_label.setText("CHYBA: Analýza během monitoringu selhala.")
            self.status_label.setStyleSheet("color: red;")
            return

        changes_found = False
        for event_id_str, new_status_bool in new_statuses.items():
            if self.current_boss_statuses.get(event_id_str) != new_status_bool:
                changes_found = True
                print(f"Změna pro Event ID {event_id_str}: {self.current_boss_statuses.get(event_id_str)} -> {new_status_bool}")
        
        if changes_found:
            self.status_label.setText("Změna detekována! Aktualizuji GUI...")
            self.status_label.setStyleSheet("color: green;")
            self.current_boss_statuses = new_statuses
            self._update_gui_from_statuses(self.current_boss_statuses)
            QTimer.singleShot(3000, lambda: self.status_label.setText(f"Monitoring aktivní...") if self.monitoring_timer.isActive() else None)
            QTimer.singleShot(3000, lambda: self.status_label.setStyleSheet("color: blue;") if self.monitoring_timer.isActive() else None)
        else:
            print("Monitoring tick: Žádné změny.")
            # Using QTime.currentTime() requires importing QTime from PySide6.QtCore
            # For simplicity, just a generic message for now.
            # from PySide6.QtCore import QTime
            # self.status_label.setText(f"Monitoring aktivní (kontrola {QTime.currentTime().toString('hh:mm:ss')})...")
            self.status_label.setText(f"Monitoring aktivní (kontrola proběhla)...")


    def _get_statuses_via_rust_cli(self):
        if not self.all_event_ids_to_monitor:
            return {}
        if not self.RUST_CLI_TOOL_PATH or not os.path.exists(self.RUST_CLI_TOOL_PATH):
            print(f"CHYBA: Rust CLI tool path not valid: {self.RUST_CLI_TOOL_PATH}")
            return None


        event_ids_str_list = [str(eid) for eid in self.all_event_ids_to_monitor]
        command = [
            self.RUST_CLI_TOOL_PATH,
            "--slot-index", str(self.current_slot_index_for_monitoring),
            "--event-ids", ",".join(event_ids_str_list),
            self.current_save_file_path_for_monitoring
        ]
        
        try:
            process = subprocess.run(command, capture_output=True, text=True, check=False, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

            if process.returncode != 0:
                print(f"CHYBA: Rust CLI selhal (kód {process.returncode}): {process.stderr}")
                self.status_label.setText(f"Rust CLI Error: {process.stderr[:100]}...") 
                self.status_label.setStyleSheet("color: red;")
                return None
            
            if not process.stdout.strip():
                print("CHYBA: Rust CLI nevrátil žádný výstup.")
                self.status_label.setText("Rust CLI no output.")
                self.status_label.setStyleSheet("color: red;")
                return None
                
            return json.loads(process.stdout) 
        except FileNotFoundError: 
            print(f"CHYBA: Rust CLI nebyl nalezen při pokusu o spuštění: {self.RUST_CLI_TOOL_PATH}")
            self.status_label.setText("Rust CLI not found during execution.")
            self.status_label.setStyleSheet("color: red;")
            return None
        except json.JSONDecodeError as e:
            print(f"CHYBA: Nepodařilo se dekódovat JSON z Rust CLI: {e}. Výstup: '{process.stdout}'")
            self.status_label.setText("Chyba JSON z Rust CLI.")
            self.status_label.setStyleSheet("color: red;")
            return None
        except Exception as e:
            print(f"CHYBA při volání Rust CLI nebo parsování výstupu: {e}")
            self.status_label.setText("Obecná chyba Rust CLI.")
            self.status_label.setStyleSheet("color: red;")
            return None

    def _update_gui_from_statuses(self, statuses_dict, initial_scan=False):
        if not self.boss_data_by_location : 
            if initial_scan: 
                print("DEBUG: _update_gui_from_statuses - chybí referenční data, pokus o načtení.")
                script_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.dirname(script_dir)
                default_reference_path = os.path.join(project_root, "data", "Bosses", "boss_ids_reference.json") # CHANGED FILENAME
                if not self.load_reference_boss_definitions(default_reference_path):
                    self.status_label.setText("CHYBA: Chybí referenční data bossů pro aktualizaci GUI.")
                    return
            else: 
                self.status_label.setText("CHYBA: Chybí referenční data bossů pro aktualizaci GUI (po inicializaci).")
                return


        for location, bosses_in_location in self.boss_data_by_location.items():
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

    def populate_boss_tree(self):
        self.boss_tree.clear()

        if not self.boss_data_by_location:
            return

        # Colors are now imported from styles.py and used directly
        # DEFEATED_TEXT_COLOR, NOT_DEFEATED_TEXT_COLOR, LOCATION_TEXT_COLOR,
        # BOSS_NAME_TEXT_COLOR, LOCATION_ITEM_BG_COLOR, BOSS_ITEM_BG_COLOR

        total_bosses_overall = 0
        sorted_locations = sorted(self.boss_data_by_location.items())

        for location_name, bosses_in_location in sorted_locations:
            location_item = QTreeWidgetItem(self.boss_tree)
            
            boss_count_in_location = 0
            defeated_count_in_location = 0
            if isinstance(bosses_in_location, list):
                boss_count_in_location = len(bosses_in_location)
                total_bosses_overall += boss_count_in_location # Accumulate total
                for boss_info_count in bosses_in_location:
                    if isinstance(boss_info_count, dict) and boss_info_count.get("is_defeated", False):
                        defeated_count_in_location +=1
            
            display_location_name = f"📖 {location_name} ({defeated_count_in_location}/{boss_count_in_location})"
            location_item.setText(1, display_location_name) # Location name in second column
            location_item.setForeground(1, LOCATION_TEXT_COLOR)
            location_item.setBackground(0, LOCATION_ITEM_BG_COLOR) # Apply to all columns of location item
            location_item.setBackground(1, LOCATION_ITEM_BG_COLOR)

            font = location_item.font(1)
            font.setBold(True)
            location_item.setFont(1, font)
            location_item.setFont(0, font) # Also bold for potential status in location row (if any)

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
                    status_text_label = "Defeated" if is_defeated else "Not Defeated" # English for consistency with image
                    
                    boss_name_text = boss_info.get("name", "N/A")
                    
                    boss_list_item = QTreeWidgetItem(location_item)
                    boss_list_item.setText(0, f"{status_icon} {status_text_label}")
                    boss_list_item.setForeground(0, DEFEATED_TEXT_COLOR if is_defeated else NOT_DEFEATED_TEXT_COLOR)
                    
                    boss_list_item.setText(1, f"💀 {boss_name_text}")
                    boss_list_item.setForeground(1, BOSS_NAME_TEXT_COLOR)

                    # Apply default boss item background
                    boss_list_item.setBackground(0, BOSS_ITEM_BG_COLOR)
                    boss_list_item.setBackground(1, BOSS_ITEM_BG_COLOR)

                    location_item.setExpanded(True) # Expand locations by default to show bosses
            else:
                 child = QTreeWidgetItem(location_item, ["", "Chybný formát bossů pro tuto lokaci"])
                 child.setBackground(0, BOSS_ITEM_BG_COLOR)
                 child.setBackground(1, BOSS_ITEM_BG_COLOR)

        self.total_boss_count_label.setText(f"Celkový počet bossů: {total_bosses_overall}")

        for i in range(self.boss_tree.columnCount()):
            if i == 1: self.boss_tree.header().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else: self.boss_tree.header().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

def main():
    app = QApplication(sys.argv)
    window = BossChecklistApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()