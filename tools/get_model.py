#!/usr/bin/env python3
"""Download a ready-made plant-disease model from Hugging Face and convert it for the app.

    pip install torch transformers onnx onnxscript
    python tools/get_model.py                      # downloads the default model
    python tools/get_model.py --source ./my_model  # or use a model folder you already have

It writes models/crop_model.onnx and models/crop_labels.json (class names + the image
settings the model was trained with). Restart the app and "Check my crop" shows the photo check.

Default model: linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification
(MobileNetV2, 38 PlantVillage classes, ~95% accuracy reported by its author; check its licence
before you publish the app).
"""
import argparse
import json
from pathlib import Path

DEFAULT = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
ROOT = Path(__file__).resolve().parent.parent


def _px(value, default):
    """Old configs store a plain number (256), new ones a dict ({"shortest_edge": 256})."""
    if value is None:
        return default
    if isinstance(value, dict):
        return int(value.get("shortest_edge") or value.get("height") or default)
    return int(value)


def load_preprocessing(source: str):
    """Read preprocessor_config.json directly (the model's config is old-style, and new
    versions of transformers cannot pick the image processor class from it)."""
    local = Path(source) / "preprocessor_config.json"
    if local.is_file():
        path = local
    else:
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(source, "preprocessor_config.json")
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    size = _px(cfg.get("crop_size"), 224)
    if cfg.get("do_center_crop", True):
        resize = _px(cfg.get("size"), 256)      # shorter side is resized to this, then centre-cropped
    else:
        size, resize = _px(cfg.get("size"), size), None
    mean = [float(x) for x in cfg.get("image_mean", [0.5, 0.5, 0.5])]
    std = [float(x) for x in cfg.get("image_std", [0.5, 0.5, 0.5])]
    return size, (resize if resize and resize != size else None), mean, std


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=DEFAULT, help="Hugging Face model id or a local model folder")
    ap.add_argument("--out", default=str(ROOT / "models"), help="where to write the two files")
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForImageClassification

    print("Loading", args.source)
    size, resize, mean, std = load_preprocessing(args.source)
    model = AutoModelForImageClassification.from_pretrained(args.source).eval()
    n = model.config.num_labels
    labels = [model.config.id2label[i] for i in range(n)]

    class Logits(torch.nn.Module):
        def __init__(self, m):
            super().__init__()
            self.m = m

        def forward(self, x):
            return self.m(pixel_values=x).logits

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dummy = torch.zeros(1, 3, size, size)
    torch.onnx.export(
        Logits(model), dummy, str(out / "crop_model.onnx"),
        input_names=["pixel_values"], output_names=["logits"],
        dynamic_axes={"pixel_values": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17, dynamo=False,
    )
    (out / "crop_labels.json").write_text(
        json.dumps({"labels": labels, "mean": mean, "std": std, "size": size, "resize": resize}, indent=2),
        encoding="utf-8",
    )
    print(f"Done: {n} classes, input {size}x{size}, mean={mean}, std={std}, resize={resize}")
    print("Wrote", out / "crop_model.onnx", "and", out / "crop_labels.json")


if __name__ == "__main__":
    main()
