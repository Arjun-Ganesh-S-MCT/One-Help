"""All the screens. Each page has retranslate() so the language button works everywhere."""
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QGuiApplication, QPixmap
from PyQt6.QtWidgets import (QButtonGroup, QDialog, QFileDialog, QFrame, QGridLayout,
                             QHBoxLayout, QLineEdit, QPlainTextEdit, QRadioButton,
                             QVBoxLayout, QWidget)

from .. import complaint as C
from .. import crop
from .. import labels as crop_labels
from .. import i18n
from ..i18n import pick, tr
from ..paths import resource
from . import theme
from .widgets import MenuCard, button, label, page_body, scrolling

IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.webp *.bmp)"


def _full_name(disease: dict) -> str:
    """'Tomato - Late blight' (the crop matters: potato and tomato both have late blight)."""
    cr = next((c for c in crop.crops() if c["id"] == disease["crop"]), None)
    return f"{pick(cr, 'name')} - {pick(disease, 'name')}" if cr else pick(disease, "name")


def _tile_icon(btn, name: str) -> None:
    """Dark icon; the selected tile sinks in and shows a red lamp edge."""
    btn.setIconSize(QSize(28, 28))
    btn.setIcon(theme.icon(name, theme.INK, 28))
    


# ---------------------------------------------------------------- Home
class HomePage(QWidget):
    open_report = pyqtSignal()
    open_crop = pyqtSignal()
    open_history = pyqtSignal()
    open_emergency = pyqtSignal()
    open_chat = pyqtSignal()

    def __init__(self):
        super().__init__()
        body, lay = page_body(14)
        banner = label(wrap=False)
        pm = QPixmap(str(resource("assets", "logo-wide-transparent.png")))
        banner.setPixmap(pm.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation))
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(banner)
        self.tagline = label("muted")
        self.tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tagline.setStyleSheet("font-size: 18px;")
        lay.addWidget(self.tagline)
        lay.addSpacing(6)
        self.c_chat = MenuCard("chat")
        self.c_report = MenuCard("camera")
        self.c_crop = MenuCard("leaf")
        self.c_hist = MenuCard("list")
        for c in (self.c_chat, self.c_report, self.c_crop, self.c_hist):
            lay.addWidget(c)
        self.c_chat.clicked.connect(self.open_chat)
        self.c_report.clicked.connect(self.open_report)
        self.c_crop.clicked.connect(self.open_crop)
        self.c_hist.clicked.connect(self.open_history)
        lay.addStretch(1)
        self.emergency = button()
        self.emergency.setObjectName("dark")
        self.emergency.setMinimumHeight(52)
        theme.shadow(self.emergency, "#2B2A2E", 90, 16, 0, 6)
        self.emergency.clicked.connect(self.open_emergency)
        lay.addWidget(self.emergency)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scrolling(body))
        self.retranslate()

    def retranslate(self):
        self.tagline.setText(tr("tagline"))
        self.c_chat.set_text(tr("home_chat"), tr("home_chat_sub"))
        self.c_report.set_text(tr("home_report"), tr("home_report_sub"))
        self.c_crop.set_text(tr("home_crop"), tr("home_crop_sub"))
        self.c_hist.set_text(tr("home_history"), tr("home_history_sub"))
        self.emergency.setText(tr("home_emergency") + "  –  112")


# ---------------------------------------------------------------- Report a problem
class ReportPage(QWidget):
    make_letter = pyqtSignal(object, str)  # Complaint, photo path

    def __init__(self):
        super().__init__()
        self.photo = ""
        self.auto_picked = False
        body, lay = page_body(8)

        self.h1 = label("h2")
        lay.addWidget(self.h1)
        grid = QGridLayout()
        grid.setSpacing(10)
        self.tiles = {}
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for n, it in enumerate(C.issues()):
            b = button(tile=True)
            _tile_icon(b, it["icon"])
            b.setProperty("issue", it["id"])
            self.group.addButton(b)
            self.tiles[it["id"]] = b
            grid.addWidget(b, n // 2, n % 2)
            b.clicked.connect(self._tile_clicked)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        lay.addLayout(grid)
        self.hint = label("hint")
        self.hint.hide()
        lay.addWidget(self.hint)

        self.h2 = label("h2")
        lay.addWidget(self.h2)
        row = QHBoxLayout()
        self.thumb = label(wrap=False)
        self.thumb.setFixedSize(96, 96)
        self.thumb.setObjectName("panel")
        self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb.setPixmap(theme.pixmap("camera", theme.GREY, 40))
        self.photo_btn = button()
        self.photo_btn.clicked.connect(self.choose_photo)
        self.photo_text = label("muted")
        col = QVBoxLayout()
        col.addWidget(self.photo_btn)
        col.addWidget(self.photo_text)
        row.addWidget(self.thumb)
        row.addLayout(col, 1)
        lay.addLayout(row)

        self.h3 = label("h2")
        lay.addWidget(self.h3)
        self.area_group = QButtonGroup(self)
        self.r_area = {}
        for key in ("chennai", "city", "village"):
            r = QRadioButton()
            self.area_group.addButton(r)
            self.r_area[key] = r
            r.toggled.connect(self._area_changed)
            lay.addWidget(r)
        self.l_town = label("muted")
        self.town = QLineEdit()
        self.l_addr = label("muted")
        self.addr = QLineEdit()
        self.l_land = label("muted")
        self.land = QLineEdit()
        for w in (self.l_town, self.town, self.l_addr, self.addr, self.l_land, self.land):
            lay.addWidget(w)

        self.h4 = label("h2")
        lay.addWidget(self.h4)
        self.l_name = label("muted")
        self.name = QLineEdit()
        self.l_phone = label("muted")
        self.phone = QLineEdit()
        self.l_extra = label("muted")
        self.extra = QPlainTextEdit()
        self.extra.setFixedHeight(90)
        self.extra.textChanged.connect(self._text_changed)
        for w in (self.l_name, self.name, self.l_phone, self.phone, self.l_extra, self.extra):
            lay.addWidget(w)

        self.error = label("error")
        self.error.hide()
        lay.addWidget(self.error)
        self.go = button(primary=True)
        self.go.clicked.connect(self._submit)
        lay.addSpacing(6)
        lay.addWidget(self.go)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scrolling(body))
        self.r_area["chennai"].setChecked(True)
        self._area_changed()
        self.retranslate()

    # -- helpers
    def preselect(self, issue_id: str):
        """Used by the helper chat: tick the problem it already worked out."""
        b = self.tiles.get(issue_id)
        if b:
            b.setChecked(True)
            self._tile_clicked()

    def area(self) -> str:
        return next(k for k, r in self.r_area.items() if r.isChecked())

    def issue_id(self):
        b = self.group.checkedButton()
        return b.property("issue") if b else None

    def _area_changed(self):
        show = self.area() != "chennai"
        self.l_town.setVisible(show)
        self.town.setVisible(show)

    def _tile_clicked(self):
        self.auto_picked = False
        self.hint.hide()
        self.error.hide()

    def _text_changed(self):
        # If the user has not chosen a problem yet, try to guess it from what they typed.
        if self.issue_id() and not self.auto_picked:
            return
        guess = C.suggest_issue(self.extra.toPlainText())
        if guess:
            self.group.setExclusive(True)
            self.tiles[guess].setChecked(True)
            self.auto_picked = True
            self.hint.setText(tr("hint_suggest", x=pick(C.issue_by_id(guess), "name")))
            self.hint.show()

    def choose_photo(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("photo_dialog"), str(Path.home()), IMAGE_FILTER)
        if path:
            self.set_photo(path)

    def set_photo(self, path: str):
        pm = QPixmap(path)
        if pm.isNull():
            return
        self.photo = path
        self.thumb.setPixmap(pm.scaled(92, 92, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation))
        self.retranslate()

    def _submit(self):
        err = None
        if not self.issue_id():
            err = "err_issue"
        elif self.area() != "chennai" and not self.town.text().strip():
            err = "err_town"
        elif not self.addr.text().strip():
            err = "err_address"
        elif not self.name.text().strip():
            err = "err_name"
        if err:
            self.error.setText(tr(err))
            self.error.show()
            return
        self.error.hide()
        c = C.Complaint(
            issue_id=self.issue_id(), area=self.area(), town=self.town.text(),
            address=self.addr.text(), landmark=self.land.text(), name=self.name.text(),
            phone=self.phone.text(), extra=self.extra.toPlainText(), has_photo=bool(self.photo),
        )
        self.make_letter.emit(c, self.photo)

    def reset(self):
        self.photo = ""
        self.thumb.setPixmap(theme.pixmap("camera", theme.GREY, 40))
        self.group.setExclusive(False)
        for b in self.tiles.values():
            b.setChecked(False)
        self.group.setExclusive(True)
        for w in (self.town, self.addr, self.land, self.extra):
            w.clear()
        self.hint.hide()
        self.error.hide()
        self.retranslate()

    def retranslate(self):
        for it in C.issues():
            self.tiles[it["id"]].setText("  " + pick(it, "name"))
        self.h1.setText(tr("step1"))
        self.h2.setText(tr("step2"))
        self.h3.setText(tr("step3"))
        self.h4.setText(tr("step4"))
        self.photo_btn.setText(tr("photo_change") if self.photo else tr("photo_choose"))
        self.photo_text.setText(Path(self.photo).name if self.photo else tr("photo_none"))
        for k, r in self.r_area.items():
            r.setText(tr("area_" + k))
        self.l_town.setText(tr("town_label"))
        self.l_addr.setText(tr("address_label"))
        self.l_land.setText(tr("landmark_label"))
        self.l_name.setText(tr("name_label"))
        self.l_phone.setText(tr("phone_label"))
        self.l_extra.setText(tr("extra_label"))
        self.go.setText(tr("make_letter"))
        if self.hint.isVisible() and self.issue_id():
            self.hint.setText(tr("hint_suggest", x=pick(C.issue_by_id(self.issue_id()), "name")))


# ---------------------------------------------------------------- Result (letter)
class ResultPage(QWidget):
    changed = pyqtSignal()  # history changed

    def __init__(self, store):
        super().__init__()
        self.store = store
        self.c = None
        self.cid = None
        self.issue_id = None
        self.area = "chennai"
        self.has_photo = False
        self.letter_lang = "ta"
        body, lay = page_body(10)

        self.h_to = label("h2")
        lay.addWidget(self.h_to)
        self.panel = QFrame()
        self.panel.setObjectName("panel")
        pl = QVBoxLayout(self.panel)
        self.office = label()
        self.office.setStyleSheet("font-size: 19px; font-weight: 700;")
        self.lines = label()
        pl.addWidget(self.office)
        pl.addWidget(self.lines)
        lay.addWidget(self.panel)

        self.h_lang = label("h2")
        lay.addWidget(self.h_lang)
        row = QHBoxLayout()
        self.r_ta = QRadioButton("தமிழ்")
        self.r_en = QRadioButton("English")
        self.lg = QButtonGroup(self)
        self.lg.addButton(self.r_ta)
        self.lg.addButton(self.r_en)
        self.r_ta.toggled.connect(self._lang_clicked)
        row.addWidget(self.r_ta)
        row.addWidget(self.r_en)
        row.addStretch(1)
        lay.addLayout(row)

        self.text = QPlainTextEdit()
        self.text.setMinimumHeight(360)
        lay.addWidget(self.text)
        self.note = label("muted")
        lay.addWidget(self.note)
        self.status = label("h2")
        self.status.setStyleSheet("color: %s; font-weight: 800;" % theme.GREY)
        lay.addWidget(self.status)

        self.b_copy = button(primary=True)
        self.b_save = button()
        self.b_sent = button()
        self.b_copy.clicked.connect(self.copy)
        self.b_save.clicked.connect(self.save_file)
        self.b_sent.clicked.connect(self.mark_sent)
        for b in (self.b_copy, self.b_save, self.b_sent):
            lay.addWidget(b)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scrolling(body))

    # new complaint from the form
    def show_complaint(self, c: "C.Complaint", lang: str):
        self.c = c
        self.issue_id, self.area, self.has_photo = c.issue_id, c.area, c.has_photo
        self.letter_lang = lang
        letter = C.build_letter(c, lang)
        area_text = c.address + (", " + c.town if c.town else "")
        self.cid = self.store.add(c.issue_id, c.area, area_text, lang, letter)
        self._fill(letter)
        self.changed.emit()

    # opened from history
    def show_saved(self, row: dict):
        self.c = None
        self.cid = row["id"]
        self.issue_id, self.area, self.has_photo = row["issue_id"], row["area"], False
        self.letter_lang = row["lang"]
        self._fill(row["letter"])

    def _fill(self, letter: str):
        self.r_ta.blockSignals(True)
        self.r_ta.setChecked(self.letter_lang == "ta")
        self.r_en.setChecked(self.letter_lang == "en")
        self.r_ta.blockSignals(False)
        self.r_ta.setEnabled(self.c is not None)
        self.r_en.setEnabled(self.c is not None)
        self.text.setPlainText(letter)
        self.status.setText("")
        self.retranslate()

    def _lang_clicked(self):
        if self.c is None:
            return
        self.letter_lang = "ta" if self.r_ta.isChecked() else "en"
        self.text.setPlainText(C.build_letter(self.c, self.letter_lang))
        self.store.update_letter(self.cid, self.letter_lang, self.text.toPlainText())

    def _persist_text(self):
        if self.cid is not None:
            self.store.update_letter(self.cid, self.letter_lang, self.text.toPlainText())

    def copy(self):
        QGuiApplication.clipboard().setText(self.text.toPlainText())
        self._persist_text()
        self.status.setText(tr("copied"))

    def save_file(self):
        default = str(Path.home() / f"complaint-{datetime.now():%Y%m%d-%H%M}.txt")
        path, _ = QFileDialog.getSaveFileName(self, tr("save_file"), default, "Text (*.txt)")
        if path:
            Path(path).write_text(self.text.toPlainText(), encoding="utf-8")
            self._persist_text()
            self.status.setText(tr("saved_to") + ": " + path)

    def mark_sent(self):
        if self.cid is not None:
            self._persist_text()
            self.store.set_status(self.cid, "sent")
            self.status.setText(tr("sent_done"))
            self.changed.emit()

    def retranslate(self):
        if not self.issue_id:
            return
        route = C.route(self.issue_id, self.area)
        self.h_to.setText(tr("send_to"))
        self.office.setText(route["short_" + i18n.lang()])
        lines = [f"{tr('helpline')}: {h['number']}  –  {pick(h, 'label')}" for h in route["helplines"]]
        self.lines.setText("\n".join(lines) if lines else tr("no_helpline"))
        self.h_lang.setText(tr("letter_lang"))
        self.note.setText(tr("photo_note") if self.has_photo else "")
        self.b_copy.setText(tr("copy"))
        self.b_save.setText(tr("save_file"))
        self.b_sent.setText(tr("mark_sent"))


# ---------------------------------------------------------------- History
class HistoryPage(QWidget):
    open_row = pyqtSignal(dict)

    def __init__(self, store):
        super().__init__()
        self.store = store
        self.body, self.lay = page_body(10)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scrolling(self.body))
        self.refresh()

    def refresh(self):
        while self.lay.count():
            it = self.lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        rows = self.store.all()
        if not rows:
            e = label("muted")
            e.setText(tr("history_empty"))
            e.setAlignment(Qt.AlignmentFlag.AlignCenter)
            e.setStyleSheet("font-size: 19px; margin-top: 40px;")
            self.lay.addWidget(e)
        for r in rows:
            self.lay.addWidget(self._row(r))
        self.lay.addStretch(1)

    def _row(self, r: dict) -> QFrame:
        f = QFrame()
        f.setObjectName("panel")
        v = QVBoxLayout(f)
        issue = C.issue_by_id(r["issue_id"])
        when = datetime.fromisoformat(r["created"]).strftime("%d/%m/%Y")
        t = label()
        t.setText(f"<b>{pick(issue, 'name')}</b> &nbsp;•&nbsp; {when}")
        s = label("muted")
        status = tr("status_sent") if r["status"] == "sent" else tr("status_draft")
        s.setText(f"{r['area_text']}  –  {status}")
        v.addWidget(t)
        v.addWidget(s)
        h = QHBoxLayout()
        b1, b2 = button(), button()
        b1.setText(tr("view"))
        b2.setText(tr("delete"))
        b1.clicked.connect(lambda _=False, row=r: self.open_row.emit(row))
        b2.clicked.connect(lambda _=False, cid=r["id"]: (self.store.delete(cid), self.refresh()))
        h.addWidget(b1)
        h.addWidget(b2)
        v.addLayout(h)
        return f

    def retranslate(self):
        self.refresh()


# ---------------------------------------------------------------- Crop
class DiseaseDialog(QDialog):
    def __init__(self, disease: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_full_name(disease))
        self.resize(520, 640)
        body, lay = page_body(6)
        t = label("h1")
        t.setText(_full_name(disease))
        lay.addWidget(t)
        for head, key in (("symptoms", "symptoms"), ("what_to_do", "action"), ("prevention", "prevent")):
            h = label("h2")
            h.setText(tr(head))
            lay.addWidget(h)
            val = disease[f"{key}_{i18n.lang()}"]
            lb = label()
            lb.setText(val if isinstance(val, str) else "\n".join("•  " + x for x in val))
            lay.addWidget(lb)
        note = label("hint")
        note.setText(tr("officer_note"))
        lay.addSpacing(10)
        lay.addWidget(note)
        lay.addStretch(1)
        close = button(primary=True)
        close.setText(tr("close"))
        close.clicked.connect(self.accept)
        lay.addWidget(close)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scrolling(body))


class CropPage(QWidget):
    def __init__(self, predictor=None):
        super().__init__()
        self.predictor = predictor
        self.photo = ""
        self.crop_id = None
        body, lay = page_body(8)

        self.h0 = label("h2")
        lay.addWidget(self.h0)
        self.photo_note = label("hint")
        lay.addWidget(self.photo_note)
        self.pick_photo = button()
        self.pick_photo.clicked.connect(self._choose)
        self.run = button(primary=True)
        self.run.clicked.connect(self._run)
        self.preview = label(wrap=False)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.hide()
        self.ai_out = label()
        self.ai_out.setStyleSheet("font-size: 19px; font-weight: 700;")
        for w in (self.pick_photo, self.preview, self.run, self.ai_out):
            lay.addWidget(w)
        has_model = predictor is not None
        self.photo_note.setVisible(not has_model)
        self.pick_photo.setVisible(has_model)
        self.run.setVisible(has_model)

        self.h1 = label("h2")
        lay.addWidget(self.h1)
        grid = QGridLayout()
        grid.setSpacing(10)
        self.group = QButtonGroup(self)
        self.tiles = {}
        for n, cr in enumerate(crop.crops()):
            b = button(tile=True)
            _tile_icon(b, "leaf")
            b.setProperty("crop", cr["id"])
            b.clicked.connect(self._crop_clicked)
            self.group.addButton(b)
            self.tiles[cr["id"]] = b
            grid.addWidget(b, n // 2, n % 2)
        lay.addLayout(grid)

        self.h2 = label("h2")
        lay.addWidget(self.h2)
        self.list_lay = QVBoxLayout()
        self.list_lay.setSpacing(10)
        lay.addLayout(self.list_lay)
        lay.addStretch(1)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scrolling(body))
        self.retranslate()

    def _choose(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("photo_dialog"), str(Path.home()), IMAGE_FILTER)
        if path:
            pm = QPixmap(path)
            if pm.isNull():
                return
            self.photo = path
            self.preview.setPixmap(pm.scaled(260, 260, Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation))
            self.preview.show()
            self.ai_out.setText("")

    def _run(self):
        if not (self.predictor and self.photo):
            return
        try:
            raw, p = self.predictor.predict(self.photo)[0]
        except Exception:
            self.ai_out.setText(tr("ai_not_sure"))
            return
        pct = round(p * 100)
        reading = crop_labels.interpret(raw)
        d = crop.disease(reading.disease_id) if reading.disease_id else None
        if p < 0.6:
            self.ai_out.setText(tr("ai_not_sure"))
        elif reading.kind == "healthy":
            self.ai_out.setText(tr("ai_healthy") + f" ({pct}%)")
        elif d is not None:
            self.ai_out.setText(tr("ai_result", x=_full_name(d), p=pct) + "\n" + tr("ai_disclaimer"))
            DiseaseDialog(d, self).exec()
        else:
            self.ai_out.setText(tr("ai_other", x=reading.pretty, p=pct))

    def _crop_clicked(self):
        self.crop_id = self.group.checkedButton().property("crop")
        self._fill_list()

    def _fill_list(self):
        while self.list_lay.count():
            it = self.list_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        if not self.crop_id:
            return
        for d in crop.diseases_for(self.crop_id):
            card = MenuCard("leaf")
            card.set_text(pick(d, "name"), pick(d, "symptoms"))
            card.setMinimumHeight(110)
            card.clicked.connect(lambda _=False, dd=d: DiseaseDialog(dd, self).exec())
            self.list_lay.addWidget(card)

    def retranslate(self):
        self.h0.setText(tr("crop_photo_title"))
        self.photo_note.setText(tr("crop_ai_unavailable"))
        self.pick_photo.setText(tr("photo_choose"))
        self.run.setText(tr("crop_check"))
        self.h1.setText(tr("crop_step1"))
        self.h2.setText(tr("crop_step2"))
        for cr in crop.crops():
            self.tiles[cr["id"]].setText("  " + pick(cr, "name"))
        self._fill_list()


# ---------------------------------------------------------------- Emergency
class EmergencyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("emergency_title"))
        self.resize(480, 560)
        body, lay = page_body(8)
        t = label("h1")
        t.setText(tr("emergency_title"))
        lay.addWidget(t)
        for e in C.departments()["emergency"]:
            f = QFrame()
            f.setObjectName("card")
            theme.shadow(f, blur=14, dx=4, dy=4)
            h = QHBoxLayout(f)
            name = label()
            name.setText(e[i18n.lang()])
            name.setStyleSheet("font-weight: 800;")
            lcd = QFrame()
            lcd.setObjectName("lcd")
            ll = QHBoxLayout(lcd)
            ll.setContentsMargins(14, 4, 14, 4)
            num = label(wrap=False)
            num.setText(e["number"])
            num.setStyleSheet("font-size: 22px; font-weight: 700; font-family: 'DM Mono','DejaVu Sans Mono',monospace;")
            ll.addWidget(num)
            h.addWidget(name, 1)
            h.addWidget(lcd)
            lay.addWidget(f)
        lay.addStretch(1)
        close = button(primary=True)
        close.setText(tr("close"))
        close.clicked.connect(self.accept)
        lay.addWidget(close)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scrolling(body))
