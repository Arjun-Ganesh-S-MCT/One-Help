"""Colours, icons and the stylesheet. Plain, high-contrast, large text."""
from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QImage, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

# Tactile (skeuomorphic) palette, 60 / 30 / 10: ivory surfaces, ink + sand, red for the one action.
IVORY = "#EFE9E0"
IVORY_HI = "#F8F4EE"
IVORY_LO = "#E3DBCF"
SAND = "#E2CBB5"
RED = "#D7191C"
RED_DARK = "#A81013"
INK = "#2B2A2E"
GREY = "#5F574F"        # small labels: 5.9:1 on ivory
LINE = "#CDB095"
SOFT = IVORY_LO
EDGE_LO = "#C9BCAA"

# 24x24 line icons
_ICONS = {
    "camera": '<rect x="3" y="7" width="18" height="13" rx="2"/><circle cx="12" cy="13.5" r="3.5"/><path d="M8 7l1.5-2.5h5L16 7"/>',
    "leaf": '<path d="M5 19C5 10 11 5 20 4c0 9-5 15-14 15z"/><path d="M5 19L14 10"/>',
    "list": '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4h6v3H9z"/><path d="M8.5 12h7M8.5 16h5"/>',
    "phone": '<path d="M6 3h4l2 5-2.5 1.5a11 11 0 005 5L16 12l5 2v4a2 2 0 01-2 2A16 16 0 014 5a2 2 0 012-2z"/>',
    "back": '<path d="M15 5l-7 7 7 7"/>',
    "road": '<path d="M7 21L10 3M17 21L14 3"/><path d="M12 5v3M12 11v3M12 17v3"/>',
    "trash": '<path d="M5 7h14M10 7V4h4v3M7 7l1 13h8l1-13M10 11v6M14 11v6"/>',
    "drain": '<rect x="3" y="8" width="18" height="8" rx="1"/><path d="M7 8v8M11 8v8M15 8v8"/>',
    "bulb": '<path d="M9 18h6M10 21h4M12 3a6 6 0 00-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0012 3z"/>',
    "water": '<path d="M12 3C8 9 6 12 6 15a6 6 0 0012 0c0-3-2-6-6-12z"/>',
    "bolt": '<path d="M13 2L5 14h6l-1 8 9-13h-6z"/>',
    "paw": '<circle cx="6.5" cy="10" r="1.8"/><circle cx="10.5" cy="6.5" r="1.8"/><circle cx="14.5" cy="6.5" r="1.8"/><circle cx="18" cy="10" r="1.8"/><path d="M12 11.5c-3 0-5 3-5 5 0 2 2 2.5 5 1.3 3 1.2 5 .7 5-1.3 0-2-2-5-5-5z"/>',
    "dots": '<circle cx="6" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="18" cy="12" r="1.6"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "mic": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0013 0M12 17.5V21M9 21h6"/>',
    "send": '<path d="M4 12L20 4l-5 16-3.5-6.5z"/><path d="M11.5 13.5L20 4"/>',
    "speaker": '<path d="M4 9.5h3.5L12 6v12l-4.5-3.5H4z"/><path d="M15.5 9a4 4 0 010 6M18 6.5a8 8 0 010 11"/>',
    "speaker_off": '<path d="M4 9.5h3.5L12 6v12l-4.5-3.5H4z"/><path d="M16 9.5l5 5M21 9.5l-5 5"/>',
    "chat": '<path d="M4 5h16v11H10l-5 4v-4H4z"/><path d="M8 9.5h8M8 12.5h5"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
}


def pixmap(name: str, color: str = INK, size: int = 28) -> QPixmap:
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{color}" '
           f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{_ICONS[name]}</svg>')
    scale = 2
    img = QImage(size * scale, size * scale, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    QSvgRenderer(QByteArray(svg.encode())).render(p)
    p.end()
    pm = QPixmap.fromImage(img)
    pm.setDevicePixelRatio(scale)
    return pm


def icon(name: str, color: str = INK, size: int = 28) -> QIcon:
    return QIcon(pixmap(name, color, size))



def shadow(widget, color="#7C644C", alpha=95, blur=22, dx=6, dy=6):
    """Soft cast shadow (light comes from the top left)."""
    fx = QGraphicsDropShadowEffect(widget)
    c = QColor(color)
    c.setAlpha(alpha)
    fx.setColor(c)
    fx.setBlurRadius(blur)
    fx.setOffset(dx, dy)
    widget.setGraphicsEffect(fx)


_RAISED = "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #FBF8F3, stop:1 #E6DED3)"
_PRESSED = "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #E2D9CC, stop:1 #EFE9E0)"
_WELL = "qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #E4DBCF, stop:1 #F2EDE5)"

STYLE = f"""
* {{ color: {INK}; font-size: 17px; }}
QMainWindow, QDialog, QWidget#page, QScrollArea, QScrollArea > QWidget > QWidget {{ background: {IVORY}; }}
QLabel {{ background: transparent; }}
QLabel#h1 {{ font-size: 22px; font-weight: 800; }}
QLabel#h2 {{ font-size: 18px; font-weight: 800; margin-top: 14px; }}
QLabel#muted {{ color: {GREY}; font-size: 15px; }}
QLabel#error {{ color: {RED_DARK}; font-weight: 800; }}
QLabel#hint {{ background: {_WELL}; border-left: 5px solid {RED}; border-radius: 10px; padding: 8px 10px; }}
QFrame#header {{ background: {IVORY}; border: none; }}
QFrame#header QLabel#h1 {{ background: {_WELL}; border: 1px solid {EDGE_LO}; border-right-color: #FFFFFF; border-bottom-color: #FFFFFF;
    border-radius: 14px; padding: 9px 14px; qproperty-alignment: AlignCenter; }}
QFrame#card {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #F9F6F0, stop:1 #E8E1D6);
    border: 1px solid #FFFFFF; border-right-color: {EDGE_LO}; border-bottom-color: {EDGE_LO}; border-radius: 22px; }}
QFrame#card:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #FFFFFF, stop:1 #EDE6DB); }}
QFrame#panel {{ background: {_WELL}; border: 1px solid {EDGE_LO}; border-right-color: #FFFFFF; border-bottom-color: #FFFFFF; border-radius: 16px; }}
QFrame#lcd {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #1B1A1E, stop:1 {INK}); border: 3px solid {IVORY_LO}; border-radius: 14px; }}
QFrame#lcd QLabel {{ color: #F3E6D6; }}
QPushButton {{ background: {_RAISED}; border: 1px solid #FFFFFF; border-right-color: {EDGE_LO}; border-bottom: 2px solid {EDGE_LO};
    border-radius: 14px; padding: 10px 16px; font-size: 17px; font-weight: 800; }}
QPushButton:hover {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #FFFFFF, stop:1 #EDE6DB); }}
QPushButton:pressed {{ background: {_PRESSED}; border: 1px solid {EDGE_LO}; border-right-color: #FFFFFF; border-bottom-color: #FFFFFF; padding-top: 12px; }}
QPushButton:disabled {{ color: {GREY}; background: {IVORY_LO}; border: 1px solid {LINE}; }}
QPushButton:focus {{ border: 2px solid {INK}; }}
QPushButton#primary {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #F04A4D, stop:0.5 #D7191C, stop:1 #BC1217);
    border: 1px solid #F27B7D; border-bottom: 3px solid #8E0D10; color: #FFFFFF; font-size: 19px; padding: 14px 18px; border-radius: 18px; }}
QPushButton#primary:hover {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #F55B5E, stop:0.5 #E02024, stop:1 #C4131A); }}
QPushButton#primary:pressed {{ background: {RED_DARK}; border-bottom: 1px solid #8E0D10; padding-top: 16px; }}
QPushButton#primary:disabled {{ background: {IVORY_LO}; color: {GREY}; border: 1px solid {LINE}; }}
QPushButton#dark {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #55545B, stop:0.6 {INK}, stop:1 #1E1D21); color: #F4ECE2;
    border: 1px solid #6A6970; border-bottom: 3px solid #131215; }}
QPushButton#link {{ background: transparent; border: none; padding: 8px 12px; }}
QPushButton#link:hover {{ background: {IVORY_LO}; }}
QPushButton#tile {{ text-align: left; padding: 12px 12px; min-height: 40px; }}
QPushButton#tile:checked {{ background: {_PRESSED}; border: 1px solid {EDGE_LO}; border-right-color: #FFFFFF; border-bottom-color: #FFFFFF; border-left: 6px solid {RED}; }}
QLineEdit, QPlainTextEdit, QTextEdit {{ background: {_WELL}; border: 1px solid {EDGE_LO}; border-right-color: #FFFFFF; border-bottom-color: #FFFFFF;
    border-radius: 14px; padding: 10px 12px; selection-background-color: {INK}; selection-color: #FFFFFF; }}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {{ border: 2px solid {INK}; }}
QPlainTextEdit#paper, QTextEdit#paper {{ background: #FFFDF8; border: 1px solid {LINE}; border-radius: 6px; }}
QFrame#bubble_me {{ background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #F04A4D, stop:0.5 #D7191C, stop:1 #BC1217); border-bottom: 2px solid #8E0D10; border-radius: 18px; }}
QFrame#bubble_me QLabel {{ color: #FFFFFF; }}
QFrame#bubble_ai {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #F9F6F0, stop:1 #E8E1D6); border: 1px solid #FFFFFF; border-right-color: {EDGE_LO}; border-bottom-color: {EDGE_LO}; border-radius: 18px; }}
QPushButton#mic {{ border-radius: 30px; min-width: 60px; max-width: 60px; min-height: 60px; max-height: 60px; padding: 0;
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #6A6970, stop:0.55 {INK}, stop:1 #1E1D21); border: 3px solid #8A8990; border-bottom-color: #131215; }}
QPushButton#mic:checked {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #F7706F, stop:0.55 {RED}, stop:1 {RED_DARK}); border: 3px solid #F7A0A0; border-bottom-color: #8E0D10; }}
QRadioButton {{ spacing: 10px; padding: 6px 0; }}
QRadioButton::indicator {{ width: 20px; height: 20px; border-radius: 11px; background: {_WELL}; border: 1px solid {EDGE_LO}; }}
QRadioButton::indicator:checked {{ background: qradialgradient(cx:0.5,cy:0.5,radius:0.5, stop:0 {RED}, stop:0.45 {RED}, stop:0.55 {IVORY_LO}, stop:1 {IVORY_LO}); }}
QComboBox {{ background: {_RAISED}; border: 1px solid #FFFFFF; border-bottom: 2px solid {EDGE_LO}; border-radius: 12px; padding: 8px 12px; }}
QScrollBar:vertical {{ width: 12px; background: transparent; }}
QScrollBar::handle:vertical {{ background: {SAND}; border-radius: 6px; min-height: 30px; margin: 2px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QToolTip {{ background: {INK}; color: #F3E6D6; border: none; padding: 6px 8px; }}
"""
