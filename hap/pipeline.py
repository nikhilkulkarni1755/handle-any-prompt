from hap.backend import Backend
from hap.schemas import Chunk, Record
from hap.segment import segment
from hap.store import Store
from hap.validate import uncovered, validate

PROMPT_VERSION = "v1"
AGREED, VERIFIED, UNVERIFIED = 1.0, 0.7, 0.3


def _run(backend: Backend, chunk: Chunk, ledger: list[str], run: int) -> list[Record]:
    """One extraction run, with a single retry if any record failed validation."""
    accepted, rejected = validate(chunk, backend.extract(chunk.text, ledger, run).records, run)
    if rejected:
        retried, _ = validate(chunk, backend.extract(chunk.text, ledger, run + 2).records, run)
        seen = {(r.start, r.end, r.type) for r in accepted}
        accepted += [r for r in retried if (r.start, r.end, r.type) not in seen]
    return accepted


def _reconcile(backend: Backend, a: list[Record], b: list[Record]) -> list[Record]:
    """Agreement across runs gets full confidence. Disagreements are verified, never discarded."""
    key = lambda r: (r.start, r.end, r.type)
    in_b = {key(r) for r in b}
    in_a = {key(r) for r in a}
    out = [r.model_copy(update={"confidence": AGREED}) for r in a if key(r) in in_b]
    for r in [r for r in a if key(r) not in in_b] + [r for r in b if key(r) not in in_a]:
        out.append(r.model_copy(update={"confidence": VERIFIED if backend.verify(r) else UNVERIFIED}))
    return out


def ingest(text: str, store: Store, backend: Backend) -> str:
    doc_id = store.add_document(text)
    ledger: list[str] = []
    stored: set[tuple] = set()
    all_records: list[Record] = []
    for chunk in segment(text):
        records = _reconcile(backend, _run(backend, chunk, ledger, 0), _run(backend, chunk, ledger, 1))
        fresh = [r for r in records if (r.start, r.end, r.type) not in stored]  # overlap between chunks
        stored |= {(r.start, r.end, r.type) for r in fresh}
        store.add_records(doc_id, fresh, backend.name, PROMPT_VERSION)
        all_records += fresh
        ledger = sorted(set(ledger) | {e for r in fresh for e in r.entities})
    store.add_unprocessed(doc_id, uncovered(text, all_records), "no record covers this sentence")
    return doc_id
