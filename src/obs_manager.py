# src/obs_manager.py

import os
from PySide6.QtWidgets import QFileDialog, QMessageBox, QGroupBox
from PySide6.QtCore import QSettings, Qt # <--- PŘIDÁN IMPORT Qt ZDE

class ObsManager:
    def __init__(self, main_app_ref, obs_panel_ref, settings_button_ref, 
                 enable_toggle_ref, folder_label_ref, browse_button_ref, 
                 instructions_button_ref, bosses_enabled_ref, bosses_format_ref,
                 deaths_enabled_ref, deaths_format_ref, time_enabled_ref, time_format_ref):
        
        self.app = main_app_ref
        self.panel = obs_panel_ref
        
        # UI References
        self.settings_button = settings_button_ref
        self.enable_toggle = enable_toggle_ref
        self.folder_label = folder_label_ref
        self.browse_button = browse_button_ref
        self.instructions_button = instructions_button_ref
        self.bosses_enabled = bosses_enabled_ref
        self.bosses_format = bosses_format_ref
        self.deaths_enabled = deaths_enabled_ref
        self.deaths_format = deaths_format_ref
        self.time_enabled = time_enabled_ref
        self.time_format = time_format_ref

        # UI Grouping for enabling/disabling
        self.child_widgets = [
            self.folder_label, self.browse_button,
            self.bosses_enabled, self.bosses_format, self.deaths_enabled,
            self.deaths_format, self.time_enabled, self.time_format,
            self.panel.findChild(QGroupBox, "files_groupbox")
        ]

        self.settings = QSettings("TheTarnishedChronicle", "App")
        self._load_settings()
        self.connect_signals()
        self.handle_state_change() # Apply initial enabled/disabled state

    def connect_signals(self):
        """Connect all UI signals to their respective handlers."""
        self.enable_toggle.toggled.connect(self.handle_state_change)
        self.browse_button.clicked.connect(self.set_folder_path)
        self.instructions_button.clicked.connect(self.show_instructions)
        
        # Connect all settings changes to the save method
        self.enable_toggle.toggled.connect(self._save_settings)
        self.bosses_enabled.stateChanged.connect(self._save_settings)
        self.deaths_enabled.stateChanged.connect(self._save_settings)
        self.time_enabled.stateChanged.connect(self._save_settings)
        self.bosses_format.textChanged.connect(self._save_settings)
        self.deaths_format.textChanged.connect(self._save_settings)
        self.time_format.textChanged.connect(self._save_settings)

    def _load_settings(self):
        """Load all OBS settings from QSettings and apply them to the UI."""
        self.enable_toggle.setChecked(self.settings.value("obs/enabled", False, type=bool))
        self.folder_label.setText(self.settings.value("obs/folder", "Not set."))
        
        self.bosses_enabled.setChecked(self.settings.value("obs/bossesEnabled", True, type=bool))
        self.bosses_format.setText(self.settings.value("obs/bossesFormat", "Bosses: {defeated}/{total}"))
        
        self.deaths_enabled.setChecked(self.settings.value("obs/deathsEnabled", True, type=bool))
        self.deaths_format.setText(self.settings.value("obs/deathsFormat", "Deaths: {deaths}"))

        self.time_enabled.setChecked(self.settings.value("obs/timeEnabled", True, type=bool))
        self.time_format.setText(self.settings.value("obs/timeFormat", "Time: {time}"))

    def _save_settings(self):
        """Save all current UI settings to QSettings."""
        self.settings.setValue("obs/enabled", self.enable_toggle.isChecked())
        self.settings.setValue("obs/folder", self.folder_label.text())

        self.settings.setValue("obs/bossesEnabled", self.bosses_enabled.isChecked())
        self.settings.setValue("obs/bossesFormat", self.bosses_format.text())

        self.settings.setValue("obs/deathsEnabled", self.deaths_enabled.isChecked())
        self.settings.setValue("obs/deathsFormat", self.deaths_format.text())

        self.settings.setValue("obs/timeEnabled", self.time_enabled.isChecked())
        self.settings.setValue("obs/timeFormat", self.time_format.text())

    def handle_state_change(self):
        """Enable or disable child widgets based on the main toggle."""
        is_enabled = self.enable_toggle.isChecked()
        for widget in self.child_widgets:
            if widget: # Check if widget exists
                widget.setEnabled(is_enabled)
    
    def toggle_panel_visibility(self):
        """Zobrazí nebo skryje panel s nastavením pro OBS."""
        is_visible = not self.panel.isVisible()
        self.panel.setVisible(is_visible)
        self.settings_button.setText("Hide OBS Settings" if is_visible else "OBS Settings")

    def set_folder_path(self):
        """Open a dialog to select an output folder."""
        current_path = self.folder_label.text()
        start_dir = current_path if os.path.isdir(current_path) else ""
        folder = QFileDialog.getExistingDirectory(self.app, "Select Output Folder", start_dir)
        if folder:
            self.folder_label.setText(folder)
            self._save_settings() # Save immediately after selection
            self.app.force_stats_update_for_obs()
    
    def show_instructions(self):
        """Zobrazí detailní a přehledné instrukce pro nastavení OBS."""
        msg_box = QMessageBox(self.app)
        msg_box.setWindowTitle("OBS File Output Instructions")
        msg_box.setIcon(QMessageBox.Icon.Information)

        # Použijeme HTML pro bohaté formátování
        title_app = "<h3>Step 1: Configure in The Tarnished's Chronicle</h3>"
        steps_app = """
        <ol>
            <li><b>Enable the Feature:</b> Click the main toggle at the top of this panel to enable file writing.</li>
            <li>
                <b>Set the Output Folder:</b> Click 'Set Output Folder' and choose a dedicated folder on your computer (e.g., a 'TTC-OBS' folder on your Desktop).
                <br><em>This is where all text files will be saved.</em>
            </li>
            <li>
                <b>Configure Files:</b> For each stat (Bosses, Deaths, Time), you can:
                <ul>
                    <li>Check the 'Enable' box to create/update its file (e.g., <code>bosses.txt</code>).</li>
                    <li>Customize the text format using placeholders:
                        <ul>
                            <li><code>{defeated}</code> - Number of bosses defeated.</li>
                            <li><code>{total}</code> - Total number of bosses.</li>
                            <li><code>{deaths}</code> - Current death count.</li>
                            <li><code>{time}</code> - Total play time (HH:MM:SS).</li>
                        </ul>
                    </li>
                </ul>
            </li>
        </ol>
        <p>The app will now automatically keep these files updated.</p>
        """

        title_obs = "<h3>Step 2: Add Sources in OBS</h3>"
        steps_obs = """
        <ol>
            <li>
                <b>Add a Text Source:</b> In your OBS scene, click the '+' under 'Sources' and add a new <b>Text (GDI+)</b> source. Give it a name like "Boss Counter".
            </li>
            <li>
                <b>Link the File:</b> In the properties for the new text source, check the box labeled <b>'Read from file'</b>.
            </li>
            <li>
                <b>Browse for the File:</b> Click the 'Browse' button and navigate to the output folder you selected earlier. Choose the corresponding file (e.g., <code>bosses.txt</code>).
            </li>
            <li>
                <b>Style in OBS:</b> Now you can customize the font, color, and size directly in OBS to match your stream layout.
            </li>
            <li>
                <b>Repeat:</b> To show other stats, simply repeat these steps. Add a new 'Text (GDI+)' source for <code>deaths.txt</code>, another for <code>time.txt</code>, etc.
            </li>
        </ol>
        """
        
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(title_app + steps_app + title_obs + steps_obs)
        msg_box.addButton(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def update_obs_files(self, stats: dict):
        """Zapíše data do všech povolených souborů."""
        if not self.enable_toggle.isChecked(): return
        folder = self.folder_label.text()
        if not folder or folder == "Not set.": return

        # Formátování času
        s = stats.get('time', -1)
        time_str = f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}" if s >= 0 else "--:--"
        
        # Zápis do bosses.txt
        if self.bosses_enabled.isChecked():
            path = os.path.join(folder, "bosses.txt")
            text = self.bosses_format.text().format(defeated=stats['defeated'], total=stats['total'])
            self._write_file(path, text)

        # Zápis do deaths.txt
        if self.deaths_enabled.isChecked():
            path = os.path.join(folder, "deaths.txt")
            text = self.deaths_format.text().format(deaths=stats['deaths'])
            self._write_file(path, text)
            
        # Zápis do time.txt
        if self.time_enabled.isChecked():
            path = os.path.join(folder, "time.txt")
            text = self.time_format.text().format(time=time_str)
            self._write_file(path, text)

    def _write_file(self, path, content):
        """Pomocná metoda pro bezpečný zápis do souboru."""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
        except IOError as e:
            print(f"Error writing to OBS file '{path}': {e}")