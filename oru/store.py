"""Saves the user's complaints on their own computer (SQLite, no internet needed)."""
import sqlite3
from datetime import datetime
from pathlib import Path

from .paths import data_dir


class Store:
    def __init__(self, path: Path = None):
        self.path = Path(path) if path else data_dir() / "complaints.db"
        with self._db() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS complaints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created TEXT NOT NULL,
                    issue_id TEXT NOT NULL,
                    area TEXT NOT NULL DEFAULT 'chennai',
                    area_text TEXT NOT NULL,
                    lang TEXT NOT NULL,
                    letter TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft'
                )"""
            )

    def _db(self):
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        return con

    def add(self, issue_id: str, area: str, area_text: str, lang: str, letter: str) -> int:
        with self._db() as db:
            cur = db.execute(
                "INSERT INTO complaints (created, issue_id, area, area_text, lang, letter) VALUES (?,?,?,?,?,?)",
                (datetime.now().isoformat(timespec="seconds"), issue_id, area, area_text, lang, letter),
            )
            return cur.lastrowid

    def update_letter(self, cid: int, lang: str, letter: str) -> None:
        with self._db() as db:
            db.execute("UPDATE complaints SET lang=?, letter=? WHERE id=?", (lang, letter, cid))

    def set_status(self, cid: int, status: str) -> None:
        with self._db() as db:
            db.execute("UPDATE complaints SET status=? WHERE id=?", (status, cid))

    def delete(self, cid: int) -> None:
        with self._db() as db:
            db.execute("DELETE FROM complaints WHERE id=?", (cid,))

    def all(self) -> list:
        with self._db() as db:
            return [dict(r) for r in db.execute("SELECT * FROM complaints ORDER BY id DESC")]

    def get(self, cid: int):
        with self._db() as db:
            r = db.execute("SELECT * FROM complaints WHERE id=?", (cid,)).fetchone()
            return dict(r) if r else None
