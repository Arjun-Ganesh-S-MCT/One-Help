"""Listening and speaking.

Speaking: Google text-to-speech (gTTS, online, has a Tamil voice) -> mp3 -> played by Qt.
Listening: the microphone is recorded with Qt, then Google's free speech recognition turns it into text
(it needs the `flac` program installed: sudo pacman -S flac).
Both need internet. If something is missing the chat still works by typing."""
import os
import tempfile
import wave

from PyQt6.QtCore import QBuffer, QIODevice, QObject, QThread, QUrl, pyqtSignal
from PyQt6.QtMultimedia import (QAudioFormat, QAudioOutput, QAudioSource, QMediaDevices,
                                QMediaPlayer)

RATE = 16000
LANG_CODE = {"ta": "ta", "en": "en"}                 # gTTS
STT_CODE = {"ta": "ta-IN", "en": "en-IN"}            # speech recognition


def clean_for_speech(text: str) -> str:
    """Remove symbols that a voice would read out loud."""
    for ch in "*#_`•>|":
        text = text.replace(ch, " ")
    return " ".join(text.split())


class Job(QThread):
    done = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self._fn = fn

    def run(self):
        try:
            self.done.emit(self._fn())
        except Exception as e:           # shown as a short code, never a stack trace
            self.failed.emit(getattr(e, "code", None) or type(e).__name__)


class Speaker(QObject):
    """speak(text, lang) -> plays it. stop() stops. `error` carries a short code."""
    started = pyqtSignal()
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer(self)
        self._out = QAudioOutput(self)
        self._out.setVolume(1.0)
        self._player.setAudioOutput(self._out)
        self._player.mediaStatusChanged.connect(self._status)
        self._player.errorOccurred.connect(lambda *_: self.error.emit("playback"))
        self._job = None
        self._tmp = None
        self._token = 0

    def available(self) -> bool:
        try:
            import gtts  # noqa: F401
        except ImportError:
            return False
        return len(QMediaDevices.audioOutputs()) > 0

    def speak(self, text: str, lang: str):
        self.stop()
        text = clean_for_speech(text)
        if not text:
            return
        self._token += 1
        token = self._token

        def make():
            from gtts import gTTS
            fd, path = tempfile.mkstemp(suffix=".mp3", prefix="oru-")
            os.close(fd)
            gTTS(text=text, lang=LANG_CODE.get(lang, "en")).save(path)
            return path

        job = Job(make, self)
        job.done.connect(lambda p, t=token: self._play(p, t))
        job.failed.connect(lambda c, t=token: self.error.emit("tts_" + c) if t == self._token else None)
        self._job = job
        job.start()

    def _play(self, path: str, token: int):
        if token != self._token:           # the user already stopped or asked something else
            _rm(path)
            return
        self._tmp = path
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.play()
        self.started.emit()

    def _status(self, st):
        if st == QMediaPlayer.MediaStatus.EndOfMedia:
            self._cleanup()
            self.finished.emit()

    def stop(self):
        self._token += 1
        self._player.stop()
        self._cleanup()

    def _cleanup(self):
        if self._tmp:
            self._player.setSource(QUrl())
            _rm(self._tmp)
            self._tmp = None


def _rm(path):
    try:
        os.remove(path)
    except OSError:
        pass


class Listener(QObject):
    """start() records, stop() ends and recognises. Emits `heard(text)` or `error(code)`."""
    heard = pyqtSignal(str)
    error = pyqtSignal(str)
    busy = pyqtSignal(bool)       # True while recording or recognising

    def __init__(self, parent=None):
        super().__init__(parent)
        self._src = None
        self._buf = None
        self._job = None
        self._lang = "ta"

    def available(self) -> bool:
        try:
            import speech_recognition  # noqa: F401
        except ImportError:
            return False
        return len(QMediaDevices.audioInputs()) > 0

    @property
    def recording(self) -> bool:
        return self._src is not None

    def start(self, lang: str):
        if self._src is not None:
            return
        dev = QMediaDevices.defaultAudioInput()
        if dev.isNull():
            self.error.emit("no_mic")
            return
        fmt = QAudioFormat()
        fmt.setSampleRate(RATE)
        fmt.setChannelCount(1)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        if not dev.isFormatSupported(fmt):
            fmt = dev.preferredFormat()
            if fmt.sampleFormat() != QAudioFormat.SampleFormat.Int16:
                self.error.emit("mic_format")
                return
        self._fmt = fmt
        self._lang = lang
        self._buf = QBuffer(self)
        self._buf.open(QIODevice.OpenModeFlag.ReadWrite)
        self._src = QAudioSource(dev, fmt, self)
        self._src.start(self._buf)
        self.busy.emit(True)

    def cancel(self):
        self._release()
        self.busy.emit(False)

    def stop(self):
        if self._src is None:
            return
        data = bytes(self._buf.data())
        fmt = self._fmt
        self._release()
        rate, ch = fmt.sampleRate(), fmt.channelCount()
        if len(data) < rate * ch * 2 * 0.4:         # under 0.4 s: nothing was said
            self.busy.emit(False)
            self.error.emit("too_short")
            return
        lang = self._lang
        job = Job(lambda: _recognise(data, rate, ch, lang), self)
        job.done.connect(self._ok)
        job.failed.connect(lambda c: (self.busy.emit(False), self.error.emit(c)))
        self._job = job
        job.start()

    def _ok(self, text):
        self.busy.emit(False)
        self.heard.emit(text)

    def _release(self):
        if self._src is not None:
            self._src.stop()
            self._src = None
        if self._buf is not None:
            self._buf.close()
            self._buf = None


class NotUnderstood(Exception):
    code = "not_understood"


def _recognise(pcm: bytes, rate: int, channels: int, lang: str) -> str:
    import speech_recognition as sr
    if channels > 1:                            # keep only the first channel
        import numpy as np
        pcm = np.frombuffer(pcm, dtype="<i2").reshape(-1, channels)[:, 0].tobytes()
    audio = sr.AudioData(pcm, rate, 2)
    r = sr.Recognizer()
    try:
        return r.recognize_google(audio, language=STT_CODE.get(lang, "en-IN"))
    except sr.UnknownValueError:
        raise NotUnderstood()
    except sr.RequestError:
        e = Exception()
        e.code = "offline"
        raise e


def write_wav(path: str, pcm: bytes, rate: int = RATE, channels: int = 1):
    with wave.open(path, "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
