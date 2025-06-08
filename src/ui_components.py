from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QTreeWidget, QHeaderView, QComboBox, QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QAbstractItemView, QCheckBox, QSizePolicy, QFrame, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QTimer # Added QTimer
from PySide6.QtGui import QColor, QIcon # Přidat import
from PySide6.QtCore import QSize, QByteArray
from PySide6.QtGui import QPixmap

# === NOVÁ POMOCNÁ FUNKCE PRO BAREVNÉ IKONY ===
def create_colored_pixmap(icon_path: str, color: QColor, size: QSize) -> QPixmap:
    try:
        with open(icon_path, 'r', encoding='utf-8') as f:
            svg_data = f.read()
        colored_svg_data = svg_data.replace('currentColor', color.name())
        byte_array = QByteArray(colored_svg_data.encode('utf-8'))
        pixmap = QPixmap()
        pixmap.loadFromData(byte_array)
        return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    except Exception as e:
        print(f"Chyba při vytváření barevné pixmapy pro {icon_path}: {e}")
        return QPixmap()

# === NOVÝ POMOCNÝ WIDGET PRO NADPISY V SIDEBARU ===
class IconHeader(QWidget):
    def __init__(self, icon_path, text, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        icon_label = QLabel()
        pixmap = create_colored_pixmap(icon_path, QColor(234, 179, 8), QSize(20, 20))
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(22, 22)
        icon_label.setAlignment(Qt.AlignCenter)
        
        text_label = QLabel(text)
        text_label.setObjectName("sidebarHeader") # Dáme mu jméno pro QSS
        
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addStretch()

def create_file_slot_layout(parent_widget):
    """Vytvoří NOVÝ layout pro výběr souboru a postavy."""
    main_v_layout = QVBoxLayout()
    main_v_layout.setSpacing(8)

    # --- Sekce pro Save File ---
    main_v_layout.addWidget(IconHeader("assets/icons/file-text.svg", "Save File"))
    
    # Použijeme ne-editovatelný QLabel pro zobrazení cesty
    parent_widget.save_file_path_label = QLabel("No file selected.")
    parent_widget.save_file_path_label.setObjectName("filePathLabel")
    parent_widget.save_file_path_label.setWordWrap(True)
    main_v_layout.addWidget(parent_widget.save_file_path_label)

    # Nové tlačítko pro procházení
    parent_widget.browse_button = QPushButton("Browse File")
    parent_widget.browse_button.setObjectName("browseButton")
    
    main_v_layout.addWidget(parent_widget.browse_button)

    main_v_layout.addSpacing(15)

    # --- Sekce pro Character Profile ---
    main_v_layout.addWidget(IconHeader("assets/icons/user.svg", "Character Profile"))
    
    parent_widget.character_slot_combobox = QComboBox(parent_widget)
    parent_widget.character_slot_combobox.setPlaceholderText("Select Character")
    parent_widget.character_slot_combobox.setEnabled(False)
    main_v_layout.addWidget(parent_widget.character_slot_combobox)
    
    return main_v_layout

def create_monitoring_controls_layout(parent_widget):
    """Creates the layout for monitoring controls. (Now empty as monitoring is automatic)"""
    layout = QHBoxLayout()
    # parent_widget.start_monitor_button = QPushButton("Start Monitoring", parent_widget)
    # layout.addWidget(parent_widget.start_monitor_button)

    # parent_widget.stop_monitor_button = QPushButton("Stop Monitoring", parent_widget)
    # parent_widget.stop_monitor_button.setEnabled(False)
    # layout.addWidget(parent_widget.stop_monitor_button)

    # layout.addWidget(QLabel("Interval (s):", parent_widget))
    # parent_widget.interval_spinbox = QSpinBox(parent_widget)
    # parent_widget.interval_spinbox.setRange(1, 300)
    # parent_widget.interval_spinbox.setValue(5) # Default to 5s
    # layout.addWidget(parent_widget.interval_spinbox)
    return layout

from PySide6.QtWidgets import QScrollArea # Added QScrollArea

def create_main_boss_area(parent_widget):
    """Creates the main scrollable area that will contain LocationSectionWidgets."""
    scroll_area = QScrollArea(parent_widget)
    scroll_area.setWidgetResizable(True)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    
    # Důležité: Dáme scroll area jméno, aby poslouchala náš hlavní styl
    scroll_area.setObjectName("mainBossScrollArea")

    # Vnitřní kontejner, který drží všechny karty
    main_container_widget = QWidget()
    main_container_widget.setObjectName("locationsContainer")
    
    parent_widget.locations_layout = QVBoxLayout(main_container_widget)
    
    # === ZDE JE TA KLÍČOVÁ ZMĚNA ===
    # Nastavíme vnitřní okraje (padding), aby karty nebyly nalepené na hranu.
    # formát je: (levý, horní, pravý, dolní)
    parent_widget.locations_layout.setContentsMargins(10, 10, 10, 10)
    
    # Mezery mezi kartami řídí jejich `margin` v QSS, zde nechceme žádné navíc
    parent_widget.locations_layout.setSpacing(0)
    
    # DŮLEŽITÉ: Přidá prázdné místo na konec, což natlačí karty nahoru
    parent_widget.locations_layout.addStretch()

    scroll_area.setWidget(main_container_widget)
    
    # Všechny staré .setStyleSheet() příkazy jsou pryč!
    return scroll_area

def create_overlay_settings_panel_layout(parent_widget): # Renamed for clarity
    """Creates the layout for overlay customization input fields."""
    settings_layout = QVBoxLayout() # Changed to QVBoxLayout for better arrangement of multiple settings rows if needed in future

    # Background Color
    bg_layout = QHBoxLayout()
    bg_layout.addWidget(QLabel("BG Color:", parent_widget))
    parent_widget.overlay_bg_color_button = QPushButton("rgba(100, 100, 100, 220)", parent_widget) # Text will be updated by OverlayManager
    parent_widget.overlay_bg_color_button.setToolTip("Click to choose background color. Opacity is set via 'Alpha channel' in the dialog (0=transparent, 255=opaque).")
    # We'll connect this button to a handler in gui.py
    bg_layout.addWidget(parent_widget.overlay_bg_color_button)
    settings_layout.addLayout(bg_layout)

    # Text Color
    text_color_layout = QHBoxLayout()
    text_color_layout.addWidget(QLabel("Text Color:", parent_widget))
    parent_widget.overlay_text_color_button = QPushButton("lightblue", parent_widget) # Text will be updated
    parent_widget.overlay_text_color_button.setToolTip("Click to choose text color")
    # We'll connect this button to a handler in gui.py
    text_color_layout.addWidget(parent_widget.overlay_text_color_button)
    settings_layout.addLayout(text_color_layout)

    # Font Size
    font_size_layout = QHBoxLayout()
    font_size_layout.addWidget(QLabel("Font Size:", parent_widget))
    parent_widget.overlay_font_size_input = QLineEdit("15pt", parent_widget)
    parent_widget.overlay_font_size_input.setPlaceholderText("e.g., 12pt or 16px")
    font_size_layout.addWidget(parent_widget.overlay_font_size_input)
    settings_layout.addLayout(font_size_layout)
    
    parent_widget.apply_overlay_settings_button = QPushButton("Apply Settings", parent_widget) # Shortened button text
    settings_layout.addWidget(parent_widget.apply_overlay_settings_button, 0, Qt.AlignmentFlag.AlignRight) # Align button to the right

    # Create a container widget for this layout
    settings_panel_widget = QWidget()
    settings_panel_widget.setLayout(settings_layout)
    
    return settings_panel_widget

class LocationSectionWidget(QFrame):
    """
    Widget reprezentující "kartu" pro jednu lokaci.
    Nyní plně řízený centrálním QSS.
    """
    def __init__(self, location_name, bosses_data, parent=None):
        super().__init__(parent)
        self.setObjectName("locationCard")
        
        self.location_name = location_name
        self.bosses_data = bosses_data
        self.is_expanded = False

        self._init_ui()
        self._apply_shadow()

    def _apply_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.header_widget = QWidget()
        self.header_widget.setProperty("expanded", self.is_expanded)
        
        header_layout = QHBoxLayout(self.header_widget)
        # Zmenšíme levý/pravý okraj, protože ikony teď budou mít vlastní prostor
        header_layout.setContentsMargins(8, 12, 8, 12)
        header_layout.setSpacing(10)

        # === ZMĚNA 1: Šipka je nyní tlačítko s ikonou ===
        self.expand_button = QPushButton()
        self.expand_button.setObjectName("expandButton")
        self.expand_button.setFixedSize(24, 24) # Pevná velikost
        
        # === ZMĚNA 2: Emoji je nyní SVG ikona přes QSS ===
        self.location_icon_label = QLabel()
        self.location_icon_label.setObjectName("locationIcon") # Dáme mu jméno pro QSS
        self.location_icon_label.setFixedSize(18, 18) # Pevná velikost zůstává
        # self.location_icon_label.setAlignment(...) už není potřeba
        
        self.location_name_label = QLabel()
        self.location_name_label.setObjectName("location_name_label")

        # === ZMĚNA 3: Checkbox má pevnou velikost ===
        self.location_complete_checkbox = QCheckBox()
        self.location_complete_checkbox.setEnabled(False)
        self.location_complete_checkbox.setFixedSize(24, 24) # Pevná velikost

        # Přidáme nové tlačítko místo starého labelu
        header_layout.addWidget(self.expand_button)
        header_layout.addWidget(self.location_icon_label)
        header_layout.addWidget(self.location_name_label, 1)
        header_layout.addWidget(self.location_complete_checkbox)
        
        self.header_widget.mousePressEvent = self._header_clicked
        # Připojíme i kliknutí na tlačítko
        self.expand_button.clicked.connect(self._toggle_expand)

        main_layout.addWidget(self.header_widget)
        
        self.boss_table = QTableWidget()
        
        # ZMĚNA 1: Snížíme počet sloupců ze 3 na 2
        self.boss_table.setColumnCount(2)
        # ZMĚNA 2: Odstraníme "Event Flag ID" z hlavičky
        self.boss_table.setHorizontalHeaderLabels(["Status", "Boss Name"])
        
        self.boss_table.verticalHeader().setVisible(False)
        self.boss_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.boss_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.boss_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.boss_table.setVisible(False)
        self.boss_table.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        header = self.boss_table.horizontalHeader()
        # ZMĚNA 3: Upravíme šířky sloupců
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Status sloupec bude úzký
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)         # Jméno bosse zabere zbytek místa
        
        main_layout.addWidget(self.boss_table)
        self.setLayout(main_layout)

        self._populate_boss_table()
        self._update_header_text()

    def _populate_boss_table(self):
        self.boss_table.setRowCount(len(self.bosses_data))
        defeated_count = 0
        for row, boss_info in enumerate(self.bosses_data):
            is_defeated = boss_info.get("is_defeated", False)
            if is_defeated:
                defeated_count += 1

            # ZMĚNA 4: Místo textu vytváříme label s ikonou
            status_icon_label = QLabel()
            status_icon_label.setAlignment(Qt.AlignCenter) # Ikonu zarovnáme na střed buňky
            
            if is_defeated:
                # Vytvoříme zelenou "fajfku"
                pixmap = create_colored_pixmap("assets/icons/check.svg", QColor("#A3BE8C"), QSize(18, 18))
                status_icon_label.setPixmap(pixmap)
                status_icon_label.setToolTip("Defeated") # Tooltip pro informaci při najetí myší
            else:
                # Vytvoříme červený křížek
                pixmap = create_colored_pixmap("assets/icons/x.svg", QColor("#BF616A"), QSize(18, 18))
                status_icon_label.setPixmap(pixmap)
                status_icon_label.setToolTip("Active")

            boss_name_item = QTableWidgetItem(f" {boss_info.get('name', 'N/A')}")
            # Event ID item je kompletně odstraněn

            # Vložíme naše nové widgety do tabulky
            self.boss_table.setCellWidget(row, 0, status_icon_label)
            self.boss_table.setItem(row, 1, boss_name_item)
        
        self.defeated_count = defeated_count
        self.total_bosses = len(self.bosses_data)
        self.location_complete_checkbox.setChecked(self.total_bosses > 0 and self.defeated_count == self.total_bosses)

    def _update_header_text(self):
        # Tato metoda se nyní stará i o změnu ikony
        self.location_name_label.setText(f"{self.location_name} ({self.defeated_count}/{self.total_bosses})")
        
        if self.is_expanded:
            self.expand_button.setIcon(QIcon("assets/icons/chevron-down.svg"))
        else:
            self.expand_button.setIcon(QIcon("assets/icons/chevron-right.svg"))

    def _header_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_expand()

    def _toggle_expand(self):
        # Tato metoda je nyní krásně jednoduchá
        self.is_expanded = not self.is_expanded
        self.boss_table.setVisible(self.is_expanded)
        
        # Změníme property a řekneme stylu, aby se překreslil
        self.header_widget.setProperty("expanded", self.is_expanded)
        self.header_widget.style().unpolish(self.header_widget)
        self.header_widget.style().polish(self.header_widget)

        # Kód pro nastavení výšky zůstává
        if self.is_expanded:
            header_h = self.boss_table.horizontalHeader().height()
            content_h = sum(self.boss_table.rowHeight(i) for i in range(self.boss_table.rowCount()))
            self.boss_table.setFixedHeight(header_h + content_h + 5)
        else:
            self.boss_table.setFixedHeight(0)
            
        self._update_header_text()
        self.adjustSize()
        if self.parentWidget() and self.parentWidget().layout():
            self.parentWidget().layout().activate()

    def update_boss_info(self, new_bosses_data):
        self.bosses_data = new_bosses_data
        self._populate_boss_table()
        self._update_header_text()
# === NOVÝ WIDGET PRO PATIČKU ===
class FooterWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("footer")
        self.setFixedHeight(40) # Nastavíme pevnou výšku

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 15, 0) # Vnitřní okraje (vlevo/vpravo)
        layout.setSpacing(20) # Mezery mezi jednotlivými sekcemi

        # --- Sekce Monitoring ---
        self.monitor_layout = QHBoxLayout()
        self.monitor_icon = QLabel()
        self.monitor_text = QLabel("Monitoring Inactive")
        self.monitor_layout.addWidget(self.monitor_icon)
        self.monitor_layout.addWidget(self.monitor_text)
        layout.addLayout(self.monitor_layout)

        # --- Sekce Last Update ---
        self.update_layout = QHBoxLayout()
        self.update_icon = QLabel()
        self.update_icon.setPixmap(create_colored_pixmap("assets/icons/clock.svg", QColor("#8899A6"), QSize(16, 16)))
        self.update_text = QLabel("Last update: N/A")
        self.update_layout.addWidget(self.update_icon)
        self.update_layout.addWidget(self.update_text)
        layout.addLayout(self.update_layout)
        
        # --- Sekce Bosses Defeated ---
        self.boss_count_layout = QHBoxLayout()
        self.boss_count_icon = QLabel()
        self.boss_count_icon.setPixmap(create_colored_pixmap("assets/icons/check-circle.svg", QColor("#A3BE8C"), QSize(16, 16)))
        self.boss_count_text = QLabel("Bosses defeated: 0/0")
        self.boss_count_layout.addWidget(self.boss_count_icon)
        self.boss_count_layout.addWidget(self.boss_count_text)
        layout.addLayout(self.boss_count_layout)

        layout.addStretch() # Odsadí vše doleva

        # Vstupní nastavení
        self.update_monitoring_status(False)

    def update_monitoring_status(self, is_active: bool):
        color = QColor("#A3BE8C") if is_active else QColor("#BF616A") # Zelená/Červená
        icon_path = "assets/icons/activity.svg" # Předpokládám název souboru, upraveno z active.svg
        text = "Monitoring Active" if is_active else "Monitoring Inactive"
        
        self.monitor_icon.setPixmap(create_colored_pixmap(icon_path, color, QSize(16, 16)))
        self.monitor_text.setText(text)
        self.monitor_text.setStyleSheet(f"color: {color.name()}; font-weight: bold;")

    def update_timestamp(self):
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S")
        self.update_text.setText(f"Last update: {now}")

    def update_boss_count(self, defeated: int, total: int):
        self.boss_count_text.setText(f"Bosses defeated: {defeated}/{total}")