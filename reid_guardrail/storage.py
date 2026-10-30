import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def run_lock(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    handle = (directory / ".run.lock").open("a+b")
    handle.seek(0)
    if handle.read(1) == b"":
        handle.write(b"0")
        handle.flush()
    handle.seek(0)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        raise ValueError("Bu çıktı klasöründe başka bir işlem çalışıyor.") from None
    try:
        yield
    finally:
        handle.close()  # OS releases lock even after process termination.


class Ledger:
    """SQLite is canonical; JSONL is an immediately flushed review projection."""
    def __init__(self, directory):
        self.directory = Path(directory)
        self.db = sqlite3.connect(self.directory / "state.sqlite3")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("CREATE TABLE IF NOT EXISTS outcomes (job_id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS history (sequence INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
        # Preserve pre-history ledgers from earlier local versions.
        if self.db.execute("SELECT COUNT(*) FROM history").fetchone()[0] == 0:
            self.db.execute("INSERT INTO history(payload) SELECT payload FROM outcomes ORDER BY rowid")
        self.db.commit()

    def bind(self, signature):
        previous = self.db.execute("SELECT value FROM metadata WHERE key='signature'").fetchone()
        if previous and previous[0] != signature:
            raise ValueError("Bu klasör başka girdi/ayar/mod içeriyor. Yeni --out klasörü kullan.")
        self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('signature', ?)", (signature,))
        self.db.commit()

    def outcomes(self):
        return [json.loads(row[0]) for row in self.db.execute("SELECT payload FROM outcomes ORDER BY rowid")]

    def put(self, outcome):
        self.db.execute("INSERT INTO history(payload) VALUES (?)", (json.dumps(outcome, ensure_ascii=False),))
        self.db.execute("INSERT OR REPLACE INTO outcomes VALUES (?, ?)",
                        (outcome["job_id"], json.dumps(outcome, ensure_ascii=False)))
        self.db.commit()
        if outcome["status"] == "success":
            with (self.directory / "candidates.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(outcome["record"], ensure_ascii=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())

    def project(self):
        outcomes = self.outcomes()
        history = self.history()
        for filename, rows in [
            ("candidates.jsonl", [o["record"] for o in outcomes if o["status"] == "success"]),
            ("events.jsonl", [{k: v for k, v in o.items() if k != "record"} for o in history]),
            ("errors.jsonl", [o for o in history if o["status"] not in {"success", "duplicate"}]),
        ]:
            target = self.directory / filename
            temp = target.with_suffix(".tmp")
            with temp.open("w", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            temp.replace(target)

    def history(self):
        return [json.loads(row[0]) for row in self.db.execute("SELECT payload FROM history ORDER BY sequence")]

    def close(self):
        self.db.close()
