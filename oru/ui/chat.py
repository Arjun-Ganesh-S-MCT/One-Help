"""The talking helper screen: chat bubbles, microphone, spoken replies."""
from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (QComboBox, QDialog, QFrame, QHBoxLayout, QLineEdit, QScrollArea,
                             QVBoxLayout, QWidget)

from .. import assistant as A
from .. import i18n
from ..i18n import tr
from ..voice import Job, Listener, Speaker
from . import theme
from .widgets import button, label


class Bubble(QFrame):
    def __init__(self, text: str, mine: bool):
        super().__init__()
        self.setObjectName("bubble_me" if mine else "bubble_ai")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        self.text = label()
        self.text.setText(text)
        self.text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.text.setStyleSheet("font-size: 19px;")
        lay.addWidget(self.text)


class SetupDialog(QDialog):
    """Pick the AI service and paste its key. Free choices come first."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("chat_key_title"))
        self.setMinimumWidth(440)
        lay = QVBoxLayout(self)
        lay.setSpacing(10)
        lay.addWidget(label("h2"))
        lay.itemAt(0).widget().setText(tr("chat_setup_which"))
        self.combo = QComboBox()
        for pid, p in A.PROVIDERS.items():
            self.combo.addItem(p["name"], pid)
        self.combo.setCurrentIndex(max(0, self.combo.findData(A.provider())))
        lay.addWidget(self.combo)
        self.info = label("muted")
        self.key = QLineEdit()
        self.key.setPlaceholderText(tr("chat_setup_key"))
        self.key.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(self.info)
        lay.addWidget(self.key)
        self.save = button(primary=True)
        self.save.setText(tr("chat_setup_save"))
        self.save.clicked.connect(self._save)
        lay.addWidget(self.save)
        self.combo.currentIndexChanged.connect(self._changed)
        self.key.returnPressed.connect(self._save)
        self._changed()

    def _changed(self):
        p = A.PROVIDERS[self.combo.currentData()]
        self.key.setVisible(p["needs_key"])
        self.info.setText(tr("chat_setup_get", w=p["where"]) if p["needs_key"] else tr("chat_setup_local"))
        self.key.setText(A.api_key(self.combo.currentData()))

    def _save(self):
        pid = self.combo.currentData()
        if A.PROVIDERS[pid]["needs_key"] and not self.key.text().strip():
            self.key.setFocus()
            return
        A.save_settings(pid, self.key.text())
        self.accept()


class ChatPage(QWidget):
    open_form = pyqtSignal(str)       # issue id

    def __init__(self, assistant: A.Assistant = None):
        super().__init__()
        self.ai = assistant or A.Assistant()
        self.speaker = Speaker(self)
        self.listener = Listener(self)
        self._busy = False
        self._pending_text = ""
        self.voice_on = self.speaker.available()
        self._status_key = ""
        self._hello = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        top = QHBoxLayout()
        top.setContentsMargins(16, 8, 16, 0)
        self.voice_btn = button()
        self.voice_btn.setObjectName("link")
        self.voice_btn.clicked.connect(self._toggle_voice)
        self.new_btn = button()
        self.new_btn.setObjectName("link")
        self.new_btn.clicked.connect(self.new_chat)
        self.setup_btn = button()
        self.setup_btn.setObjectName("link")
        self.setup_btn.clicked.connect(self._open_setup)
        top.addWidget(self.voice_btn)
        top.addWidget(self.setup_btn)
        top.addStretch(1)
        top.addWidget(self.new_btn)
        outer.addLayout(top)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.body = QWidget()
        self.body.setObjectName("page")
        self.col = QVBoxLayout(self.body)
        self.col.setContentsMargins(16, 10, 16, 10)
        self.col.setSpacing(10)
        self.col.addStretch(1)
        self.scroll.setWidget(self.body)
        outer.addWidget(self.scroll, 1)

        self.status = label("muted")
        self.status.setContentsMargins(18, 0, 18, 0)
        self.status.hide()
        outer.addWidget(self.status)

        bar = QHBoxLayout()
        bar.setContentsMargins(14, 8, 14, 14)
        bar.setSpacing(8)
        self.mic = button()
        self.mic.setObjectName("mic")
        self.mic.setCheckable(True)
        self.mic.setIconSize(QSize(26, 26))
        self.mic.clicked.connect(self._mic_clicked)
        self.edit = QLineEdit()
        self.edit.returnPressed.connect(self._send_typed)
        self.send = button(primary=True)
        self.send.setIcon(theme.icon("send", "#FFFFFF", 24))
        self.send.setStyleSheet("padding: 11px 16px;")
        self.send.clicked.connect(self._send_typed)
        bar.addWidget(self.mic)
        bar.addWidget(self.edit, 1)
        bar.addWidget(self.send)
        outer.addLayout(bar)

        self.listener.heard.connect(self._heard)
        self.listener.error.connect(self._voice_error)
        self.listener.busy.connect(self._listener_busy)
        self.speaker.started.connect(lambda: self._set_status("chat_speaking"))
        self.speaker.finished.connect(lambda: self._set_status(""))
        self.speaker.error.connect(lambda c: self._note(tr("chat_err_tts")) if c.startswith("tts") or c == "playback" else None)
        self._hello = self._add("ai", tr("chat_hello"))
        self.retranslate()

    # ------------------------------------------------------------ bubbles
    def _add(self, who: str, text: str) -> Bubble:
        b = Bubble(text, who == "me")
        row = QHBoxLayout()
        if who == "me":
            row.addStretch(1)
            row.addWidget(b, 4)
        else:
            row.addWidget(b, 4)
            row.addStretch(1)
        self.col.insertLayout(self.col.count() - 1, row)
        QTimer.singleShot(30, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()))
        return b

    def _note(self, text: str):
        self.status.setText(text)
        self.status.show()
        self._status_key = ""

    def _set_status(self, key: str):
        self._status_key = key
        if key:
            self.status.setText(tr(key))
            self.status.show()
        else:
            self.status.hide()

    def _clear_rows(self):
        while self.col.count() > 1:
            item = self.col.takeAt(0)
            lay = item.layout()
            if lay:
                while lay.count():
                    w = lay.takeAt(0).widget()
                    if w:
                        w.deleteLater()
                lay.deleteLater()

    # ------------------------------------------------------------ sending
    def _send_typed(self):
        t = self.edit.text().strip()
        if t:
            self.edit.clear()
            self.submit(t)

    def submit(self, text: str):
        if self._busy:
            return
        self.speaker.stop()
        self._add("me", text)
        self._ask(text)

    def _ask(self, text: str):
        self._busy = True
        self._pending_text = text
        self._enable(False)
        self._set_status("chat_thinking")
        lang = i18n.lang()
        job = Job(lambda: self.ai.ask(text, lang), self)
        job.done.connect(self._answered)
        job.failed.connect(self._failed)
        self._job = job
        job.start()

    def _answered(self, result):
        reply, actions = result
        self._busy = False
        self._enable(True)
        self._set_status("")
        self._add("ai", reply)
        for a in actions:
            if a["type"] == "open_form":
                self._add_form_button(a["issue_id"])
        if self.voice_on:
            self.speaker.speak(reply, i18n.lang())

    def _add_form_button(self, issue_id: str):
        b = button(primary=True)
        b.setText(tr("chat_open_form"))
        b.clicked.connect(lambda: self.open_form.emit(issue_id))
        row = QHBoxLayout()
        row.addWidget(b)
        row.addStretch(1)
        self.col.insertLayout(self.col.count() - 1, row)

    def _failed(self, code: str):
        self._busy = False
        self._enable(True)
        self._set_status("")
        if code == "no_key" or code == "bad_key":
            if code == "bad_key":
                self._note(tr("chat_err_bad_key"))
            if self._ask_key():
                self._ask(self._pending_text)
                return
            return
        key = "chat_err_" + code
        self._note(tr(key) if key in i18n.STRINGS else tr("chat_err_server"))

    def _ask_key(self) -> bool:
        return SetupDialog(self).exec() == QDialog.DialogCode.Accepted

    # ------------------------------------------------------------ voice
    def _toggle_voice(self):
        self.voice_on = not self.voice_on
        if self.voice_on and not self.speaker.available():
            self.voice_on = False
            self._note(tr("chat_no_voice_out"))
        if not self.voice_on:
            self.speaker.stop()
        self._retitle()

    def _mic_clicked(self):
        if self.listener.recording:
            self._set_status("chat_recognising")
            self.listener.stop()
            return
        if not self.listener.available():
            self.mic.setChecked(False)
            self._note(tr("chat_no_voice_in"))
            return
        self.speaker.stop()           # do not record the helper's own voice
        self.listener.start(i18n.lang())

    def _listener_busy(self, on: bool):
        if on and self.listener.recording:
            self._set_status("chat_listening")
        self.mic.setChecked(on and self.listener.recording)
        self.mic.setEnabled(True)

    def _heard(self, text: str):
        self._set_status("")
        self.submit(text)

    def _voice_error(self, code: str):
        self.mic.setChecked(False)
        self._set_status("")
        key = "chat_err_" + code
        self._note(tr(key) if key in i18n.STRINGS else tr("chat_err_offline"))

    def _enable(self, on: bool):
        self.send.setEnabled(on)
        self.edit.setEnabled(on)
        self.mic.setEnabled(on)
        if on:
            self.edit.setFocus()

    def _open_setup(self):
        SetupDialog(self).exec()

    # ------------------------------------------------------------ misc
    def new_chat(self):
        self.speaker.stop()
        self.listener.cancel()
        self.ai.reset()
        self._clear_rows()
        self._hello = self._add("ai", tr("chat_hello"))
        self.status.hide()

    def hideEvent(self, e):
        self.speaker.stop()
        self.listener.cancel()
        super().hideEvent(e)

    def _retitle(self):
        self.voice_btn.setIcon(theme.icon("speaker" if self.voice_on else "speaker_off", theme.INK, 22))
        self.voice_btn.setText(" " + tr("chat_voice_on" if self.voice_on else "chat_voice_off"))

    def retranslate(self):
        self.new_btn.setText(tr("chat_new"))
        self.setup_btn.setText(tr("chat_setup"))
        self.edit.setPlaceholderText(tr("chat_placeholder"))
        self.mic.setIcon(theme.icon("mic", "#F4ECE2", 26))
        self._retitle()
        if self._hello is not None and len(self.ai.history) == 0:
            self._hello.text.setText(tr("chat_hello"))
        if self._status_key:
            self.status.setText(tr(self._status_key))
