import os
import sys
import types

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
import pytest

from oru import voice


def test_clean_for_speech():
    assert voice.clean_for_speech("**Call** 1913\n• now_ #") == "Call 1913 now"


def _fake_sr(monkeypatch, result=None, exc=None):
    seen = {}
    m = types.ModuleType("speech_recognition")

    class UnknownValueError(Exception): ...
    class RequestError(Exception): ...

    class AudioData:
        def __init__(self, pcm, rate, width):
            seen.update(pcm=pcm, rate=rate, width=width)

    class Recognizer:
        def recognize_google(self, audio, language):
            seen["language"] = language
            if exc == "unknown":
                raise UnknownValueError()
            if exc == "net":
                raise RequestError()
            return result

    m.UnknownValueError, m.RequestError, m.AudioData, m.Recognizer = UnknownValueError, RequestError, AudioData, Recognizer
    monkeypatch.setitem(sys.modules, "speech_recognition", m)
    return seen


def test_recognise_ok_and_stereo_downmix(monkeypatch):
    seen = _fake_sr(monkeypatch, result="வணக்கம்")
    stereo = np.array([[1, 9], [2, 9], [3, 9]], dtype="<i2").tobytes()
    assert voice._recognise(stereo, 16000, 2, "ta") == "வணக்கம்"
    assert seen["language"] == "ta-IN" and seen["width"] == 2
    assert np.frombuffer(seen["pcm"], dtype="<i2").tolist() == [1, 2, 3]


def test_recognise_errors(monkeypatch):
    _fake_sr(monkeypatch, exc="unknown")
    with pytest.raises(voice.NotUnderstood) as e:
        voice._recognise(b"\0\0" * 10, 16000, 1, "en")
    assert e.value.code == "not_understood"
    _fake_sr(monkeypatch, exc="net")
    with pytest.raises(Exception) as e:
        voice._recognise(b"\0\0" * 10, 16000, 1, "en")
    assert e.value.code == "offline"


def test_write_wav(tmp_path):
    import wave
    p = tmp_path / "a.wav"
    voice.write_wav(str(p), b"\0\0" * 160)
    with wave.open(str(p)) as w:
        assert w.getframerate() == 16000 and w.getnframes() == 160
