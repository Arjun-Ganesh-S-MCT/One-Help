"""Small splash window that plays the intro video at its own size (not full screen)."""
from PyQt6.QtCore import QTimer, QUrl, Qt, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from ..paths import resource

VIDEO_SIZE = 768        # the splash video is 768 x 768
MAX_WAIT_MS = 9000      # never keep the user waiting if the video cannot play


class Splash(QWidget):
    finished = pyqtSignal()

    def __init__(self, volume: float = 0.5):
        super().__init__()
        self._done = False
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint
                            | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background: #EFE9E0;")
        screen = QGuiApplication.primaryScreen().availableGeometry()
        side = min(VIDEO_SIZE, int(screen.height() * 0.9), int(screen.width() * 0.9))
        self.setFixedSize(side, side)
        self.move(screen.center().x() - side // 2, screen.center().y() - side // 2)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.video = QVideoWidget()
        lay.addWidget(self.video)

        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(volume)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        self.player.setSource(QUrl.fromLocalFile(str(resource("assets", "splash.mp4"))))
        self.player.mediaStatusChanged.connect(self._status)
        self.player.errorOccurred.connect(lambda *_: self._finish())

        QTimer.singleShot(MAX_WAIT_MS, self._finish)

    def start(self):
        self.show()
        self.player.play()

    def _status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._finish()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self._finish()

    def mousePressEvent(self, e):      # click to skip
        self._finish()

    def _finish(self):
        if self._done:
            return
        self._done = True
        self.player.stop()
        self.close()
        self.finished.emit()
