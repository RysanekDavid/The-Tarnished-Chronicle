# src/overlay_window.py
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QScrollArea
from PySide6.QtCore import Qt, QPoint, Signal

FULL_MODE_WIDTH = 340
FULL_MODE_LIST_HEIGHT = 480


class OverlayWindow(QWidget):
    position_changed = Signal(QPoint)

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
        self._click_through = False

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 5, 10, 5)

        self.label = QLabel("Overlay Active", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.label)

        # Full mode: scrollable boss checklist rendered as one rich-text label.
        # A single label is far cheaper than hundreds of widgets.
        self.boss_list_label = QLabel(self)
        self.boss_list_label.setTextFormat(Qt.TextFormat.RichText)
        self.boss_list_label.setWordWrap(True)
        self.boss_list_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.boss_list_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.boss_list_scroll = QScrollArea(self)
        self.boss_list_scroll.setObjectName("bossListScroll")
        self.boss_list_scroll.setWidgetResizable(True)
        self.boss_list_scroll.setWidget(self.boss_list_label)
        self.boss_list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.boss_list_scroll.setFixedSize(FULL_MODE_WIDTH, FULL_MODE_LIST_HEIGHT)
        self.boss_list_scroll.hide()
        self.main_layout.addWidget(self.boss_list_scroll)

        self.hint_label = QLabel("F8 mini/full  •  F9 click-through", self)
        self.hint_label.setObjectName("hintLabel")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.hint_label)

        self.setLayout(self.main_layout)
        self._apply_styles()

        # Uložíme si pozici pro přesouvání myší
        self._drag_pos = QPoint(0,0)
        self._was_dragged = False

    def _apply_styles(self):
        """Aplikuje aktuální CSS styly na widgety."""
        # Orange border doubles as the visual cue that clicks pass through
        # the overlay (it cannot be dragged in that state).
        border_color = "#D08770" if self._click_through else "#4C566A"
        self.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(30, 30, 30, 0.8); /* Tmavší průhledné pozadí pro lepší čitelnost */
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QLabel {{
                color: {self.text_color};
                font-size: {self.font_size};
                font-weight: bold;
                background-color: transparent;
                border: none;
            }}
            QLabel#hintLabel {{
                color: #7a8494;
                font-size: 9pt;
                font-weight: normal;
            }}
            QScrollArea#bossListScroll {{
                background-color: transparent;
                border: none;
            }}
            QScrollArea#bossListScroll > QWidget > QWidget {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: rgba(46, 52, 64, 0.6);
                width: 10px;
                margin: 0px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: #4C566A;
                min-height: 24px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #5E81AC;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
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

    def set_mode(self, mode: str):
        """Switches between 'mini' (stats only) and 'full' (stats + boss list)."""
        self.boss_list_scroll.setVisible(mode == "full")
        self.adjustSize()

    def set_boss_list_html(self, html: str):
        self.boss_list_label.setText(html)

    def set_click_through(self, enabled: bool):
        """Lets mouse clicks pass through the overlay into the game.
        Changing the flag recreates the native window, so re-show in place."""
        if enabled == self._click_through:
            return
        self._click_through = enabled
        position = self.pos()
        was_visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowTransparentForInput, enabled)
        self._apply_styles()
        if was_visible:
            self.move(position)
            self.show()

    def is_click_through(self) -> bool:
        return self._click_through

    def show_overlay(self, position: QPoint | None = None):
        """Zobrazí okno na uložené pozici, jinak vpravo nahoře."""
        if position is not None:
            self.move(position)
        else:
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
            self._was_dragged = True
            event.accept()

    def mouseReleaseEvent(self, event):
        """Resetuje pozici po uvolnění tlačítka a oznámí nové umístění."""
        self._drag_pos = QPoint(0,0)
        if self._was_dragged:
            self._was_dragged = False
            self.position_changed.emit(self.pos())
        event.accept()

    def wheelEvent(self, event):
        """The overlay is a non-activating Tool window, so Windows often
        won't deliver wheel events to its scroll area. Drive the scrollbar
        manually so the boss list scrolls regardless of focus."""
        if self.boss_list_scroll.isVisible():
            bar = self.boss_list_scroll.verticalScrollBar()
            # One wheel notch (120 units) scrolls ~60px of the list.
            steps = event.angleDelta().y() / 120.0
            bar.setValue(bar.value() - int(steps * 60))
            event.accept()
        else:
            event.ignore()
