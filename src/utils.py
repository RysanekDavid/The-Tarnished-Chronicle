# src/utils.py

from PySide6.QtCore import QSize, QByteArray, Qt
from PySide6.QtGui import QColor, QPixmap

def create_colored_pixmap(icon_path: str, color: QColor, size: QSize) -> QPixmap:
    """
    Loads an SVG icon, replaces its 'currentColor' with a specified QColor,
    and returns it as a scaled QPixmap.
    """
    try:
        with open(icon_path, 'r', encoding='utf-8') as f:
            svg_data = f.read()
        
        colored_svg_data = svg_data.replace('currentColor', color.name())
        byte_array = QByteArray(colored_svg_data.encode('utf-8'))
        
        pixmap = QPixmap()
        pixmap.loadFromData(byte_array)
        
        return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
    except Exception as e:
        print(f"Error creating colored pixmap for {icon_path}: {e}")
        return QPixmap()