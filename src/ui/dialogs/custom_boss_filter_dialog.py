# src/ui/dialogs/custom_boss_filter_dialog.py
import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget,
    QTreeWidgetItem, QLineEdit, QLabel, QDialogButtonBox, QFileDialog,
    QMessageBox,
)


class CustomBossFilterDialog(QDialog):
    """Lets the user pick an arbitrary set of bosses (e.g. for randomizer
    races or rune challenges). The selection can be exported to a JSON file
    and shared with friends."""

    def __init__(self, locations_data, selected_ids, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Custom Boss Selection")
        self.resize(460, 600)

        layout = QVBoxLayout(self)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search bosses...")
        self.search_input.textChanged.connect(self._apply_search)
        layout.addWidget(self.search_input)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        layout.addWidget(self.tree)

        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)

        selection_buttons = QHBoxLayout()
        select_all_button = QPushButton("Select All")
        select_all_button.clicked.connect(lambda: self._set_all(Qt.CheckState.Checked))
        select_none_button = QPushButton("Select None")
        select_none_button.clicked.connect(lambda: self._set_all(Qt.CheckState.Unchecked))
        import_button = QPushButton("Import...")
        import_button.clicked.connect(self._import_preset)
        export_button = QPushButton("Export...")
        export_button.clicked.connect(self._export_preset)
        for button in (select_all_button, select_none_button, import_button, export_button):
            selection_buttons.addWidget(button)
        layout.addLayout(selection_buttons)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self._populate(locations_data, {str(eid) for eid in selected_ids})
        self.tree.itemChanged.connect(lambda _item, _col: self._update_summary())
        self._update_summary()

    def _populate(self, locations_data, selected_ids):
        self.tree.blockSignals(True)
        for location, bosses in locations_data.items():
            location_item = QTreeWidgetItem(self.tree, [location])
            location_item.setFlags(
                location_item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsAutoTristate
            )
            for boss_info in bosses:
                event_id = boss_info.get("event_id")
                ids = [str(eid) for eid in (event_id if isinstance(event_id, list) else [event_id])]
                boss_item = QTreeWidgetItem(location_item, [boss_info.get("name", "Unknown")])
                boss_item.setFlags(boss_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                boss_item.setData(0, Qt.ItemDataRole.UserRole, ids)
                checked = any(eid in selected_ids for eid in ids)
                boss_item.setCheckState(
                    0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
                )
        self.tree.blockSignals(False)

    def _boss_items(self):
        for i in range(self.tree.topLevelItemCount()):
            location_item = self.tree.topLevelItem(i)
            for j in range(location_item.childCount()):
                yield location_item.child(j)

    def selected_event_ids(self):
        """Returns the set of selected event IDs as strings."""
        ids = set()
        for item in self._boss_items():
            if item.checkState(0) == Qt.CheckState.Checked:
                ids.update(item.data(0, Qt.ItemDataRole.UserRole))
        return ids

    def _set_all(self, state):
        self.tree.blockSignals(True)
        for item in self._boss_items():
            item.setCheckState(0, state)
        self.tree.blockSignals(False)
        self._update_summary()

    def _apply_search(self, text):
        text = text.lower().strip()
        for i in range(self.tree.topLevelItemCount()):
            location_item = self.tree.topLevelItem(i)
            any_visible = False
            for j in range(location_item.childCount()):
                boss_item = location_item.child(j)
                matches = not text or text in boss_item.text(0).lower()
                boss_item.setHidden(not matches)
                any_visible = any_visible or matches
            location_item.setHidden(not any_visible)
            location_item.setExpanded(bool(text) and any_visible)

    def _update_summary(self):
        total = sum(1 for _ in self._boss_items())
        selected = sum(
            1 for item in self._boss_items()
            if item.checkState(0) == Qt.CheckState.Checked
        )
        self.summary_label.setText(f"Selected: {selected} / {total} bosses")

    def _export_preset(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Boss Preset", "boss_preset.json", "Boss Preset (*.json)"
        )
        if not path:
            return
        preset = {"event_ids": sorted(self.selected_event_ids())}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(preset, f, indent=2)
        except OSError as e:
            QMessageBox.warning(self, "Export Failed", f"Could not write the file:\n{e}")

    def _import_preset(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Boss Preset", "", "Boss Preset (*.json)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                preset = json.load(f)
            ids = {str(eid) for eid in preset["event_ids"]}
        except (OSError, ValueError, KeyError, TypeError) as e:
            QMessageBox.warning(
                self, "Import Failed",
                f"The file is not a valid boss preset:\n{e}"
            )
            return
        self.tree.blockSignals(True)
        for item in self._boss_items():
            item_ids = item.data(0, Qt.ItemDataRole.UserRole)
            checked = any(eid in ids for eid in item_ids)
            item.setCheckState(
                0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
            )
        self.tree.blockSignals(False)
        self._update_summary()
