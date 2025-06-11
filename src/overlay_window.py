# src/overlay_window.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QPoint

class OverlayWindow(QWidget):
    def __init__(self, parent=None, text_color="white", font_size="15pt"):
        super().__init__(parent)
        # Nastavení okna, aby bylo bez rámečků, vždy nahoře a s průhledným pozadím
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.text_color = text_color
        self.font_size = font_size

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 5, 10, 5)

        self.label = QLabel("Overlay Active", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.label)
        
        self.setLayout(self.main_layout)
        self._apply_styles()

        # Uložíme si pozici pro přesouvání myší
        self._drag_pos = QPoint(0,0)

    def _apply_styles(self):
        """Aplikuje aktuální CSS styly na widgety."""
        self.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(30, 30, 30, 0.8); /* Tmavší průhledné pozadí pro lepší čitelnost */
                border: 1px solid #4C566A;
                border-radius: 8px;
            }}
            QLabel {{
                color: {self.text_color};
                font-size: {self.font_size};
                font-weight: bold;
                background-color: transparent;
                border: none;
            }}
        """)
        self.adjustSize() # Přizpůsobí velikost okna obsahu
        self.update()

    def update_styles(self, text_color, font_size):
        """Veřejná metoda pro aktualizaci stylů z hlavního okna."""
        self.text_color = text_color
        self.font_size = font_size
        self._apply_styles()

    def set_text(self, text):
        """Nastaví zobrazovaný text a přizpůsobí velikost okna."""
        self.label.setText(text)
        self.adjustSize()

    def show_overlay(self):
        """Zobrazí okno vpravo nahoře."""
        screen_geometry = QApplication.primaryScreen().geometry()
        # Přesuneme okno do pravého horního rohu s malým okrajem (20px)
        self.move(screen_geometry.width() - self.width() - 20, 20)
        self.show()

    def hide_overlay(self):
        self.hide()

    # --- Následující 3 metody zajišťují správné přesouvání okna myší ---
    
    def mousePressEvent(self, event):
        """Zaznamená počáteční bod při stisknutí levého tlačítka myši."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Přesouvá okno, pokud je levé tlačítko myši drženo."""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Resetuje pozici po uvolnění tlačítka."""
        self._drag_pos = QPoint(0,0)
        event.accept()