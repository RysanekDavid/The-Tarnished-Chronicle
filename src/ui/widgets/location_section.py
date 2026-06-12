# src/ui/widgets/location_section.py

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel, QTableWidget, 
    QTableWidgetItem, QAbstractItemView, QCheckBox, QSizePolicy, QGraphicsDropShadowEffect,
    QHeaderView
)
from PySide6.QtGui import QIcon, QColor, QPixmap
from PySide6.QtCore import Qt, QSize, Signal
from ...utils import format_seconds_to_hms
from ...utils import get_resource_path

class LocationSectionWidget(QFrame):
    boss_details_requested = Signal(dict)
    boss_location_requested = Signal(dict)
    expansion_changed = Signal(str, bool)

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
        self.expand_button.setIcon(QIcon(get_resource_path("assets/icons/chevron-right.svg")))
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
        self.boss_table.setColumnCount(5)
        self.boss_table.setHorizontalHeaderLabels(["Boss / Event", "Status", "Timestamp", "Boss Stats", "Location"])
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
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        main_layout.addWidget(self.boss_table)
        self.setLayout(main_layout)
        self._populate_boss_table()
        self._update_header_text()

    def _populate_boss_table(self):
        self.boss_table.setRowCount(len(self.bosses_data))
        for row, boss_info in enumerate(self.bosses_data):
            boss_name_item = QTableWidgetItem(f" {boss_info.get('name', 'N/A')}")
            boss_name_item.setData(Qt.ItemDataRole.UserRole, boss_info)
            self.boss_table.setItem(row, 0, boss_name_item)

            status_icon_label = QLabel()
            status_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.boss_table.setCellWidget(row, 1, status_icon_label)

            timestamp_seconds = boss_info.get('timestamp')
            timestamp_str = format_seconds_to_hms(timestamp_seconds) if timestamp_seconds is not None else ""
            timestamp_item = QTableWidgetItem(timestamp_str)
            timestamp_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.boss_table.setItem(row, 2, timestamp_item)

            if boss_info.get("stats"):
                details_label = QLabel()
                details_label.setPixmap(QIcon(get_resource_path("assets/icons/eye.svg")).pixmap(QSize(16, 18)))
                details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                details_label.setToolTip("Show boss details")
                details_label.setCursor(Qt.CursorShape.PointingHandCursor)
                details_label.mousePressEvent = lambda event, b=boss_info: self._on_details_button_clicked(b)
                self.boss_table.setCellWidget(row, 3, details_label)
            elif any(keyword in boss_info.get("name", "") for keyword in ["Patches", "Mimic Tear", "Fia's Champions", "Stray Mimic Tear"]):
                details_label = QLabel()
                details_label.setPixmap(QIcon(get_resource_path("assets/icons/x-circle.svg")).pixmap(QSize(14, 18)))
                details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                details_label.setToolTip("Stats not available for this boss")
                self.boss_table.setCellWidget(row, 3, details_label)

            location_label = QLabel()
            location_label.setPixmap(QIcon(get_resource_path("assets/icons/map-pin2.svg")).pixmap(QSize(14, 18)))
            location_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            location_label.setToolTip("Show on map (feature not implemented)")
            location_label.setCursor(Qt.CursorShape.PointingHandCursor)
            location_label.mousePressEvent = lambda event, b=boss_info: self._on_location_button_clicked(b)
            self.boss_table.setCellWidget(row, 4, location_label)

        self.update_boss_info(self.bosses_data)

    def update_boss_info(self, new_bosses_data):
        self.bosses_data = new_bosses_data
        defeated_count = 0

        for row in range(self.boss_table.rowCount()):
            boss_name_item = self.boss_table.item(row, 0)
            original_boss_info = boss_name_item.data(Qt.ItemDataRole.UserRole)
            
            new_boss_info = next((b for b in new_bosses_data if b.get('name') == original_boss_info.get('name')), None)
            
            if new_boss_info:
                # Keep the stored boss data current, otherwise apply_status_filter
                # works with stale defeat statuses after a monitoring update
                boss_name_item.setData(Qt.ItemDataRole.UserRole, new_boss_info)
                is_defeated = new_boss_info.get("is_defeated", False)
                status_icon_label = self.boss_table.cellWidget(row, 1)
                if status_icon_label:
                    icon_path = get_resource_path("assets/icons/check.svg") if is_defeated else get_resource_path("assets/icons/x.svg")
                    status_icon_label.setPixmap(QIcon(icon_path).pixmap(QSize(16, 16)))
                
                timestamp_seconds = new_boss_info.get('timestamp')
                timestamp_str = format_seconds_to_hms(timestamp_seconds) if timestamp_seconds is not None else ""
                self.boss_table.item(row, 2).setText(timestamp_str)

                if is_defeated:
                    defeated_count += 1
        
        self._update_header_text()
        self._update_table_height()

    def _update_header_text(self):
        defeated_count = sum(1 for boss in self.bosses_data if boss.get("is_defeated"))
        total_bosses = len(self.bosses_data)
        self.location_name_label.setText(f"{self.location_name} ({defeated_count}/{total_bosses})")
        self.location_complete_checkbox.setChecked(defeated_count == total_bosses)

    def _update_table_height(self):
        if self.boss_table.isVisible():
            header_height = self.boss_table.horizontalHeader().height()
            content_height = sum(self.boss_table.rowHeight(r) for r in range(self.boss_table.rowCount()))
            self.boss_table.setFixedHeight(header_height + content_height + 4)
        else:
            self.boss_table.setFixedHeight(0)

    def apply_status_filter(self, hide_defeated: bool):
        for row in range(self.boss_table.rowCount()):
            boss_name_item = self.boss_table.item(row, 0)
            boss_info = boss_name_item.data(Qt.ItemDataRole.UserRole)
            is_defeated = boss_info.get("is_defeated", False)
            self.boss_table.setRowHidden(row, hide_defeated and is_defeated)
        self._update_table_height()

    def set_expanded(self, expanded: bool):
        if self.is_expanded != expanded:
            self._toggle_expand()

    def _header_clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_expand()

    def _toggle_expand(self):
        self.is_expanded = not self.is_expanded
        self.header_widget.setProperty("expanded", self.is_expanded)
        self.boss_table.setVisible(self.is_expanded)
        self.expand_button.setIcon(QIcon(get_resource_path("assets/icons/chevron-down.svg")) if self.is_expanded else QIcon(get_resource_path("assets/icons/chevron-right.svg")))
        self.header_widget.style().unpolish(self.header_widget)
        self.header_widget.style().polish(self.header_widget)
        self._update_table_height()
        self.expansion_changed.emit(self.location_name, self.is_expanded)

    def _on_details_button_clicked(self, boss_data):
        self.boss_details_requested.emit(boss_data)

    def _on_location_button_clicked(self, boss_data):
        print(f"DEBUG: Location icon clicked for boss: {boss_data.get('name')}")
        self.boss_location_requested.emit(boss_data)