#!/usr/bin/env python3
"""Test the crop photo-check model without opening the app.

  python tools/test_model.py leaf1.jpg leaf2.jpg          # top-3 guesses for your own photos
  python tools/test_model.py --folder path/to/valid       # accuracy on labelled photos
  python tools/test_model.py --folder path/to/valid --limit 50 --only tomato,potato

--folder expects one sub-folder per class, named like the model's classes
(e.g. Tomato___Late_blight/), which is how the Kaggle "New Plant Diseases Dataset" (valid/ folder) is laid out.
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from oru import crop, labels  # noqa: E402

IMG = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def show_photos(pred, files):
    for f in files:
        top = pred.predict(str(f), top=3)
        print(f"\n{f}")
        for raw, p in top:
            r = labels.interpret(raw)
            d = crop.disease(r.disease_id) if r.disease_id else None
            note = {"disease": f"-> app shows remedy: {d['name_en']}" if d else "-> disease",
                    "healthy": "-> app says healthy", "other": "-> crop/disease not in library"}[r.kind]
            print(f"  {p*100:5.1f}%  {raw:55s} {note}")
        print("  App would say:", "Not sure (below 60%)" if top[0][1] < 0.6 else "a result")


def accuracy(pred, folder: Path, limit: int, only):
    per = defaultdict(lambda: [0, 0])
    wrong = defaultdict(int)
    for cls_dir in sorted(p for p in folder.iterdir() if p.is_dir()):
        if only and not any(o in cls_dir.name.lower() for o in only):
            continue
        files = [f for f in sorted(cls_dir.iterdir()) if f.suffix.lower() in IMG][:limit]
        for f in files:
            guess = pred.predict(str(f), top=1)[0][0]
            per[cls_dir.name][1] += 1
            if guess == cls_dir.name:
                per[cls_dir.name][0] += 1
            else:
                wrong[(cls_dir.name, guess)] += 1
        if per[cls_dir.name][1]:
            ok, n = per[cls_dir.name]
            print(f"{ok / n * 100:5.1f}%  ({ok}/{n})  {cls_dir.name}")
    ok = sum(v[0] for v in per.values())
    n = sum(v[1] for v in per.values())
    if not n:
        print("No images found. Check the folder layout (one sub-folder per class).")
        return
    print(f"\nOverall top-1 accuracy: {ok / n * 100:.1f}%  ({ok}/{n} photos, {len(per)} classes)")
    if wrong:
        print("\nMost common mistakes (true -> guessed):")
        for (t, g), c in sorted(wrong.items(), key=lambda kv: -kv[1])[:8]:
            print(f"  {c:3d}x  {t}  ->  {g}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photos", nargs="*", help="leaf photos to test")
    ap.add_argument("--folder", help="folder with one sub-folder per class")
    ap.add_argument("--limit", type=int, default=30, help="photos per class (default 30)")
    ap.add_argument("--only", default="", help="comma list, e.g. tomato,potato")
    ap.add_argument("--models", default=str(ROOT / "models"))
    a = ap.parse_args()

    pred = crop.CropPredictor.load(Path(a.models))
    if pred is None:
        sys.exit("No model found in %s. Run: python tools/get_model.py" % a.models)
    print(f"Model loaded: {len(pred.labels)} classes\n")
    if a.photos:
        show_photos(pred, [Path(p) for p in a.photos])
    if a.folder:
        accuracy(pred, Path(a.folder), a.limit, [o.strip().lower() for o in a.only.split(",") if o.strip()])
    if not a.photos and not a.folder:
        ap.print_help()


if __name__ == "__main__":
    main()
