"""Turns the model's raw class names (PlantVillage style, e.g. 'Tomato___Late_blight')
into something the app understands.

Result kinds:
  disease  -> a disease that is in our remedy library (disease_id is set)
  healthy  -> the model thinks the leaf is healthy
  other    -> a crop/disease the model knows but our library does not have yet
"""
import re
from dataclasses import dataclass


@dataclass
class Reading:
    kind: str                 # disease | healthy | other
    crop: str = ""            # e.g. "tomato"
    disease_id: str = ""      # id from remedies.json (kind == disease)
    pretty: str = ""          # readable English name, e.g. "Tomato - Late blight"


# (crop, words that must all appear in the normalised label) -> remedy id
RULES = [
    ("tomato", ("early", "blight"), "tomato_early_blight"),
    ("tomato", ("late", "blight"), "tomato_late_blight"),
    ("tomato", ("yellow", "leaf", "curl"), "tomato_leaf_curl"),
    ("tomato", ("bacterial", "spot"), "tomato_bacterial_spot"),
    ("tomato", ("leaf", "mold"), "tomato_leaf_mold"),
    ("tomato", ("septoria",), "tomato_septoria_leaf_spot"),
    ("tomato", ("spider", "mite"), "tomato_spider_mites"),
    ("tomato", ("target", "spot"), "tomato_target_spot"),
    ("tomato", ("mosaic",), "tomato_mosaic_virus"),
    ("potato", ("early", "blight"), "potato_early_blight"),
    ("potato", ("late", "blight"), "potato_late_blight"),
]


def _norm(raw: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", raw.lower()).strip()


def pretty(raw: str) -> str:
    parts = [p for p in re.split(r"_{2,}|___", raw) if p]
    parts = [re.sub(r"_+", " ", p).replace("(", "").replace(")", "").strip() for p in parts]
    return " - ".join(p[:1].upper() + p[1:] for p in parts)


def interpret(raw: str) -> Reading:
    n = _norm(raw)
    words = set(n.split())
    crop = "tomato" if "tomato" in words else "potato" if "potato" in words else ""
    name = pretty(raw)
    if "healthy" in words:
        return Reading("healthy", crop, "", name)
    for rc, must, did in RULES:
        if rc == crop and all(any(w.startswith(m) for w in words) for m in must):
            return Reading("disease", crop, did, name)
    return Reading("other", crop, "", name)
