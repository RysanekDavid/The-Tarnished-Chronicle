# src/overlay_manager.py

from PySide6.QtWidgets import QColorDialog
from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor

from .app_config import DEFAULT_OVERLAY_TEXT_COLOR_STR, DEFAULT_OVERLAY_FONT_SIZE_STR

class OverlayManager:
    def __init__(self, main_app_ref, overlay_window_ref, settings_panel_ref, 
                 text_color_button_ref, font_size_combobox_ref, settings_button_ref,
                 show_bosses_ref, show_deaths_ref, show_time_ref, show_seconds_ref):
        
        self.app = main_app_ref
        self.overlay_window = overlay_window_ref
        self.settings_panel = settings_panel_ref
        
        # Reference na UI prvky
        self.text_color_button = text_color_button_ref
        self.font_size_combobox = font_size_combobox_ref
        self.settings_button = settings_button_ref
        self.show_bosses_checkbox = show_bosses_ref
        self.show_deaths_checkbox = show_deaths_ref
        self.show_time_checkbox = show_time_ref
        self.show_seconds_checkbox = show_seconds_ref
        
        self.settings = QSettings("TheTarnishedChronicle", "App")
        self.last_known_stats = {}
        
        self.load_settings()
        self.connect_signals()

    def connect_signals(self):
        """Propojí UI prvky s jejich funkcemi."""
        self.text_color_button.clicked.connect(self.pick_text_color)
        self.font_size_combobox.currentTextChanged.connect(self.apply_settings)
        self.show_bosses_checkbox.stateChanged.connect(self.force_ui_update)
        self.show_deaths_checkbox.stateChanged.connect(self.force_ui_update)
        self.show_time_checkbox.stateChanged.connect(self.force_ui_update)
        self.show_seconds_checkbox.stateChanged.connect(self.force_ui_update)

    def load_settings(self):
        """Načte uložená nastavení a aplikuje je na UI prvky."""
        # ... (tato metoda zůstává beze změny) ...
        self.show_bosses_checkbox.setChecked(self.settings.value("overlay/showBosses", True, type=bool))
        self.show_deaths_checkbox.setChecked(self.settings.value("overlay/showDeaths", False, type=bool))
        self.show_time_checkbox.setChecked(self.settings.value("overlay/showTime", False, type=bool))
        self.show_seconds_checkbox.setChecked(self.settings.value("overlay/showSeconds", True, type=bool))
        
        color_str = self.settings.value("overlay/textColor", DEFAULT_OVERLAY_TEXT_COLOR_STR)
        font_size = self.settings.value("overlay/fontSize", DEFAULT_OVERLAY_FONT_SIZE_STR)
        
        self.font_size_combobox.setCurrentText(font_size)
        self.update_color_button(QColor(color_str))
        
        self.overlay_window.update_styles(color_str, font_size)


    def save_settings(self):
        """Uloží aktuální nastavení."""
        # ... (tato metoda zůstává beze změny) ...
        self.settings.setValue("overlay/showBosses", self.show_bosses_checkbox.isChecked())
        self.settings.setValue("overlay/showDeaths", self.show_deaths_checkbox.isChecked())
        self.settings.setValue("overlay/showTime", self.show_time_checkbox.isChecked())
        self.settings.setValue("overlay/showSeconds", self.show_seconds_checkbox.isChecked())
        self.settings.setValue("overlay/textColor", self.text_color.name(QColor.NameFormat.HexRgb))
        self.settings.setValue("overlay/fontSize", self.font_size_combobox.currentText())

    def apply_settings(self):
        """Aplikuje aktuální nastavení vzhledu a uloží je."""
        # ... (tato metoda zůstává beze změny) ...
        font_size = self.font_size_combobox.currentText()
        self.overlay_window.update_styles(self.text_color.name(QColor.NameFormat.HexRgb), font_size)
        self.save_settings()
        self.force_ui_update()


    def update_color_button(self, color: QColor):
        """Aktualizuje vzhled tlačítka pro výběr barvy."""
        # ... (tato metoda zůstává beze změny) ...
        self.text_color = color
        self.text_color_button.setText(color.name(QColor.NameFormat.HexRgb))
        text_color_on_button = "black" if color.lightness() > 127 else "white"
        self.text_color_button.setStyleSheet(f"background-color: {color.name()}; color: {text_color_on_button};")


    def pick_text_color(self):
        """Otevře dialog pro výběr barvy a aplikuje ji."""
        # ... (tato metoda zůstává beze změny) ...
        color = QColorDialog.getColor(initial=self.text_color, parent=self.app, title="Select Text Color")
        if color.isValid():
            self.update_color_button(color)
            self.apply_settings()

    # --- ZDE JE OČEKÁVANÁ OPRAVA ---
    def on_toggle_overlay(self, checked: bool):
        """
        Slot pro hlavní tlačítko Toggle Overlay. Aktivně načítá data
        a ZAJIŠŤUJE jejich okamžité zobrazení.
        """
        if checked:
            # 1. Získáme nejnovější data z hlavní aplikace.
            current_stats = self.app._get_current_stats_payload()
            
            # 2. Uložíme si je, aby je ostatní metody mohly použít.
            self.last_known_stats = current_stats.copy()
            
            # 3. Vynutíme sestavení a nastavení textu. TOTO JE KLÍČOVÉ.
            # Voláme _render_text() přímo, bez ohledu na to, zda je okno viditelné.
            self._render_text()
            
            # 4. Až TEĎ, s již připraveným a nastaveným textem, okno zobrazíme.
            self.overlay_window.show_overlay()
        else:
            # Při vypnutí okno jednoduše skryjeme.
            self.overlay_window.hide_overlay() # Použijeme metodu z OverlayWindow pro konzistenci

    def toggle_settings_panel(self):
        """Zobrazí/skryje panel nastavení."""
        is_visible = not self.settings_panel.isVisible()
        self.settings_panel.setVisible(is_visible)
        self.settings_button.setText("Hide Overlay Settings" if is_visible else "Overlay Settings")

    def update_text(self, stats: dict):
        """
        Aktualizuje text na základě kompletních dat (např. z monitoringu).
        Tato metoda se volá, když už je overlay pravděpodobně viditelný.
        """
        self.last_known_stats = stats.copy()
        # Pokud je overlay viditelný, okamžitě překreslíme text.
        if self.overlay_window.isVisible():
            self._render_text()

    def force_ui_update(self):
        """Vynutí překreslení textu na základě posledních známých dat a aktuálního nastavení."""
        # Pokud máme vybranou postavu, překreslíme.
        if self.app.save_monitor_logic.current_slot_index != -1:
            self._render_text()
            
    def _render_text(self):
        """Interní metoda, která sestaví a zobrazí finální text v overlayi."""
        # Pokud nemáme žádná data (např. na začátku), nic neděláme.
        if not self.last_known_stats:
            self.overlay_window.set_text("Select a character...")
            return

        stats_data = self.last_known_stats.get("stats", {})
        
        parts = []
        # Používáme data ze 'stats_data' a ne z kořene self.last_known_stats
        defeated = stats_data.get('defeated', '--')
        total = stats_data.get('total', '--')
        deaths = stats_data.get('deaths', '--')
        seconds = stats_data.get('seconds_played', -1)

        if self.show_bosses_checkbox.isChecked():
            parts.append(f"Bosses: {defeated}/{total}")
        if self.show_deaths_checkbox.isChecked():
            parts.append(f"Deaths: {deaths}")
        if self.show_time_checkbox.isChecked():
            if seconds >= 0:
                h, rem = divmod(seconds, 3600)
                m, s = divmod(rem, 60)
                time_str = f"{int(h):02d}:{int(m):02d}"
                if self.show_seconds_checkbox.isChecked():
                    time_str += f":{int(s):02d}"
                parts.append(f"Time: {time_str}")
            else:
                parts.append("Time: --:--:--")
        
        # Pokud nic není vybráno k zobrazení, zobrazí se "Overlay Active"
        final_text = " | ".join(parts) or "Overlay Active"
        self.overlay_window.set_text(final_text)