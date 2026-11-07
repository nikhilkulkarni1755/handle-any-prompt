from hap.schemas import Chunk, ExtractedRecord, Record
from hap.segment import _units


def validate(chunk: Chunk, extracted: list[ExtractedRecord], run: int) -> tuple[list[Record], list[ExtractedRecord]]:
    """Anchor each record to absolute offsets. Reject any whose quote or entities are not verbatim in the chunk."""
    accepted, rejected = [], []
    last: dict[str, int] = {}  # a repeated quote maps to its next occurrence, assuming document order
    for e in extracted:
        pos = chunk.text.find(e.quote, last.get(e.quote, -1) + 1) if e.quote else -1
        if pos < 0 and e.quote in last:
            pos = chunk.text.find(e.quote)
        if pos < 0 or any(name not in e.quote for name in e.entities):
            rejected.append(e)
            continue
        last[e.quote] = pos
        start = chunk.start + pos
        accepted.append(
            Record(**e.model_dump(), start=start, end=start + len(e.quote), chunk_index=chunk.index, run=run, confidence=0.0)
        )
    return accepted, rejected


def uncovered(text: str, records: list[Record]) -> list[tuple[int, int]]:
    """Sentence-level spans with any letter or digit outside every record's quote, so partial capture is flagged."""
    covered: list[list[int]] = []
    for a, b in sorted((r.start, r.end) for r in records):
        if covered and a <= covered[-1][1]:
            covered[-1][1] = max(covered[-1][1], b)
        else:
            covered.append([a, b])
    out = []
    for a, b in _units(text, max_chars=len(text) or 1):
        gaps, pos = [], a
        for ca, cb in covered:
            if cb <= a or ca >= b:
                continue
            gaps.append(text[pos:max(ca, a)])
            pos = min(cb, b)
        gaps.append(text[pos:b])
        if any(c.isalnum() for g in gaps for c in g):
            out.append((a, b))
    return out
