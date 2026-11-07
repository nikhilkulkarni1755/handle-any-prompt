import hashlib
import json
import sqlite3

from hap.schemas import Record

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY, text TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY, doc_id TEXT NOT NULL REFERENCES documents(id),
    type TEXT, quote TEXT, start INTEGER, end INTEGER, modality TEXT, specificity TEXT,
    entities TEXT, chunk_index INTEGER, run INTEGER, confidence REAL,
    model TEXT, prompt_version TEXT, superseded INTEGER DEFAULT 0
);
CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(quote, content='records', content_rowid='id');
CREATE TABLE IF NOT EXISTS unprocessed_spans (
    id INTEGER PRIMARY KEY, doc_id TEXT NOT NULL REFERENCES documents(id), start INTEGER, end INTEGER, reason TEXT
);
"""


class Store:
    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def add_document(self, text: str) -> str:
        """Raw text is immutable and content-addressed."""
        doc_id = hashlib.sha256(text.encode()).hexdigest()
        self.db.execute("INSERT OR IGNORE INTO documents (id, text) VALUES (?, ?)", (doc_id, text))
        self.db.commit()
        return doc_id

    def get_span(self, doc_id: str, start: int, end: int) -> str:
        text = self.db.execute("SELECT text FROM documents WHERE id = ?", (doc_id,)).fetchone()["text"]
        return text[start:end]

    def add_records(self, doc_id: str, records: list[Record], model: str, prompt_version: str) -> None:
        for r in records:
            cur = self.db.execute(
                "INSERT INTO records (doc_id, type, quote, start, end, modality, specificity, entities,"
                " chunk_index, run, confidence, model, prompt_version) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (doc_id, r.type.value, r.quote, r.start, r.end, r.modality.value, r.specificity.value,
                 json.dumps(r.entities), r.chunk_index, r.run, r.confidence, model, prompt_version),
            )
            self.db.execute("INSERT INTO records_fts (rowid, quote) VALUES (?, ?)", (cur.lastrowid, r.quote))
        self.db.commit()

    def add_unprocessed(self, doc_id: str, spans: list[tuple[int, int]], reason: str) -> None:
        self.db.executemany(
            "INSERT INTO unprocessed_spans (doc_id, start, end, reason) VALUES (?,?,?,?)",
            [(doc_id, a, b, reason) for a, b in spans],
        )
        self.db.commit()

    def records(self, doc_id: str) -> list[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM records WHERE doc_id = ? AND superseded = 0 ORDER BY start", (doc_id,)
        ).fetchall()

    def unprocessed(self, doc_id: str) -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM unprocessed_spans WHERE doc_id = ? ORDER BY start", (doc_id,)).fetchall()

    def search(self, doc_id: str, query: str) -> list[sqlite3.Row]:
        return self.db.execute(
            "SELECT r.* FROM records_fts f JOIN records r ON r.id = f.rowid"
            " WHERE records_fts MATCH ? AND r.doc_id = ? AND r.superseded = 0 ORDER BY r.start",
            (query, doc_id),
        ).fetchall()
