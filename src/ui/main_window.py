# src/gui.py
import sys
import os
import json
import time
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QLineEdit, QCheckBox, QFrame, QMessageBox, QStackedLayout
)
from .widgets.resizing_stacked_widget import ResizingStackedWidget
from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QIcon

from .styles import apply_app_styles
from .widgets.overlay_window import OverlayWindow
from .managers.overlay_manager import OverlayManager
from .layouts import (
    create_file_slot_layout, create_main_boss_area,
    create_overlay_settings_panel_layout, create_obs_panel_layout
)
from .widgets.location_section import LocationSectionWidget
from .widgets.footer import FooterWidget
from .widgets.stats_section import StatsSectionWidget
from .widgets.empty_state_widget import EmptyStateWidget
from .dialogs.boss_stats_dialog import BossStatsDialog
from .dialogs.location_dialog import LocationDialog
from src.config.app_config import (
    RUST_CLI_TOOL_PATH_PLACEHOLDER,
    DEFAULT_BOSS_REFERENCE_FILENAME,
    DLC_BOSS_REFERENCE_FILENAME,
    LOCATION_PROGRESSION_ORDER
)
from src.services.rust_cli_handler import RustCliHandler
from src.domain.boss_data_manager import BossDataManager
from src.services.save_monitor_logic import SaveMonitorLogic
from .managers.obs_manager import ObsManager
from src.domain.timestamp_manager import TimestampManager
from src.services.update_checker import UpdateChecker
from src.app_logic import AppLogic
from src.utils import get_resource_path
import webbrowser

class BossChecklistApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("The Tarnished's Chronicle")
        self.setGeometry(600, 200, 1000, 900)
        self.setWindowIcon(QIcon(get_resource_path("assets/icons/app_logo.ico")))

        self._init_managers()
        self.app_logic = AppLogic(self)
        self.boss_data_manager.load_definitions()
        self._init_ui()
        self.load_and_apply_filters()
        self.boss_data_manager.set_custom_preset(self._load_custom_preset_ids())
        self.boss_data_manager.set_type_filter(self.type_filter_combobox.currentData())
        self.boss_data_manager.set_content_filter(self.content_filter_combobox.currentData())
        self._init_overlay_and_obs_managers()
        self._connect_signals()
        self.app_logic.update_main_boss_area(clear=True)
        if self.character_slot_combobox.currentIndex() > 0:
            self.app_logic.handle_character_selection_change(self.character_slot_combobox.currentIndex())
        apply_app_styles(self)
        self.browse_button.setEnabled(True) # Final override to ensure the button is enabled

    def _init_managers(self):
        self.settings = QSettings("TheTarnishedChronicle", "App")
        self.boss_data_manager = BossDataManager(
            base_filename=DEFAULT_BOSS_REFERENCE_FILENAME,
            dlc_filename=DLC_BOSS_REFERENCE_FILENAME
        )
        self.rust_cli_handler = RustCliHandler(RUST_CLI_TOOL_PATH_PLACEHOLDER)
        self.save_monitor_logic = SaveMonitorLogic(self.rust_cli_handler, self.boss_data_manager, self)
        self.timestamp_manager = TimestampManager()
        self.ui_timer = QTimer(self)
        self.ui_timer.setInterval(1000)
        self.location_widgets = {}
        self.update_checker = UpdateChecker(self)

    def _init_overlay_and_obs_managers(self):
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
            show_last_boss_ref=self.overlay_show_last_boss
        )
        self.obs_manager = ObsManager(
            main_app_ref=self,
            obs_panel_ref=self.obs_panel,
            settings_button_ref=self.obs_settings_button,
            enable_toggle_ref=self.obs_enable_toggle,
            folder_label_ref=self.obs_folder_path_label,
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

    def _init_ui(self):
        self._setup_main_layout()
        self._create_sidebar()
        self._create_content_area()
        
        saved_path = self.settings.value("saveFilePath", "")
        if os.path.exists(saved_path):
            self.save_file_path_label.setText(saved_path)
            self.app_logic.on_save_file_path_changed(saved_path)
        else:
            self.save_file_path_label.setText("Please select a save file...")
            self.character_slot_combobox.clear()
            self.character_slot_combobox.setPlaceholderText("Select a character")
            self.character_slot_combobox.setEnabled(False)
            self.browse_button.setEnabled(True)
            self.update_onboarding_state("select_file")

    def _setup_main_layout(self):
        overall_layout = QVBoxLayout(self)
        overall_layout.setContentsMargins(0, 0, 0, 0)
        overall_layout.setSpacing(0)
        
        self.footer = FooterWidget()

        top_part_widget = QWidget()
        self.main_h_layout = QHBoxLayout(top_part_widget)
        self.main_h_layout.setContentsMargins(0, 0, 0, 0)
        self.main_h_layout.setSpacing(0)

        overall_layout.addWidget(top_part_widget)
        overall_layout.addWidget(self.footer)
        self.setLayout(overall_layout)

    def _create_sidebar(self):
        sidebar_frame = QFrame()
        sidebar_frame.setObjectName("sidebar")
        sidebar_frame.setFixedWidth(300)
        
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(15, 15, 15, 15)
        sidebar_layout.setSpacing(10)
        self.file_slot_layout = create_file_slot_layout(self)
        sidebar_layout.addLayout(self.file_slot_layout)

        
        self.stats_section = StatsSectionWidget()
        sidebar_layout.addWidget(self.stats_section)

        sidebar_layout.addStretch(1)
        self.main_h_layout.addWidget(sidebar_frame)

    def _create_content_area(self):
        content_widget = QWidget()
        content_widget.setObjectName("mainContent")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(15, 10, 15, 10)
        content_layout.setSpacing(10)
        
        # No parent on purpose: a parented Qt.Tool window is hidden by Windows
        # whenever the main window is minimized, taking the overlay with it.
        self.overlay_window = OverlayWindow()
        
        top_buttons_layout = QHBoxLayout()
        self.toggle_overlay_button = QPushButton("Toggle Overlay")
        self.toggle_overlay_button.setCheckable(True)
        top_buttons_layout.addWidget(self.toggle_overlay_button)
        self.overlay_settings_button = QPushButton("Overlay Settings")
        top_buttons_layout.addWidget(self.overlay_settings_button)
        self.obs_settings_button = QPushButton("OBS Overlay")
        top_buttons_layout.addWidget(self.obs_settings_button)
        content_layout.addLayout(top_buttons_layout)
        
        # Create a container for the settings panels using the new resizing widget
        self.settings_stack = ResizingStackedWidget()
        self.overlay_settings_panel = create_overlay_settings_panel_layout(self)
        self.obs_panel = create_obs_panel_layout(self)
        
        # Add a blank widget as the default page (index 0)
        self.settings_stack.addWidget(QWidget())
        self.settings_stack.addWidget(self.overlay_settings_panel) # Index 1
        self.settings_stack.addWidget(self.obs_panel) # Index 2
        
        self.settings_stack.setVisible(False) # Hide the whole stack initially
        content_layout.addWidget(self.settings_stack)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search for a boss or location...")
        content_layout.addWidget(self.search_bar)
        self.main_boss_area_widget = create_main_boss_area(self)
        
        # Add the new empty state widget
        self.empty_state_widget = EmptyStateWidget()
        
        # Add both to a stacked layout to easily switch between them
        self.main_content_stack = QStackedLayout()
        self.main_content_stack.addWidget(self.main_boss_area_widget)
        self.main_content_stack.addWidget(self.empty_state_widget)
        
        content_layout.addLayout(self.main_content_stack)
        self.main_h_layout.addWidget(content_widget)

    def _connect_signals(self):
        self.save_monitor_logic.monitoring_started.connect(self.app_logic._handle_monitoring_started)
        self.save_monitor_logic.monitoring_stopped.connect(self.app_logic._handle_monitoring_stopped)
        self.save_monitor_logic.stats_updated.connect(self.app_logic.handle_stats_update)
        
        self.browse_button.clicked.connect(self.app_logic.browse_for_save_file)
        self.character_slot_combobox.currentIndexChanged.connect(self.app_logic.handle_character_selection_change)
        self.character_slot_combobox.currentIndexChanged.connect(self.obs_manager.on_character_changed)
        
        self.content_filter_combobox.currentIndexChanged.connect(self.app_logic.handle_content_filter_change)
        self.type_filter_combobox.currentIndexChanged.connect(self.app_logic.handle_type_filter_change)
        self.edit_custom_filter_button.clicked.connect(self.app_logic.open_custom_filter_dialog)
        self.hide_defeated_checkbox.stateChanged.connect(self.app_logic.handle_status_filter_change)
        
        self.search_bar.textChanged.connect(self.app_logic.on_search_text_changed)
        
        self.toggle_overlay_button.toggled.connect(self.overlay_manager.on_toggle_overlay)
        self.overlay_settings_button.clicked.connect(self.app_logic.toggle_overlay_settings)
        self.obs_settings_button.clicked.connect(self.app_logic.toggle_obs_settings)

        self.ui_timer.timeout.connect(self.app_logic.update_live_timer)
        
        self.save_monitor_logic.boss_defeated.connect(self.app_logic.on_boss_defeated)
        self.save_monitor_logic.game_process_status.connect(self.app_logic.on_game_process_status_changed)
        self.update_checker.update_available.connect(self.show_update_dialog)

    def load_and_apply_filters(self):
        """Loads filter settings from QSettings and applies them to the UI controls."""
        # Content Filter
        saved_filter_mode = self.settings.value("filters/contentMode", "all", type=str)
        index = self.content_filter_combobox.findData(saved_filter_mode)
        if index != -1:
            self.content_filter_combobox.setCurrentIndex(index)
        
        # Boss Type Filter
        saved_type_mode = self.settings.value("filters/typeMode", "all", type=str)
        index = self.type_filter_combobox.findData(saved_type_mode)
        if index != -1:
            self.type_filter_combobox.setCurrentIndex(index)
        self.edit_custom_filter_button.setVisible(saved_type_mode == "custom")

        # Hide Defeated Filter
        hide_defeated = self.settings.value("filters/hideDefeated", False, type=bool)
        self.hide_defeated_checkbox.setChecked(hide_defeated)

    def _load_custom_preset_ids(self):
        """Loads the saved custom boss preset (list of event IDs) from QSettings."""
        saved = self.settings.value("filters/customPresetIds", "[]", type=str)
        try:
            return {str(eid) for eid in json.loads(saved)}
        except (ValueError, TypeError):
            print(f"Warning: invalid custom preset in settings, ignoring: {saved!r}")
            return set()

    def update_onboarding_state(self, state: str):
        """
        Controls the UI during the initial setup process, guiding the user.
        - Shows/hides the empty state message.
        - Highlights the next required action.
        """
        if state == "select_file":
            self.main_content_stack.setCurrentWidget(self.empty_state_widget)
            self.empty_state_widget.set_state("select_file")
            self.browse_button.setObjectName("highlighted")
            self.character_slot_combobox.setObjectName("")
        elif state == "select_character":
            self.main_content_stack.setCurrentWidget(self.empty_state_widget)
            self.empty_state_widget.set_state("select_character")
            self.browse_button.setObjectName("")
            self.character_slot_combobox.setObjectName("highlighted")
        elif state == "done":
            self.main_content_stack.setCurrentWidget(self.main_boss_area_widget)
            self.browse_button.setObjectName("")
            self.character_slot_combobox.setObjectName("")
        
        # Re-apply stylesheet to make the #highlighted style take effect
        apply_app_styles(self)

    def show_update_dialog(self, manifest_data: dict):
        """
        Zobrazí dialog s informací o nové verzi na základě dat z manifestu.
        """
        version = manifest_data.get("version", "N/A")
        notes = manifest_data.get("notes", "No release notes provided.")
        url = manifest_data.get("url")

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Update Available")
        msg_box.setText(f"<b>A new version ({version}) is available.</b>")
        msg_box.setInformativeText(f"<b>Release Notes:</b>\n{notes}\n\nDo you want to download and install it now?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            if url:
                self.app_logic.start_update_download(manifest_data)
            else:
                QMessageBox.warning(self, "Error", "Download URL is missing in the update manifest.")

    def show_update_error_dialog(self, message: str):
        """Zobrazí dialog s chybou při aktualizaci."""
        QMessageBox.critical(self, "Update Error", message)

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        if self.overlay_manager and self.overlay_manager.overlay_window:
            self.overlay_manager.overlay_window.close()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    
    # Set application icon
    # The icon is now set in the BossChecklistApp's __init__ method using get_resource_path,
    # so we no longer need to set it here. This ensures the icon works in both
    # development and packaged environments.
    
    window = BossChecklistApp()
    window.show()
    window.update_checker.check_for_updates()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()