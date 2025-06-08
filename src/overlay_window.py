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

        # Main layout for the OverlayWindow itself, to hold the content_widget
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        # Create the content widget that will have the background and actual content
        self.content_widget = QWidget(self)
        self.main_layout.addWidget(self.content_widget)

        # Layout for the content_widget
        self.content_layout = QVBoxLayout(self.content_widget)
        self.label = QLabel("Simple Overlay Active", self.content_widget)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.label)
        self.content_layout.setContentsMargins(5, 5, 5, 5) # Padding inside the background

        self._apply_styles()

        self.resize(300, 60) # Adjusted default size
        self._drag_pos = QPoint(0,0) # For dragging

    def _apply_styles(self):
        # Make the OverlayWindow itself transparent
        super().setStyleSheet("QWidget { background-color: transparent; border: none; }") # Use super to avoid recursion if self.setStyleSheet is overridden

        # Apply background color and border-radius to the content_widget
        # Important: For WA_TranslucentBackground on parent to work with a custom background color on child,
        # the color must have an alpha channel for semi-transparency. Otherwise, it will be solid.
        self.content_widget.setStyleSheet(f"QWidget {{ background-color: {self.background_color}; border-radius: 5px; }}")

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