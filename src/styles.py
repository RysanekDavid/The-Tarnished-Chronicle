from PySide6.QtGui import QColor

STYLE_SHEET = """
    QWidget {
        background-color: #2E3440; /* Nord Polar Night - Base background */
        color: #D8DEE9; /* Nord Snow Storm - Default text */
        font-family: Segoe UI, Arial, sans-serif; /* Cleaner font */
    }
    QTreeWidget {
        background-color: #2E3440; /* Darker background for the tree content area */
        border: 1px solid #4C566A; /* Nord Polar Night - Border */
        color: #ECEFF4; /* Nord Snow Storm - Light text for items */
        alternate-background-color: #3B4252; /* Slightly lighter for alternating rows if enabled */
    }
    QTreeWidget::item {
        padding: 6px;
        border-bottom: 1px solid #3B4252; /* Separator line */
    }
    QTreeWidget::item:selected {
        background-color: #88C0D0; /* Nord Frost - Selection */
        color: #2E3440; /* Dark text on selection */
    }
    QTreeWidget::item:hover {
        background-color: #434C5E; /* Nord Polar Night - Hover */
    }
    QHeaderView::section {
        background-color: #3B4252; /* Header background */
        color: #ECEFF4; /* Header text color */
        padding: 5px;
        border: none; /* Remove default border */
        border-bottom: 1px solid #4C566A; /* Bottom border for header section */
        font-weight: bold;
    }
    QPushButton {
        background-color: #4C566A;
        color: #ECEFF4;
        border: 1px solid #5E81AC;
        padding: 5px 10px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background-color: #5E81AC;
    }
    QPushButton:pressed {
        background-color: #81A1C1;
    }
    QPushButton:disabled {
        background-color: #434C5E;
        color: #6c757d;
    }
    QLineEdit, QSpinBox {
        background-color: #3B4252;
        color: #ECEFF4;
        border: 1px solid #4C566A;
        padding: 4px;
        border-radius: 3px;
    }
    QLabel {
        color: #D8DEE9;
        padding: 2px;
    }
    QSpinBox::up-button, QSpinBox::down-button {
         subcontrol-origin: border;
         subcontrol-position: top right; /* position at the top right corner */
         width: 16px;
         border-image: none; /* Or specify images */
         border-width: 1px;
         border-style: solid;
         border-color: #4C566A;
         background-color: #434C5E;
    }
    QSpinBox::up-arrow {
         image: url(none); /* Use text or custom icon */
    }
    QSpinBox::down-arrow {
         image: url(none);
    }
    /* Styles for OverlayWindow */
    OverlayWindow {
        background-color: rgba(46, 52, 64, 0.8); /* Semi-transparent Nord Polar Night */
        border: 1px solid #88C0D0; /* Nord Frost for border */
    }
    OverlayWindow QLabel {
        color: #ECEFF4; /* Nord Snow Storm - Light text */
        font-size: 16px;
        font-weight: bold;
        padding: 10px;
    }
"""

def apply_app_styles(app_widget):
    app_widget.setStyleSheet(STYLE_SHEET)

# Define colors for tree items (can be imported by gui.py)
DEFEATED_TEXT_COLOR = QColor("#98C379")  # Greenish
NOT_DEFEATED_TEXT_COLOR = QColor("#E06C75") # Reddish
LOCATION_TEXT_COLOR = QColor("#D8DEE9") # Default light text
BOSS_NAME_TEXT_COLOR = QColor("#D8DEE9")

LOCATION_ITEM_BG_COLOR = QColor("#3B4252") # Slightly lighter than tree background
BOSS_ITEM_BG_COLOR = QColor("#2E3440") # Same as tree background or slightly different