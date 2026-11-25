"""Where files live: bundled resources and the user's data folder."""
import os
import sys
from pathlib import Path


def resource(*parts: str) -> Path:
    """Path to a bundled file (works from source and from a PyInstaller build)."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base.joinpath(*parts)


def data_dir() -> Path:
    """User data folder, e.g. ~/.local/share/oru-udhavi"""
    root = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    p = Path(root) / "oru-udhavi"
    p.mkdir(parents=True, exist_ok=True)
    return p
