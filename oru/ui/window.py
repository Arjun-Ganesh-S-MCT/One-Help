from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QIcon
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QMainWindow, QStackedWidget,
                             QVBoxLayout, QWidget)

from .. import i18n
from ..i18n import tr
from ..paths import resource
from ..store import Store
from . import theme
from .chat import ChatPage
from .pages import (CropPage, EmergencyDialog, HistoryPage, HomePage, ReportPage,
                    ResultPage)
from .widgets import button, label


class MainWindow(QMainWindow):
    def __init__(self, predictor=None, store: Store = None):
        super().__init__()
        self.store = store or Store()
        self.setWindowIcon(QIcon(str(resource("assets", "icon.png"))))
        self.resize(560, 860)
        self.setMinimumSize(460, 620)

        root = QWidget()
        root.setObjectName("page")
        col = QVBoxLayout(root)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)

        header = QFrame()
        header.setObjectName("header")
        h = QHBoxLayout(header)
        h.setContentsMargins(12, 8, 12, 8)
        self.back = button()
        self.back.setObjectName("link")
        self.back.setIcon(theme.icon("back", theme.INK, 24))
        self.back.clicked.connect(self.go_back)
        self.title = label("h1", wrap=False)
        self.lang_btn = button()
        self.lang_btn.setIcon(theme.icon("globe", theme.INK, 22))
        self.lang_btn.setStyleSheet("padding: 6px 12px; font-size: 16px;")
        self.lang_btn.clicked.connect(i18n.toggle)
        h.addWidget(self.back)
        h.addWidget(self.title, 1)
        h.addWidget(self.lang_btn)
        col.addWidget(header)

        self.stack = QStackedWidget()
        col.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        self.home = HomePage()
        self.report = ReportPage()
        self.result = ResultPage(self.store)
        self.history = HistoryPage(self.store)
        self.crop = CropPage(predictor)
        self.chat = ChatPage()
        self.pages = {"home": self.home, "report": self.report, "result": self.result,
                      "history": self.history, "crop": self.crop, "chat": self.chat}
        for p in self.pages.values():
            self.stack.addWidget(p)
        self._trail = ["home"]

        self.home.open_report.connect(lambda: self.goto("report"))
        self.home.open_crop.connect(lambda: self.goto("crop"))
        self.home.open_chat.connect(lambda: self.goto("chat"))
        self.chat.open_form.connect(self._chat_to_form)
        self.home.open_history.connect(self._open_history)
        self.home.open_emergency.connect(lambda: EmergencyDialog(self).exec())
        self.report.make_letter.connect(self._make_letter)
        self.result.changed.connect(self.history.refresh)
        self.history.open_row.connect(self._open_saved)
        i18n.bus.changed.connect(self.retranslate)
        self.goto("home", push=False)
        self.retranslate()

    # navigation
    def goto(self, name: str, push: bool = True):
        if push:
            self._trail.append(name)
        self.stack.setCurrentWidget(self.pages[name])
        self.back.setVisible(name != "home")
        self._update_title()

    def go_back(self):
        if len(self._trail) > 1:
            self._trail.pop()
        name = self._trail[-1]
        self.goto(name, push=False)

    def _chat_to_form(self, issue_id: str):
        self.report.preselect(issue_id)
        self.goto("report")

    def _open_history(self):
        self.history.refresh()
        self.goto("history")

    def _make_letter(self, complaint, photo):
        self.result.show_complaint(complaint, i18n.lang())
        self.report.reset()
        # after the letter, "back" should return to home, not to the filled form
        self._trail = ["home"]
        self.goto("result")

    def _open_saved(self, row):
        self.result.show_saved(row)
        self.goto("result")

    def _update_title(self):
        name = self._trail[-1]
        titles = {"home": "", "report": "report_title", "result": "result_title",
                  "history": "history_title", "crop": "crop_title", "chat": "chat_title"}
        key = titles[name]
        self.title.setText(tr(key) if key else tr("app_name"))

    def retranslate(self):
        self.setWindowTitle(tr("app_name") + " – Oru Udhavi")
        self.lang_btn.setText(" " + tr("lang_button"))
        self.back.setText(" " + tr("back"))
        self._update_title()
        for p in self.pages.values():
            p.retranslate()
