# Finální verze souboru: src/gui.py
import sys
import os
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QLineEdit, QCheckBox, QFrame
)
from PySide6.QtCore import Qt, QTimer, QSettings

from .styles import apply_app_styles
from .overlay_window import OverlayWindow
from .ui_components import (
    create_file_slot_layout, create_main_boss_area,
    create_overlay_settings_panel_layout, LocationSectionWidget, FooterWidget
)
# OPRAVENÝ IMPORT: Přidáme i GAME_PHASE_HEADINGS
from .app_config import (
    RUST_CLI_TOOL_PATH_PLACEHOLDER, DEFAULT_BOSS_REFERENCE_FILENAME,
    LOCATION_PROGRESSION_ORDER, GAME_PHASE_HEADINGS
)
from .rust_cli_handler import RustCliHandler
from .boss_data_manager import BossDataManager
from .save_monitor_logic import SaveMonitorLogic
from .overlay_manager import OverlayManager

class BossChecklistApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Tarnished's Chronicle")
        self.setGeometry(150, 150, 1000, 750)

        self.settings = QSettings("TheTarnishedChronicle", "App")
        self.rust_cli_handler = RustCliHandler(RUST_CLI_TOOL_PATH_PLACEHOLDER)
        self.boss_data_manager = BossDataManager(DEFAULT_BOSS_REFERENCE_FILENAME)
        self.save_monitor_logic = SaveMonitorLogic(self.rust_cli_handler, self.boss_data_manager, self)
        
        self.init_ui()

        self.overlay_manager = OverlayManager(
            main_app_ref=self,
            overlay_window_ref=self.overlay_window,
            boss_data_manager_ref=self.boss_data_manager,
            settings_panel_ref=self.overlay_settings_panel,
            bg_color_button_ref=self.overlay_bg_color_button,
            text_color_button_ref=self.overlay_text_color_button,
            font_size_input_ref=self.overlay_font_size_input,
            settings_button_ref=self.overlay_settings_button
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
        overlay_buttons_layout = QHBoxLayout()
        self.toggle_overlay_button = QPushButton("Toggle Overlay")
        overlay_buttons_layout.addWidget(self.toggle_overlay_button)
        self.overlay_settings_button = QPushButton("Overlay Settings")
        overlay_buttons_layout.addWidget(self.overlay_settings_button)
        content_layout.addLayout(overlay_buttons_layout)
        self.overlay_settings_panel = create_overlay_settings_panel_layout(self)
        self.overlay_settings_panel.setVisible(False)
        content_layout.addWidget(self.overlay_settings_panel)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Hledat bosse nebo lokaci...")
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
        self.save_monitor_logic.boss_statuses_changed.connect(self._handle_boss_statuses_changed)
        self.save_monitor_logic.initial_boss_statuses_loaded.connect(self._handle_initial_boss_statuses_loaded)
        self.browse_button.clicked.connect(self.browse_for_save_file)
        self.character_slot_combobox.currentIndexChanged.connect(self.handle_character_selection_change)
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        self.toggle_overlay_button.clicked.connect(self.overlay_manager.toggle_overlay_visibility)
        self.overlay_settings_button.clicked.connect(self.overlay_manager.toggle_settings_panel_visibility)
        self.overlay_bg_color_button.clicked.connect(self.overlay_manager.pick_background_color)
        self.overlay_text_color_button.clicked.connect(self.overlay_manager.pick_text_color)
        self.apply_overlay_settings_button.clicked.connect(self.overlay_manager.apply_settings)

    def _handle_monitoring_started(self, char_name, interval):
        self.footer.update_monitoring_status(True)

    def _handle_monitoring_stopped(self):
        self.footer.update_monitoring_status(False)

    def _handle_boss_statuses_changed(self, new_statuses):
        if self.boss_data_manager.update_boss_statuses(new_statuses):
            self.footer.update_timestamp()
            self.populate_main_boss_area()
            self.overlay_manager.update_text_if_visible()

    def _handle_initial_boss_statuses_loaded(self, initial_statuses):
        if self.boss_data_manager.update_boss_statuses(initial_statuses):
            self.populate_main_boss_area()
            self.overlay_manager.update_text_if_visible()
    
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
            if char_info.get("character_name") and char_info.get("character_name") != "Error decoding name":
                display_name = f"{char_info['character_name']} (Level {char_info['character_level']})"
                self.character_slot_combobox.addItem(display_name, userData=char_info['slot_index'])
        
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
        start_dir = os.path.dirname(current_path) if os.path.exists(os.path.dirname(current_path)) else ""
        filepath, _ = QFileDialog.getOpenFileName(self, "Select Elden Ring Save File", start_dir, "SL2 Files (*.sl2)")
        if filepath:
            self.save_file_path_label.setText(filepath)
            self.settings.setValue("saveFilePath", filepath)
            self.on_save_file_path_changed(filepath)

    def _load_initial_boss_data(self):
        loaded, _ = self.boss_data_manager.load_reference_boss_definitions()
        if loaded:
            self.populate_main_boss_area()

    def handle_character_selection_change(self, index):
        self.save_monitor_logic.stop_monitoring()
        selected_data = self.character_slot_combobox.itemData(index)
        
        if index == 0 or selected_data is None:
            self.footer.update_monitoring_status(False)
            return

        self.settings.setValue("lastCharacterIndex", index)
        save_file_path = self.save_file_path_label.text()
        slot_index = selected_data
        char_name = self.character_slot_combobox.itemText(index)
        self.save_monitor_logic.start_monitoring(save_file_path, slot_index, char_name)

    # === FINÁLNÍ VERZE METODY PRO ŘAZENÍ A BAREVNÉ NADPISY ===
    def populate_main_boss_area(self):
        layout = self.main_boss_area_widget.widget().layout()
        while layout.count() > 1:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        boss_data = self.boss_data_manager.get_boss_data_by_location()
        if not boss_data:
            return

        order_map = {location: i for i, location in enumerate(LOCATION_PROGRESSION_ORDER)}
        all_locations = list(boss_data.items())

        sorted_locations = sorted(
            all_locations,
            key=lambda item: (order_map.get(item[0], float('inf')), item[0])
        )

        for location_name, bosses_list in sorted_locations:
            # Zkontrolujeme, zda se má před touto lokací zobrazit nadpis
            if location_name in GAME_PHASE_HEADINGS:
                # Načteme celá data pro nadpis (text i property)
                header_data = GAME_PHASE_HEADINGS[location_name]
                
                header_label = QLabel(header_data["text"])
                header_label.setObjectName("gamePhaseHeader")
                header_label.setAlignment(Qt.AlignCenter)
                
                # NASTAVÍME DYNAMICKOU VLASTNOST, kterou pak použije QSS
                header_label.setProperty("phase", header_data["property"])
                
                layout.insertWidget(layout.count() - 1, header_label)

            # Vložíme samotnou kartu lokace
            section = LocationSectionWidget(location_name, bosses_list, self.main_boss_area_widget.widget())
            layout.insertWidget(layout.count() - 1, section)
            
        defeated_count, total_count = self.boss_data_manager.get_boss_counts()
        self.footer.update_boss_count(defeated_count, total_count)

    def on_search_text_changed(self, text):
        search_term = text.lower().strip()
        layout = self.main_boss_area_widget.widget().layout()
        for i in range(layout.count() - 1):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, LocationSectionWidget):
                location_matches = search_term in widget.location_name.lower()
                boss_matches = any(search_term in b.get("name", "").lower() for b in widget.bosses_data)
                widget.setVisible(location_matches or boss_matches or not search_term)

def main():
    app = QApplication(sys.argv)
    window = BossChecklistApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()