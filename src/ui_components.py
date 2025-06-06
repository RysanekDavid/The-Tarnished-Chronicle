from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QTreeWidget, QHeaderView, QComboBox, QVBoxLayout, QWidget
)
from PySide6.QtCore import Qt

def create_file_slot_layout(parent_widget):
    """Creates the layout for file path and character slot selection."""
    layout = QHBoxLayout()
    layout.addWidget(QLabel("Save File:", parent_widget))
    parent_widget.save_file_path_input = QLineEdit(parent_widget)
    parent_widget.save_file_path_input.setPlaceholderText("Cesta k ER0000.sl2")
    # Default path can be set in gui.py or loaded from config
    # parent_widget.save_file_path_input.setText("C:\\Users\\dawel\\AppData\\Roaming\\EldenRing\\76561198082650286\\ER0000.sl2")
    layout.addWidget(parent_widget.save_file_path_input)

    parent_widget.browse_button = QPushButton("Procházet...", parent_widget)
    layout.addWidget(parent_widget.browse_button)

    layout.addWidget(QLabel("Character:", parent_widget)) # Changed label from "Slot:"
    parent_widget.character_slot_combobox = QComboBox(parent_widget)
    parent_widget.character_slot_combobox.setPlaceholderText("Select Character")
    parent_widget.character_slot_combobox.setEnabled(False) # Enable after characters are loaded
    layout.addWidget(parent_widget.character_slot_combobox)
    return layout

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

def create_boss_tree_widget(parent_widget):
    """Creates the boss tree widget."""
    tree = QTreeWidget(parent_widget)
    tree.setColumnCount(3) # Increased to 3 columns
    tree.setHeaderLabels(["Status", "Boss Name / Location", ""]) # Removed header text for the third column
    tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # Status
    tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch) # Boss Name / Location
    tree.setColumnWidth(2, 35) # Set a fixed width for the checkbox column
    tree.setAlternatingRowColors(False)
    tree.setIndentation(20)
    return tree

def create_overlay_settings_panel_layout(parent_widget): # Renamed for clarity
    """Creates the layout for overlay customization input fields."""
    settings_layout = QVBoxLayout() # Changed to QVBoxLayout for better arrangement of multiple settings rows if needed in future

    # Background Color
    bg_layout = QHBoxLayout()
    bg_layout.addWidget(QLabel("BG Color:", parent_widget))
    parent_widget.overlay_bg_color_input = QLineEdit("rgba(30, 30, 30, 220)", parent_widget)
    parent_widget.overlay_bg_color_input.setPlaceholderText("e.g., rgba(0,0,0,150) or blue")
    bg_layout.addWidget(parent_widget.overlay_bg_color_input)
    settings_layout.addLayout(bg_layout)

    # Text Color
    text_color_layout = QHBoxLayout()
    text_color_layout.addWidget(QLabel("Text Color:", parent_widget))
    parent_widget.overlay_text_color_input = QLineEdit("lightblue", parent_widget)
    parent_widget.overlay_text_color_input.setPlaceholderText("e.g., white or #FF0000")
    text_color_layout.addWidget(parent_widget.overlay_text_color_input)
    settings_layout.addLayout(text_color_layout)

    # Font Size
    font_size_layout = QHBoxLayout()
    font_size_layout.addWidget(QLabel("Font Size:", parent_widget))
    parent_widget.overlay_font_size_input = QLineEdit("10pt", parent_widget)
    parent_widget.overlay_font_size_input.setPlaceholderText("e.g., 12pt or 16px")
    font_size_layout.addWidget(parent_widget.overlay_font_size_input)
    settings_layout.addLayout(font_size_layout)
    
    parent_widget.apply_overlay_settings_button = QPushButton("Apply Settings", parent_widget) # Shortened button text
    settings_layout.addWidget(parent_widget.apply_overlay_settings_button, 0, Qt.AlignmentFlag.AlignRight) # Align button to the right

    # Create a container widget for this layout
    settings_panel_widget = QWidget()
    settings_panel_widget.setLayout(settings_layout)
    
    return settings_panel_widget