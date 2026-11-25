"""Render every screen of the Linux app to PNG (offscreen) for checking the design."""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PyQt6.QtWidgets import QApplication
from oru import i18n
from oru.app import load_fonts
from oru.ui import theme
# The sandbox has no sound card, and Qt Multimedia crashes without one: use silent stand-ins here.
from PyQt6.QtCore import QObject, pyqtSignal
class _Quiet(QObject):
    busy = error = finished = heard = started = pyqtSignal(object)
    def __init__(self, *a, **k): super().__init__(*a)
    def available(self): return False
    def __getattr__(self, n): return lambda *a, **k: None
import oru.ui.chat as _chat
_chat.Speaker = _chat.Listener = _Quiet
from oru.ui.window import MainWindow
from oru.store import Store
from oru import complaint as C

out = sys.argv[1] if len(sys.argv) > 1 else "screenshots-linux"
os.makedirs(out, exist_ok=True)
app = QApplication([])
load_fonts(); app.setStyleSheet(theme.STYLE)
w = MainWindow(predictor=None, store=Store(__import__("pathlib").Path("/tmp/oru_shot.db")))
w.show()
def snap(n):
    app.processEvents(); w.grab().save(f"{out}/{i18n.lang()}-{n}.png")
for lang in ("en", "ta"):
    i18n.set_lang(lang) if hasattr(i18n, "set_lang") else None
    w.goto("home", push=False); snap("1-home")
    w.goto("report"); snap("2-report")
    w.goto("crop"); snap("3-crop")
    w.goto("chat"); snap("4-chat")
    w.goto("history"); snap("5-history")
print("ok")
