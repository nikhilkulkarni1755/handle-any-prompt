import json

from hap.segment import segment
from hap.store import Store


def render(store: Store, doc_id: str) -> str:
    """Detailed summary built only from verbatim quotes, in prompt order. No model rewrites anything."""
    text = store.text(doc_id)
    spans: dict[tuple[int, int], list] = {}
    for r in store.records(doc_id):
        spans.setdefault((r["start"], r["end"]), []).append(r)
    unprocessed = store.unprocessed(doc_id)
    entities = sorted({e for rs in spans.values() for r in rs for e in json.loads(r["entities"])})

    out = [
        "# Summary",
        f"{len(text)} characters, {len(segment(text))} chunks, {len(spans)} captured spans, "
        f"{len(unprocessed)} spans quoted verbatim below because extraction was incomplete.",
        "",
        "## Content, in prompt order",
    ]
    for (start, end), rs in sorted(spans.items()):
        best = max(rs, key=lambda r: r["confidence"])
        types = "/".join(sorted({r["type"] for r in rs}))
        flag = " ⚠ low confidence" if best["confidence"] < 0.7 else ""
        out.append(f"- [{types} · {best['modality']} · {best['specificity']}] {best['quote']}  (chars {start}-{end}){flag}")
    if entities:
        out += ["", "## Names mentioned", ", ".join(entities)]
    if unprocessed:
        out += ["", "## Text not captured by extraction (verbatim)"]
        out += [f"- {text[u['start']:u['end']].strip()}  (chars {u['start']}-{u['end']})" for u in unprocessed]
    return "\n".join(out) + "\n"
