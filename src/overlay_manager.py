# src/overlay_manager.py
from PySide6.QtWidgets import QColorDialog
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor

from .app_config import (
    DEFAULT_OVERLAY_BG_COLOR_STR, DEFAULT_OVERLAY_TEXT_COLOR_STR,
    DEFAULT_OVERLAY_FONT_SIZE_STR
)

class OverlayManager:
    def __init__(self, main_app_ref, overlay_window_ref, boss_data_manager_ref,
                 settings_panel_ref, bg_color_button_ref, text_color_button_ref,
                 font_size_input_ref, settings_button_ref):
        self.app = main_app_ref # Reference to the main BossChecklistApp instance
        self.overlay_window = overlay_window_ref
        self.boss_data_manager = boss_data_manager_ref
        
        # UI Elements from BossChecklistApp
        self.settings_panel = settings_panel_ref
        self.bg_color_button = bg_color_button_ref
        self.text_color_button = text_color_button_ref
        self.font_size_input = font_size_input_ref
        self.settings_button = settings_button_ref # To update its text

        # Overlay state
        self.selected_bg_color = QColor(DEFAULT_OVERLAY_BG_COLOR_STR)
        self.selected_text_color = QColor(DEFAULT_OVERLAY_TEXT_COLOR_STR)
        self.current_font_size_str = DEFAULT_OVERLAY_FONT_SIZE_STR

        # Initialize UI elements related to overlay settings
        self.font_size_input.setText(self.current_font_size_str)
        self._update_color_button_style(self.bg_color_button, self.selected_bg_color)
        self._update_color_button_style(self.text_color_button, self.selected_text_color, is_text_color=True)

        # Apply initial styles to the overlay window
        self.apply_settings()

    def toggle_overlay_visibility(self):
        if self.overlay_window.isVisible():
            self.overlay_window.hide_overlay()
        else:
            self.update_text_if_visible(force_show=True)

    def update_text_if_visible(self, force_show=False):
        boss_data = self.boss_data_manager.get_boss_data_by_location()
        if not boss_data:
            if force_show or self.overlay_window.isVisible():
                self.overlay_window.set_text("Bosses: N/A (No data)")
                if force_show: self.overlay_window.show_overlay()
            return

        defeated_boss_count = 0
        total_bosses = 0
        for _, bosses_in_location in boss_data.items():
            if isinstance(bosses_in_location, list):
                total_bosses += len(bosses_in_location)
                for b_info in bosses_in_location:
                    if isinstance(b_info, dict) and b_info.get("is_defeated"):
                        defeated_boss_count += 1
        
        text_to_display = f"Bosses Defeated: {defeated_boss_count}/{total_bosses}"
        if total_bosses == 0: text_to_display = "Bosses: N/A"

        if force_show or self.overlay_window.isVisible():
            self.overlay_window.set_text(text_to_display)
            if force_show:
                self.overlay_window.show_overlay()

    def toggle_settings_panel_visibility(self):
        is_visible = not self.settings_panel.isVisible()
        self.settings_panel.setVisible(is_visible)
        self.settings_button.setText("Hide Settings" if is_visible else "Overlay Settings")

    def _update_color_button_style(self, button, color, is_text_color=False):
        button.setText(color.name(QColor.NameFormat.HexArgb))
        text_on_button_color = "black" if color.lightnessF() > 0.5 and not is_text_color else "white"
        if is_text_color:
            button.setStyleSheet(f"QPushButton {{ background-color: #333; color: {color.name()}; border: 1px solid {color.name()}; }}")
        else:
            button.setStyleSheet(f"QPushButton {{ background-color: {color.name()}; color: {text_on_button_color}; border: 1px solid grey; }}")

    def pick_background_color(self):
        # Pass the main app window as parent for the dialog
        color_dialog = QColorDialog(self.selected_bg_color, self.app)
        color_dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, True)
        color_dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True) # Force Qt's dialog
        if color_dialog.exec():
            self.selected_bg_color = color_dialog.selectedColor()
            self._update_color_button_style(self.bg_color_button, self.selected_bg_color)

    def pick_text_color(self):
        color_dialog = QColorDialog(self.selected_text_color, self.app)
        color_dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, True)
        if color_dialog.exec():
            self.selected_text_color = color_dialog.selectedColor()
            self._update_color_button_style(self.text_color_button, self.selected_text_color, is_text_color=True)

    def apply_settings(self):
        bg_color_str = f"rgba({self.selected_bg_color.red()},{self.selected_bg_color.green()},{self.selected_bg_color.blue()},{self.selected_bg_color.alpha()})"
        text_color_str = f"rgba({self.selected_text_color.red()},{self.selected_text_color.green()},{self.selected_text_color.blue()},{self.selected_text_color.alpha()})"
        
        font_size = self.font_size_input.text()
        if not font_size: font_size = DEFAULT_OVERLAY_FONT_SIZE_STR
        self.current_font_size_str = font_size

        self.overlay_window.update_styles(
            background_color=bg_color_str,
            text_color=text_color_str,
            font_size=font_size
        )
        