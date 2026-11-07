# Memory model

One SQLite file per ingested document set.

| Table | Purpose |
|---|---|
| `documents` | raw text, hash, ingest time |
| `chunks` | offsets, overlap, status, model and prompt version, extraction run (A or B) |
| `records` | typed items with quote, offsets, modality, specificity, confidence |
| `entities` / `aliases` | resolved names |
| `edges` | `elaborates`, `contradicts`, `tangent_of`, `refers_to`, `depends_on` |
| `threads` | topic clusters with member records |
| `unprocessed_spans` | validation failures awaiting review |

## Record fields

- `type`: claim, requirement, constraint, decision, question, reference, tangent
- `quote`, `start`, `end`: verbatim source span
- `modality`: stated, hedged, implied, unspecified
- `specificity`: exact, approximate, vague, unspecified
- `confidence`: set by agreement between the two extraction runs and the verification pass
- `model`, `prompt_version`, `schema_version`

## Rules

- Records are append-only. Re-extraction with a better model adds new records and marks old ones superseded.
- Raw text is never modified.
- Search uses FTS5 for text and sqlite-vec for similarity.
