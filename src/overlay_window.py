from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QPoint

class OverlayWindow(QWidget):
    def __init__(self, parent=None, background_color="rgba(50, 50, 50, 200)", text_color="white", font_size="12pt"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.background_color = background_color
        self.text_color = text_color
        self.font_size = font_size

        self.layout = QVBoxLayout(self)
        self.label = QLabel("Simple Overlay Active", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)
        self.layout.setContentsMargins(0,0,0,0) # Remove margins if any for better dragging feel

        self._apply_styles()

        self.resize(300, 60) # Adjusted default size
        self._drag_pos = QPoint(0,0) # For dragging

    def _apply_styles(self):
        # Apply background color to the QWidget itself
        # Important: For WA_TranslucentBackground to work with a custom background color,
        # the color must have an alpha channel. Otherwise, the window might not be translucent.
        self.setStyleSheet(f"QWidget {{ background-color: {self.background_color}; border-radius: 5px; }}")

        # Apply text color and font size to the QLabel
        self.label.setStyleSheet(f"QLabel {{ color: {self.text_color}; font-size: {self.font_size}; background-color: transparent; }}")

    def update_styles(self, background_color, text_color, font_size):
        self.background_color = background_color
        self.text_color = text_color
        self.font_size = font_size
        self._apply_styles()
        # May need to trigger a repaint or resize if styles affect geometry significantly
        self.update() # Request a repaint

    def set_text(self, text):
        self.label.setText(text)

    def show_overlay(self):
        # Position in top-right corner of the primary screen
        screen_geometry = QApplication.primaryScreen().geometry()
        self.move(screen_geometry.width() - self.width() - 20, 20) # 20px padding
        self.show()

    def hide_overlay(self):
        self.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = QPoint(0,0)
        event.accept()