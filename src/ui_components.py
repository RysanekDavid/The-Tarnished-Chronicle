# src/ui_components.py

from PySide6.QtCore import Property, QPointF, QRectF, QPropertyAnimation, QEasingCurve, Qt, Signal, QTimer, QSize, QByteArray
from PySide6.QtGui import QPainter, QBrush, QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QAbstractButton, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QVBoxLayout, QWidget, QTableWidget, QTableWidgetItem, QAbstractItemView,
    QCheckBox, QSizePolicy, QFrame, QGraphicsDropShadowEffect, QScrollArea, QHeaderView, QGroupBox
)
from .app_config import APP_VERSION
# --- ZDE JE KLÍČOVÁ OPRAVA ---
from .utils import create_colored_pixmap, format_seconds_to_hms # <--- NEW IMPORT

#==============================================================================
# Custom widget for the toggle switch
#==============================================================================
class ToggleSwitch(QAbstractButton):
    # ... (třída ToggleSwitch zůstává beze změny) ...
    """A custom widget for a modern animated toggle switch."""
    def __init__(self, parent=None, bg_color="#4C566A", circle_color="#D8DEE9", active_color="#A3BE8C"):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(50, 26)
        self._bg_color = QColor(bg_color)
        self._circle_color = QColor(circle_color)
        self._active_color = QColor(active_color)
        self._circle_position = 3
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(QEasingCurve.OutBounce)
        self.animation.setDuration(300)
        self.toggled.connect(self.start_animation)

    @Property(float)
    def circle_position(self):
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()

    def start_animation(self, value):
        self.animation.stop()
        if value:
            self.animation.setEndValue(self.width() - 23)
        else:
            self.animation.setEndValue(3)
        self.animation.start()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        rect = QRectF(0, 0, self.width(), self.height())
        bg_brush = QBrush(self._active_color if self.isChecked() else self._bg_color)
        p.setBrush(bg_brush)
        p.drawRoundedRect(rect, 13, 13)
        p.setBrush(QBrush(self._circle_color))
        p.drawEllipse(QPointF(self._circle_position + 10, self.height() / 2), 10, 10)


#==============================================================================
# Helper functions for creating UI
#==============================================================================
# --- FUNKCE create_colored_pixmap JE NYNÍ ODSTRANĚNA A IMPORTUJE SE ---

class IconHeader(QWidget):
    # ... (tato třída zůstává beze změny) ...
    def __init__(self, icon_path, text, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        icon_label = QLabel()
        pixmap = create_colored_pixmap(icon_path, QColor(234, 179, 8), QSize(20, 20))
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(22, 22)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label = QLabel(text)
        text_label.setObjectName("sidebarHeader")
        layout.addWidget(icon_label)
        layout.addWidget(text_label)
        layout.addStretch()

def create_file_slot_layout(parent_widget):
    main_v_layout = QVBoxLayout()
    main_v_layout.setSpacing(8)
    
    # --- Save File Section ---
    main_v_layout.addWidget(IconHeader("assets/icons/file-text.svg", "Save File"))
    parent_widget.save_file_path_label = QLabel("No save file selected...")
    parent_widget.save_file_path_label.setObjectName("filePathLabel")
    parent_widget.save_file_path_label.setWordWrap(True)
    main_v_layout.addWidget(parent_widget.save_file_path_label)
    parent_widget.browse_button = QPushButton("Browse for ER0000.sl2")
    parent_widget.browse_button.setObjectName("browseButton")
    main_v_layout.addWidget(parent_widget.browse_button)
    main_v_layout.addSpacing(15)

    # --- Character Section ---
    main_v_layout.addWidget(IconHeader("assets/icons/user.svg", "Character:"))
    parent_widget.character_slot_combobox = QComboBox(parent_widget)
    parent_widget.character_slot_combobox.setPlaceholderText("Select a character")
    parent_widget.character_slot_combobox.setEnabled(False)
    main_v_layout.addWidget(parent_widget.character_slot_combobox)
    main_v_layout.addSpacing(15)
    
    # --- Filter Section ---
    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.HLine)
    separator.setFrameShadow(QFrame.Shadow.Sunken)
    separator.setObjectName("separatorLine")
    main_v_layout.addWidget(separator)
    main_v_layout.addSpacing(10)
    
    # Content Filter (Base/DLC/All)
    main_v_layout.addWidget(IconHeader("assets/icons/filter.svg", "Content Filter"))
    parent_widget.content_filter_combobox = QComboBox()
    parent_widget.content_filter_combobox.addItem("Show All", userData="all")
    parent_widget.content_filter_combobox.addItem("Base Game Only", userData="base")
    parent_widget.content_filter_combobox.addItem("DLC Only", userData="dlc")
    main_v_layout.addWidget(parent_widget.content_filter_combobox)
    main_v_layout.addSpacing(10)

    # Display Filter (Hide Defeated)
    parent_widget.hide_defeated_checkbox = QCheckBox("Hide Defeated Bosses")
    main_v_layout.addWidget(parent_widget.hide_defeated_checkbox)

    return main_v_layout

def create_main_boss_area(parent_widget):
    # ... (tato funkce zůstává beze změny) ...
    scroll_area = QScrollArea(parent_widget)
    scroll_area.setWidgetResizable(True)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    scroll_area.setObjectName("mainBossScrollArea")
    main_container_widget = QWidget()
    main_container_widget.setObjectName("locationsContainer")
    parent_widget.locations_layout = QVBoxLayout(main_container_widget)
    parent_widget.locations_layout.setContentsMargins(10, 10, 10, 10)
    parent_widget.locations_layout.setSpacing(0)
    parent_widget.locations_layout.addStretch()
    scroll_area.setWidget(main_container_widget)
    return scroll_area

def create_overlay_settings_panel_layout(parent_widget):
    # ... (tato funkce zůstává beze změny) ...
    settings_panel_widget = QFrame()
    settings_panel_widget.setObjectName("settingsPanel")
    settings_layout = QVBoxLayout(settings_panel_widget)
    settings_layout.setSpacing(10)

    content_groupbox = QGroupBox("Displayed Information")
    content_layout = QVBoxLayout()
    parent_widget.overlay_show_bosses = QCheckBox("Show Boss Counter")
    parent_widget.overlay_show_bosses.setChecked(True)
    content_layout.addWidget(parent_widget.overlay_show_bosses)
    parent_widget.overlay_show_deaths = QCheckBox("Show Death Counter")
    content_layout.addWidget(parent_widget.overlay_show_deaths)
    parent_widget.overlay_show_time = QCheckBox("Show Play Time")
    content_layout.addWidget(parent_widget.overlay_show_time)
    parent_widget.overlay_show_seconds = QCheckBox("Show Seconds in Time")
    parent_widget.overlay_show_seconds.setStyleSheet("margin-left: 20px;")
    content_layout.addWidget(parent_widget.overlay_show_seconds)
    
    # --- PŘIDÁNO ---
    parent_widget.overlay_show_last_boss = QCheckBox("Show Last Boss Killed")
    parent_widget.overlay_show_last_boss.setToolTip("Displays the name and time of the last defeated boss.")
    content_layout.addWidget(parent_widget.overlay_show_last_boss)
    # --- KONEC ---
    content_groupbox.setLayout(content_layout)
    settings_layout.addWidget(content_groupbox)

    appearance_groupbox = QGroupBox("Appearance")
    appearance_layout = QVBoxLayout(appearance_groupbox)
    text_color_layout = QHBoxLayout()
    text_color_layout.addWidget(QLabel("Text Color:"))
    parent_widget.overlay_text_color_button = QPushButton("lightblue")
    parent_widget.overlay_text_color_button.setToolTip("Click to choose text color")
    text_color_layout.addWidget(parent_widget.overlay_text_color_button)
    appearance_layout.addLayout(text_color_layout)

    font_size_layout = QHBoxLayout()
    font_size_layout.addWidget(QLabel("Font Size:"))
    parent_widget.overlay_font_size_combobox = QComboBox()
    for size in range(10, 31, 2):
        parent_widget.overlay_font_size_combobox.addItem(f"{size}pt")
    font_size_layout.addWidget(parent_widget.overlay_font_size_combobox)
    appearance_layout.addLayout(font_size_layout)

    settings_layout.addWidget(appearance_groupbox)
    
    return settings_panel_widget

def create_obs_panel_layout(parent_widget):
    # ... (tato funkce zůstává beze změny) ...
    obs_settings_panel = QFrame()
    obs_settings_panel.setObjectName("settingsPanel")
    layout = QVBoxLayout(obs_settings_panel)
    layout.setSpacing(10)

    top_layout = QHBoxLayout()
    top_layout.addWidget(QLabel("<b>Enable OBS File Output</b>"))
    top_layout.addStretch()
    parent_widget.obs_enable_toggle = ToggleSwitch()
    top_layout.addWidget(parent_widget.obs_enable_toggle)
    layout.addLayout(top_layout)
    
    instructions_layout = QHBoxLayout()
    parent_widget.obs_instructions_button = QPushButton(" Show Setup Instructions")
    parent_widget.obs_instructions_button.setIcon(QIcon("assets/icons/info-circle-solid.svg"))
    parent_widget.obs_instructions_button.setObjectName("infoButton")
    instructions_layout.addWidget(parent_widget.obs_instructions_button)
    instructions_layout.addStretch()
    layout.addLayout(instructions_layout)

    separator = QFrame()
    separator.setFrameShape(QFrame.Shape.HLine)
    separator.setFrameShadow(QFrame.Shadow.Sunken)
    separator.setObjectName("separatorLine")
    layout.addWidget(separator)
    layout.addSpacing(5)
    
    layout.addWidget(QLabel("Output Folder:"))
    parent_widget.obs_folder_path_label = QLabel("Not set.")
    parent_widget.obs_folder_path_label.setObjectName("filePathLabel")
    layout.addWidget(parent_widget.obs_folder_path_label)
    parent_widget.obs_browse_button = QPushButton("Set Output Folder")
    layout.addWidget(parent_widget.obs_browse_button)

    files_groupbox = QGroupBox("Configure Output Files")
    files_groupbox.setObjectName("files_groupbox")
    files_layout = QVBoxLayout(files_groupbox)
    files_layout.setSpacing(15)
    
    boss_layout = QVBoxLayout()
    parent_widget.obs_bosses_enabled = QCheckBox("Enable bosses.txt")
    parent_widget.obs_bosses_enabled.setChecked(True)
    boss_layout.addWidget(parent_widget.obs_bosses_enabled)
    parent_widget.obs_bosses_format = QLineEdit("Bosses: {defeated}/{total}")
    boss_layout.addWidget(parent_widget.obs_bosses_format)
    files_layout.addLayout(boss_layout)

    death_layout = QVBoxLayout()
    parent_widget.obs_deaths_enabled = QCheckBox("Enable deaths.txt")
    parent_widget.obs_deaths_enabled.setChecked(True)
    death_layout.addWidget(parent_widget.obs_deaths_enabled)
    parent_widget.obs_deaths_format = QLineEdit("Deaths: {deaths}")
    death_layout.addWidget(parent_widget.obs_deaths_format)
    files_layout.addLayout(death_layout)

    # --- Death Counter Management for OBS ---
    death_management_groupbox = QGroupBox("OBS Death Counter Management")
    death_management_layout = QVBoxLayout(death_management_groupbox)
    
    parent_widget.obs_reset_deaths_button = QPushButton("Reset OBS Deaths to 0")
    parent_widget.obs_reset_deaths_button.setToolTip("This sets the OBS death counter to 0 by creating an offset. The real death count is not affected.")
    death_management_layout.addWidget(parent_widget.obs_reset_deaths_button)
    
    parent_widget.obs_undo_reset_button = QPushButton("Undo Reset")
    parent_widget.obs_undo_reset_button.setToolTip("Removes the death counter offset.")
    parent_widget.obs_undo_reset_button.setEnabled(False)
    death_management_layout.addWidget(parent_widget.obs_undo_reset_button)
    
    files_layout.addWidget(death_management_groupbox)
    # --- End Death Counter Management ---

    time_layout = QVBoxLayout()
    parent_widget.obs_time_enabled = QCheckBox("Enable time.txt")
    parent_widget.obs_time_enabled.setChecked(True)
    time_layout.addWidget(parent_widget.obs_time_enabled)
    parent_widget.obs_time_format = QLineEdit("Time: {time}")
    time_layout.addWidget(parent_widget.obs_time_format)
    files_layout.addLayout(time_layout)

    last_boss_layout = QVBoxLayout()
    parent_widget.obs_last_boss_enabled = QCheckBox("Enable last_boss.txt")
    parent_widget.obs_last_boss_enabled.setChecked(True)
    last_boss_layout.addWidget(parent_widget.obs_last_boss_enabled)
    parent_widget.obs_last_boss_format = QLineEdit("Last Kill: {boss_name} ({kill_time})")
    last_boss_layout.addWidget(parent_widget.obs_last_boss_format)
    files_layout.addLayout(last_boss_layout)
    
    files_groupbox.setLayout(files_layout)
    layout.addWidget(files_groupbox)
    
    return obs_settings_panel


#==============================================================================
# Main Widgets (Cards, Footer)
#==============================================================================
class LocationSectionWidget(QFrame):
    # ... (třída a její metody, včetně nové metody 'update_boss_info', zůstávají beze změny) ...
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
        header_layout.setContentsMargins(8, 12, 8, 12)
        header_layout.setSpacing(10)
        self.expand_button = QPushButton()
        self.expand_button.setObjectName("expandButton")
        self.expand_button.setFixedSize(24, 24)
        self.location_icon_label = QLabel()
        self.location_icon_label.setObjectName("locationIcon")
        self.location_icon_label.setFixedSize(18, 18)
        self.location_name_label = QLabel()
        self.location_name_label.setObjectName("location_name_label")
        self.location_complete_checkbox = QCheckBox()
        self.location_complete_checkbox.setEnabled(False)
        self.location_complete_checkbox.setFixedSize(24, 24)
        header_layout.addWidget(self.expand_button)
        header_layout.addWidget(self.location_icon_label)
        header_layout.addWidget(self.location_name_label, 1)
        header_layout.addWidget(self.location_complete_checkbox)
        self.header_widget.mousePressEvent = self._header_clicked
        self.expand_button.clicked.connect(self._toggle_expand)
        main_layout.addWidget(self.header_widget)
        self.boss_table = QTableWidget()
        self.boss_table.setColumnCount(3)
        self.boss_table.setHorizontalHeaderLabels(["Boss / Event", "Status", "Timestamp"])
        self.boss_table.verticalHeader().setVisible(False)
        self.boss_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.boss_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.boss_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.boss_table.setVisible(False)
        self.boss_table.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        header = self.boss_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        main_layout.addWidget(self.boss_table)
        self.setLayout(main_layout)
        self._populate_boss_table()
        self._update_header_text()

    def _populate_boss_table(self):
        self.boss_table.setRowCount(len(self.bosses_data))
        for row, boss_info in enumerate(self.bosses_data):
            # ... (boss name and status icon logic is unchanged) ...
            boss_name_item = QTableWidgetItem(f" {boss_info.get('name', 'N/A')}")
            boss_name_item.setData(Qt.ItemDataRole.UserRole, boss_info)
            self.boss_table.setItem(row, 0, boss_name_item)
            
            status_icon_label = QLabel()
            status_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.boss_table.setCellWidget(row, 1, status_icon_label)
            
            # --- MODIFIED: Handle timestamp display ---
            timestamp_seconds = boss_info.get('timestamp')
            timestamp_str = format_seconds_to_hms(timestamp_seconds)
            timestamp_item = QTableWidgetItem(timestamp_str)
            # --- END MODIFIED ---
            
            timestamp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.boss_table.setItem(row, 2, timestamp_item)

        self.update_boss_info(self.bosses_data)

    def update_boss_info(self, new_bosses_data):
        self.bosses_data = new_bosses_data
        defeated_count = 0

        for row in range(self.boss_table.rowCount()):
            boss_name_item = self.boss_table.item(row, 0)
            original_boss_info = boss_name_item.data(Qt.ItemDataRole.UserRole)
            
            new_boss_info = next((b for b in new_bosses_data if b.get('name') == original_boss_info.get('name')), None)
            
            if not new_boss_info: continue

            is_defeated = new_boss_info.get("is_defeated", False)
            if is_defeated:
                defeated_count += 1

            status_icon_label = self.boss_table.cellWidget(row, 1)
            if is_defeated:
                pixmap = create_colored_pixmap("assets/icons/check.svg", QColor("#A3BE8C"), QSize(18, 18))
                status_icon_label.setPixmap(pixmap)
                status_icon_label.setToolTip("Defeated")
            else:
                pixmap = create_colored_pixmap("assets/icons/x.svg", QColor("#BF616A"), QSize(18, 18))
                status_icon_label.setPixmap(pixmap)
                status_icon_label.setToolTip("Active")
            
        self.defeated_count = defeated_count
        self.total_bosses = len(self.bosses_data)
        self.location_complete_checkbox.setChecked(self.total_bosses > 0 and self.defeated_count == self.total_bosses)
        self._update_header_text()

    def _update_header_text(self):
        self.location_name_label.setText(f"{self.location_name} ({self.defeated_count}/{self.total_bosses})")
        if self.is_expanded:
            self.expand_button.setIcon(QIcon("assets/icons/chevron-down.svg"))
        else:
            self.expand_button.setIcon(QIcon("assets/icons/chevron-right.svg"))

    def _update_table_height(self):
        """Calculates and sets the correct fixed height for the boss table."""
        if self.is_expanded:
            header_h = self.boss_table.horizontalHeader().height()
            # Calculate height based only on visible rows
            content_h = sum(self.boss_table.rowHeight(i) for i in range(self.boss_table.rowCount()) if not self.boss_table.isRowHidden(i))
            self.boss_table.setFixedHeight(header_h + content_h + 5)
        else:
            self.boss_table.setFixedHeight(0)
        
        # This is important to force the layout to re-evaluate
        QTimer.singleShot(0, lambda: self.parentWidget().layout().activate())

    def apply_status_filter(self, hide_defeated: bool):
        """Hides or shows rows in the table based on their defeated status."""
        # ... (the existing logic for hiding/showing rows is unchanged) ...
        any_boss_visible = False
        for row in range(self.boss_table.rowCount()):
            item = self.boss_table.item(row, 0)
            if not item: continue
            
            boss_info = item.data(Qt.ItemDataRole.UserRole)
            is_defeated = boss_info.get("is_defeated", False)
            
            should_hide = hide_defeated and is_defeated
            self.boss_table.setRowHidden(row, should_hide)
            
            if not should_hide:
                any_boss_visible = True
        
        self.setVisible(any_boss_visible)
        
        # --- ADDED CALL ---
        # After changing row visibility, we must update the table's height
        self._update_table_height()

    def set_expanded(self, expanded: bool):
        """Programmatically sets the expanded state of the widget."""
        # Only call toggle if the state is actually different, to avoid recursion
        if self.is_expanded != expanded:
            self._toggle_expand()

    def _header_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_expand()

    def _toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.boss_table.setVisible(self.is_expanded)
        self.header_widget.setProperty("expanded", self.is_expanded)
        self.header_widget.style().unpolish(self.header_widget)
        self.header_widget.style().polish(self.header_widget)
        
        # --- MODIFIED ---
        # Use our new helper method here as well for consistency
        self._update_table_height()
        
        self._update_header_text()
        self.adjustSize()
        if self.parentWidget() and self.parentWidget().layout():
            self.parentWidget().layout().activate()

class FooterWidget(QFrame):
    # ... (tato třída zůstává beze změny) ...
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("footer")
        self.setFixedHeight(40)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(25)

        self.monitoring_status = FooterStatusWidget("assets/icons/activity.svg", "Not Monitoring")
        
        self.boss_stat = FooterStatusWidget("assets/icons/check-circle.svg", "Bosses: --/--")
        self.deaths_stat = FooterStatusWidget("assets/icons/skull-and-crossbones.svg", "Deaths: --")
        self.time_stat = FooterStatusWidget("assets/icons/clock.svg", "Time: --:--:--")
        
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setObjectName("versionLabel")

        layout.addWidget(self.monitoring_status)
        layout.addStretch(1)
        layout.addWidget(self.boss_stat)
        layout.addWidget(self.deaths_stat)
        layout.addWidget(self.time_stat)
        layout.addStretch(1)
        layout.addWidget(version_label)
        
        self.update_monitoring_status(False)

    def update_monitoring_status(self, active: bool, text: str = ""):
        if active:
            color = QColor("#A3BE8C")
            status_text = text or "Monitoring Active"
        else:
            color = QColor("#EBCB8B")
            status_text = text or "Not Monitoring"
        
        self.monitoring_status.set_text(status_text)
        self.monitoring_status.set_color(color)

    def update_stats(self, stats: dict):
        self.boss_stat.set_text(f"Bosses: {stats.get('defeated', '--')}/{stats.get('total', '--')}")
        self.deaths_stat.set_text(f"Deaths: {stats.get('deaths', '--')}")
        self.update_time(stats.get('seconds_played', -1))

    def update_time(self, seconds: int):
        if seconds < 0:
            self.time_stat.set_text("Time: --:--:--")
            return
        
        h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
        self.time_stat.set_text(f"Time: {h:02d}:{m:02d}:{s:02d}")


class FooterStatusWidget(QWidget):
    """Náš finální, znovupoužitelný widget pro zobrazení ikony a textu."""
    def __init__(self, icon_path: str, initial_text: str, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        self.icon_label = QLabel()
        self.text_label = QLabel(initial_text)

        self.set_color(QColor("#D8DEE9"))
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)

    def set_text(self, text: str):
        self.text_label.setText(text)

    def set_color(self, color: QColor):
        pixmap = create_colored_pixmap(self.icon_path, color, QSize(16, 16))
        self.icon_label.setPixmap(pixmap)
        self.text_label.setStyleSheet(f"color: {color.name()}; font-weight: bold;")