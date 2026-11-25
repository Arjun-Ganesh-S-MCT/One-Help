"""Crop disease library + optional photo check.

The library (remedies.json) always works. The photo check needs an ONNX model
file in models/ (see models/README.md); without it the app says it is not available yet."""
import json
from pathlib import Path

from .paths import resource

_data = None


def _load() -> dict:
    global _data
    if _data is None:
        _data = json.loads(resource("oru", "data", "remedies.json").read_text("utf-8"))
    return _data


def crops() -> list:
    return _load()["crops"]


def diseases_for(crop_id: str) -> list:
    return [d for d in _load()["diseases"] if d["crop"] == crop_id]


def disease(disease_id: str):
    return next((d for d in _load()["diseases"] if d["id"] == disease_id), None)


class CropPredictor:
    """Runs models/crop_model.onnx on a leaf photo.

    models/crop_labels.json looks like (written by tools/get_model.py):
      {"labels": ["Tomato___Early_blight", ...], "mean": [..], "std": [..], "size": 224, "resize": 256}
    Only "labels" is required; the rest default to ImageNet values and a plain 224 x 224 resize.
    """

    def __init__(self, session, labels, mean=None, std=None, size=224, resize=None):
        self.session = session
        self.labels = labels
        self.mean = mean or [0.485, 0.456, 0.406]
        self.std = std or [0.229, 0.224, 0.225]
        self.size = int(size)
        self.resize = int(resize) if resize else None
        self.input_name = session.get_inputs()[0].name

    @classmethod
    def load(cls, model_dir: Path = None):
        model_dir = Path(model_dir) if model_dir else resource("models")
        model, labels = model_dir / "crop_model.onnx", model_dir / "crop_labels.json"
        if not (model.exists() and labels.exists()):
            return None
        try:
            import onnxruntime as ort
            session = ort.InferenceSession(str(model), providers=["CPUExecutionProvider"])
            cfg = json.loads(labels.read_text("utf-8"))
            return cls(session, cfg["labels"], cfg.get("mean"), cfg.get("std"), cfg.get("size", 224), cfg.get("resize"))
        except Exception:
            return None

    def _prepare(self, image_path: str):
        import numpy as np
        from PIL import Image

        img = Image.open(image_path).convert("RGB")
        if self.resize and self.resize != self.size:
            w, h = img.size
            scale = self.resize / min(w, h)
            img = img.resize((max(self.size, round(w * scale)), max(self.size, round(h * scale))))
            w, h = img.size
            left, top = (w - self.size) // 2, (h - self.size) // 2
            img = img.crop((left, top, left + self.size, top + self.size))
        else:
            img = img.resize((self.size, self.size))
        x = np.asarray(img, dtype=np.float32) / 255.0
        x = (x - np.array(self.mean, dtype=np.float32)) / np.array(self.std, dtype=np.float32)
        return x.transpose(2, 0, 1)[None].astype(np.float32)

    def predict(self, image_path: str, top: int = 3):
        import numpy as np

        out = self.session.run(None, {self.input_name: self._prepare(image_path)})[0][0]
        e = np.exp(out - out.max())
        p = e / e.sum()
        idx = np.argsort(-p)[:top]
        return [(self.labels[i], float(p[i])) for i in idx]
