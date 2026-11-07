# Pipeline

Short and long inputs share one code path.

## Stage 0: Intake

Store the raw text and its hash. Estimate tokens conservatively (chars / 3 plus a margin), since small models lack reliable public tokenizers. Inputs under about 800 tokens skip chunking and run a single pass.

## Stage 1: Segmentation (deterministic, no model)

- Split on structure first: headings, paragraphs, then sentences. Cut mid-sentence only as a last resort.
- Target 500-700 tokens of chunk text. Smaller chunks cost more calls but give the model less to lose.
- Overlap about 100 tokens so ideas that span a boundary are not cut. Deduplicate by offsets afterward.

## Stage 2: Per-chunk extraction

Each call receives the chunk, the extraction schema, and a **name-only entity ledger**: known entities and aliases, never prose. This resolves pronouns without carrying meaning through a paraphrase. Output is schema-constrained and contains:

- Claims, requirements, constraints, decisions and questions, each with `quote`, `start`, `end`, `modality`, `specificity` and `confidence`.
- Entities and aliases.
- Quantities, dates and names, copied verbatim.
- References such as "as I said earlier", stored as unresolved pointers.
- Tangent markers where a span departs from the preceding topic.

Because accuracy outranks latency, **every chunk is extracted twice** with different sampling seeds, in sequence. Records are compared by quote span. Disagreements are not merged silently. They go to a verification pass.

## Stage 3: Validation (deterministic)

- The quote must be a substring of the chunk.
- Every number, name and date in a record must appear in its quote.
- Failures get one retry. After that the span is stored as an `unprocessed_span`. It is still preserved and is flagged for review.
- A coverage report lists every uncovered sentence.

## Stage 4: Verification pass

For each disagreement between the two extractions, ask the model a narrow question with only the quote and the two candidate records: does the quote support this record, and is the modality or specificity right? Unresolved cases are kept as low-confidence records. They are never discarded.

## Stage 5: Memory write

See the [memory model](memory-model.md).

## Stage 6: Consolidation (over records only)

- Merge entities by string match plus embeddings. Merges are reversible and aliases are kept.
- Resolve reference pointers by search over records.
- Cluster records into topic threads. Tangents become child threads with a `tangent_of` edge.
- Flag contradictions. Both records are kept, joined by a `contradicts` edge.
- Build a navigable outline. It is an index, and every node expands to its source quotes.

## Stage 7: Agent-facing interface

The downstream agent reads the memory through a small query surface, exposed as a library API and an MCP server:

- `search_records(query)` for full-text and vector search
- `get_span(start, end)` for raw source text
- `get_thread(id)` and `get_outline()`
- `list_open_questions()` for everything the input left unspecified
- `get_record(id)` with its quote and provenance

The task summary is generated from records and cites record IDs per line. Unspecified items appear under "Open questions" instead of being guessed.
