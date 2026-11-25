from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
                             QVBoxLayout, QWidget)

from . import theme


class MenuCard(QFrame):
    """Big tappable card: icon, a main line and a smaller second line."""
    clicked = pyqtSignal()

    def __init__(self, icon_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(96)
        theme.shadow(self, blur=26, dx=8, dy=8)
        row = QHBoxLayout(self)
        row.setContentsMargins(18, 12, 18, 12)
        row.setSpacing(16)
        self.icon = QLabel()
        self.icon.setPixmap(theme.pixmap(icon_name, theme.INK, 44))
        self.icon.setFixedSize(48, 48)
        col = QVBoxLayout()
        col.setSpacing(2)
        self.title = QLabel()
        self.title.setStyleSheet("font-size: 21px; font-weight: 800;")
        self.title.setWordWrap(True)
        self.sub = QLabel()
        self.sub.setObjectName("muted")
        self.sub.setWordWrap(True)
        col.addWidget(self.title)
        col.addWidget(self.sub)
        row.addWidget(self.icon)
        row.addLayout(col, 1)

    def set_text(self, title: str, sub: str = ""):
        self.title.setText(title)
        self.sub.setText(sub)
        self.sub.setVisible(bool(sub))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.rect().contains(e.position().toPoint()):
            self.clicked.emit()


def scrolling(content: QWidget) -> QScrollArea:
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setFrameShape(QFrame.Shape.NoFrame)
    sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    sa.setWidget(content)
    return sa


def page_body(spacing: int = 8):
    """A padded vertical column; returns (widget, layout)."""
    w = QWidget()
    w.setObjectName("page")
    lay = QVBoxLayout(w)
    lay.setContentsMargins(22, 14, 22, 22)
    lay.setSpacing(spacing)
    return w, lay


def label(obj_name: str = "", wrap: bool = True) -> QLabel:
    lb = QLabel()
    if obj_name:
        lb.setObjectName(obj_name)
    lb.setWordWrap(wrap)
    return lb


def button(primary: bool = False, tile: bool = False) -> QPushButton:
    b = QPushButton()
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    if primary:
        b.setObjectName("primary")
        theme.shadow(b, "#A81013", 110, 20, 0, 8)
    if tile:
        b.setObjectName("tile")
        b.setCheckable(True)
        theme.shadow(b, blur=14, dx=4, dy=4)
    return b
