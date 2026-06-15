# src/overlay_manager.py

from html import escape

from PySide6.QtWidgets import QApplication, QColorDialog
from PySide6.QtCore import QPoint, QSettings
from PySide6.QtGui import QColor

from ...config.app_config import DEFAULT_OVERLAY_TEXT_COLOR_STR, DEFAULT_OVERLAY_FONT_SIZE_STR
from ...utils import format_seconds_to_hms
from .global_hotkeys import GlobalHotkeys, VK_F8, VK_F9

class OverlayManager:
    def __init__(self, main_app_ref, overlay_window_ref, settings_panel_ref,
                 text_color_button_ref, font_size_combobox_ref, settings_button_ref,
                 show_bosses_ref, show_deaths_ref, show_time_ref, show_seconds_ref,
                 show_last_boss_ref): # <--- NOVÝ PARAMETR
        
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
        self.show_last_boss_checkbox = show_last_boss_ref # <--- NOVÁ REFERENCE
        
        self.settings = QSettings("TheTarnishedChronicle", "App")
        self.last_known_stats = {}

        self._mode = self.settings.value("overlay/mode", "mini")
        self._last_boss_list_key = None
        self.hotkeys = GlobalHotkeys()

        self.load_settings()
        self.connect_signals()
        self.overlay_window.set_mode(self._mode)

    def connect_signals(self):
        """Propojí UI prvky s jejich funkcemi."""
        self.text_color_button.clicked.connect(self.pick_text_color)
        self.font_size_combobox.currentTextChanged.connect(self.apply_settings)
        self.show_bosses_checkbox.stateChanged.connect(self.force_ui_update)
        self.show_deaths_checkbox.stateChanged.connect(self.force_ui_update)
        self.show_time_checkbox.stateChanged.connect(self.force_ui_update)
        self.show_seconds_checkbox.stateChanged.connect(self.force_ui_update)
        self.show_last_boss_checkbox.stateChanged.connect(self.force_ui_update) # <--- NOVÉ PROPOJENÍ
        self.overlay_window.position_changed.connect(self._save_overlay_position)

    def _save_overlay_position(self, pos: QPoint):
        self.settings.setValue("overlay/posX", pos.x())
        self.settings.setValue("overlay/posY", pos.y())

    def _load_overlay_position(self):
        """Returns the saved overlay position, or None when there is none
        or it lies outside all current screens (e.g. unplugged monitor)."""
        if not self.settings.contains("overlay/posX"):
            return None
        pos = QPoint(
            self.settings.value("overlay/posX", 0, type=int),
            self.settings.value("overlay/posY", 0, type=int),
        )
        for screen in QApplication.screens():
            if screen.geometry().contains(pos):
                return pos
        return None

    def load_settings(self):
        """Načte uložená nastavení a aplikuje je na UI prvky."""
        # ... (tato metoda zůstává beze změny) ...
        self.show_bosses_checkbox.setChecked(self.settings.value("overlay/showBosses", True, type=bool))
        self.show_deaths_checkbox.setChecked(self.settings.value("overlay/showDeaths", False, type=bool))
        self.show_time_checkbox.setChecked(self.settings.value("overlay/showTime", False, type=bool))
        self.show_seconds_checkbox.setChecked(self.settings.value("overlay/showSeconds", True, type=bool))
        self.show_last_boss_checkbox.setChecked(self.settings.value("overlay/showLastBoss", True, type=bool)) # <--- NOVÉ
        
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
        self.settings.setValue("overlay/showLastBoss", self.show_last_boss_checkbox.isChecked()) # <--- NOVÉ
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
            current_stats = self.app.app_logic._get_current_stats_payload()
            
            # 2. Uložíme si je, aby je ostatní metody mohly použít.
            self.last_known_stats = current_stats.copy()
            
            # 3. Vynutíme sestavení a nastavení textu. TOTO JE KLÍČOVÉ.
            # Voláme _render_text() přímo, bez ohledu na to, zda je okno viditelné.
            self._render_text()
            
            # 4. Až TEĎ, s již připraveným a nastaveným textem, okno zobrazíme.
            self._last_boss_list_key = None  # Force a rebuild of the boss list
            self._refresh_boss_list()
            self.overlay_window.show_overlay(self._load_overlay_position())

            # Hotkeys live only while the overlay is visible, so F8/F9
            # stay free for other apps the rest of the time.
            self.hotkeys.register(VK_F8, self.toggle_mode)
            self.hotkeys.register(VK_F9, self.toggle_click_through)
        else:
            self.hotkeys.unregister_all()
            # Při vypnutí okno jednoduše skryjeme.
            self.overlay_window.hide_overlay() # Použijeme metodu z OverlayWindow pro konzistenci

    def toggle_mode(self):
        """Switches the overlay between 'mini' and 'full' (boss list) mode."""
        self._mode = "full" if self._mode == "mini" else "mini"
        self.settings.setValue("overlay/mode", self._mode)
        self._last_boss_list_key = None
        self._refresh_boss_list()
        self.overlay_window.set_mode(self._mode)

    def toggle_click_through(self):
        self.overlay_window.set_click_through(not self.overlay_window.is_click_through())


    def update_text(self, stats: dict):
        """
        Aktualizuje text na základě kompletních dat (např. z monitoringu).
        Tato metoda se volá, když už je overlay pravděpodobně viditelný.
        """
        self.last_known_stats = stats.copy()
        # Pokud je overlay viditelný, okamžitě překreslíme text.
        if self.overlay_window.isVisible():
            self._render_text()
            self._refresh_boss_list()

    def force_ui_update(self):
        """Vynutí překreslení textu na základě posledních známých dat a aktuálního nastavení."""
        # Pokud máme vybranou postavu, překreslíme.
        if self.app.save_monitor_logic.current_slot_index != -1:
            self._render_text()
            
    def _refresh_boss_list(self):
        """Rebuilds the full-mode boss list, but only when the underlying
        data actually changed — update_text() fires every second for the
        live timer and rebuilding rich text that often would be wasteful."""
        if self._mode != "full":
            return

        data = self.app.boss_data_manager.get_boss_data_by_location()
        key = tuple(
            (location, tuple(
                (boss.get("name"), bool(boss.get("is_defeated")))
                for boss in bosses if isinstance(boss, dict)
            ))
            for location, bosses in data.items() if isinstance(bosses, list)
        )
        if key == self._last_boss_list_key:
            return
        self._last_boss_list_key = key
        self.overlay_window.set_boss_list_html(self._build_boss_list_html(data))

    def _build_boss_list_html(self, data: dict) -> str:
        rows = []
        for location, bosses in data.items():
            if not isinstance(bosses, list) or not bosses:
                continue
            valid = [b for b in bosses if isinstance(b, dict)]
            defeated = sum(1 for b in valid if b.get("is_defeated"))
            rows.append(
                f"<div style='margin-top:8px;'><span style='color:#88C0D0;'>"
                f"{escape(str(location))} ({defeated}/{len(valid)})</span></div>"
            )
            for boss in valid:
                name = escape(str(boss.get("name", "Unknown")))
                if boss.get("is_defeated"):
                    rows.append(f"<div style='color:#A3BE8C;'>✓ <s>{name}</s></div>")
                else:
                    rows.append(f"<div style='color:#D8DEE9;'>○ {name}</div>")

        if not rows:
            return "<i>Select a character...</i>"
        return (
            "<div style='font-size:10pt; font-weight:normal;'>"
            + "".join(rows)
            + "</div>"
        )

    def _render_text(self):
        """Interní metoda, která sestaví a zobrazí finální text v overlayi."""
        if not self.last_known_stats:
            self.overlay_window.set_text("Select a character...")
            return

        parts = []
        stats = self.last_known_stats.get("stats", {})
        
        if self.show_bosses_checkbox.isChecked():
            parts.append(f"Bosses: {stats.get('defeated', '--')}/{stats.get('total', '--')}")
        if self.show_deaths_checkbox.isChecked():
            parts.append(f"Deaths: {stats.get('deaths', '--')}")
        if self.show_time_checkbox.isChecked():
            # ... (logika pro zobrazení času zůstává stejná)
            seconds = stats.get('seconds_played', -1)
            if seconds >= 0:
                h, rem = divmod(seconds, 3600)
                m, s = divmod(rem, 60)
                time_str = f"{int(h):02d}:{int(m):02d}"
                if self.show_seconds_checkbox.isChecked():
                    time_str += f":{int(s):02d}"
                parts.append(f"Time: {time_str}")
            else:
                parts.append("Time: --:--:--")

        
        # Sestavíme první řádek
        final_text = " | ".join(parts)
        
        # --- NOVÁ LOGIKA PRO DRUHÝ ŘÁDEK ---
        if self.show_last_boss_checkbox.isChecked():
            last_kill = self.last_known_stats.get("last_kill")
            if last_kill and last_kill.get("name"):
                boss_name = last_kill["name"]
                kill_time_str = format_seconds_to_hms(last_kill["time"])
                
                # Pokud je první řádek prázdný, nepřidáváme zbytečný newline
                if final_text:
                    final_text += f"\n{boss_name} {kill_time_str}"
                else:
                    final_text = f"{boss_name} {kill_time_str}"

        # Pokud je po všem text stále prázdný, zobrazíme výchozí
        final_text = final_text or "Overlay Active"
        self.overlay_window.set_text(final_text)