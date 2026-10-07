"""Thread-safe local persistence. No remote database or telemetry."""
import json
import secrets
import sqlite3
import threading
import time
from pathlib import Path

class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, data TEXT NOT NULL, updated REAL NOT NULL)')
        self.db.execute('CREATE INDEX IF NOT EXISTS records_kind ON records(kind)')
        self.db.commit()

    def put(self, kind, data, ident=None):
        with self.lock:
            ident = ident or secrets.token_hex(12)
            old = self.db.execute('SELECT kind FROM records WHERE id=?', (ident,)).fetchone()
            if old and old[0] != kind:
                raise ValueError('Record type mismatch')
            data = dict(data, id=ident)
            self.db.execute('INSERT OR REPLACE INTO records VALUES (?,?,?,?)',
                            (ident, kind, json.dumps(data, ensure_ascii=False), time.time()))
            self.db.commit()
            return data

    def get(self, kind, ident):
        with self.lock:
            row = self.db.execute('SELECT data FROM records WHERE kind=? AND id=?', (kind, ident)).fetchone()
            if row is None:
                raise ValueError('Record not found')
            return json.loads(row[0])

    def list(self, kind):
        with self.lock:
            return [json.loads(r[0]) for r in self.db.execute('SELECT data FROM records WHERE kind=? ORDER BY updated DESC', (kind,))]

    def delete(self, kind, ident):
        with self.lock:
            cur = self.db.execute('DELETE FROM records WHERE kind=? AND id=?', (kind, ident))
            self.db.commit()
            if not cur.rowcount:
                raise ValueError('Record not found')

    def backup(self, target):
        with self.lock:
            dest = sqlite3.connect(target)
            try:
                self.db.backup(dest)
            finally:
                dest.close()

    def close(self):
        with self.lock:
            self.db.close()
