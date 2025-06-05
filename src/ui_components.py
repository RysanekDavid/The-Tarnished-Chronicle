from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QTreeWidget, QHeaderView
)

def create_file_slot_layout(parent_widget):
    """Creates the layout for file path and slot selection."""
    layout = QHBoxLayout()
    layout.addWidget(QLabel("Save File:", parent_widget))
    parent_widget.save_file_path_input = QLineEdit(parent_widget)
    parent_widget.save_file_path_input.setPlaceholderText("Cesta k ER0000.sl2")
    parent_widget.save_file_path_input.setText("C:\\Users\\dawel\\AppData\\Roaming\\EldenRing\\76561198082650286\\ER0000.sl2")
    layout.addWidget(parent_widget.save_file_path_input)

    parent_widget.browse_button = QPushButton("Procházet...", parent_widget)
    layout.addWidget(parent_widget.browse_button)

    layout.addWidget(QLabel("Slot:", parent_widget))
    parent_widget.slot_index_spinbox = QSpinBox(parent_widget)
    parent_widget.slot_index_spinbox.setRange(0, 9)
    parent_widget.slot_index_spinbox.setValue(0)
    layout.addWidget(parent_widget.slot_index_spinbox)
    return layout

def create_monitoring_controls_layout(parent_widget):
    """Creates the layout for monitoring controls."""
    layout = QHBoxLayout()
    parent_widget.start_monitor_button = QPushButton("Start Monitoring", parent_widget)
    layout.addWidget(parent_widget.start_monitor_button)

    parent_widget.stop_monitor_button = QPushButton("Stop Monitoring", parent_widget)
    parent_widget.stop_monitor_button.setEnabled(False)
    layout.addWidget(parent_widget.stop_monitor_button)

    layout.addWidget(QLabel("Interval (s):", parent_widget))
    parent_widget.interval_spinbox = QSpinBox(parent_widget)
    parent_widget.interval_spinbox.setRange(1, 300)
    parent_widget.interval_spinbox.setValue(10) # Default to 10s, was 5s
    layout.addWidget(parent_widget.interval_spinbox)
    return layout

def create_boss_tree_widget(parent_widget):
    """Creates the boss tree widget."""
    tree = QTreeWidget(parent_widget)
    tree.setColumnCount(2)
    tree.setHeaderLabels(["Status", "Boss Name / Location"])
    tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    tree.setAlternatingRowColors(False)
    tree.setIndentation(20)
    return tree