import os
import sys

from PyQt6.QtGui import QFont, QFontDatabase, QIcon
from PyQt6.QtWidgets import QApplication

from . import crop
from .paths import resource
from .ui import theme
from .ui.splash import Splash
from .ui.window import MainWindow


def load_fonts() -> None:
    families = []
    for name in ("NotoSansTamil-tamil-Regular.ttf", "NotoSansTamil-tamil-Bold.ttf"):
        fid = QFontDatabase.addApplicationFont(str(resource("oru", "fonts", name)))
        if fid >= 0:
            families += QFontDatabase.applicationFontFamilies(fid)
    font = QFont()
    font.setFamilies(list(dict.fromkeys(families)) + ["Noto Sans", "DejaVu Sans", "Sans Serif"])
    font.setPixelSize(17)
    QApplication.setFont(font)


def run(argv=None) -> int:
    argv = list(sys.argv if argv is None else argv)
    app = QApplication(argv)
    app.setApplicationName("oru-udhavi")
    app.setDesktopFileName("oru-udhavi")
    app.setWindowIcon(QIcon(str(resource("assets", "icon.png"))))
    load_fonts()
    app.setStyleSheet(theme.STYLE)

    window = MainWindow(predictor=crop.CropPredictor.load())

    def show_main():
        window.show()
        window.raise_()
        window.activateWindow()

    skip = "--no-splash" in argv or os.environ.get("ORU_NO_SPLASH") == "1"
    if skip:
        show_main()
    else:
        splash = Splash()
        splash.finished.connect(show_main)
        splash.start()
        app._splash = splash  # keep a reference
    return app.exec()
