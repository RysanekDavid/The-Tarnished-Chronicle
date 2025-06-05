from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt

class OverlayWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.layout = QVBoxLayout(self)
        self.label = QLabel("Simple Overlay Active", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)

        self.resize(300, 100) # Default size

    def set_text(self, text):
        self.label.setText(text)

    def show_overlay(self):
        # Potentially center on parent or screen
        if self.parent():
            parent_rect = self.parent().geometry()
            self.move(parent_rect.center().x() - self.width() / 2,
                        parent_rect.center().y() - self.height() / 2)
        self.show()

    def hide_overlay(self):
        self.hide()