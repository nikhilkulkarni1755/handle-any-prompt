# Stack and deployment

## Deployment: Tier 1, local

A CLI and library plus a single SQLite file on one Apple Silicon Mac. No network calls by default, so no input data leaves the machine.

Cloud models (Haiku, Opus) are an opt-in escalation backend for `unprocessed_spans` and unresolved verification cases. They are off by default.

## Stack

- **Orchestrator:** Python. It handles segmentation, validation, queueing and consolidation, and defines a model-agnostic `Backend.extract(chunk, schema)` interface. Pydantic models define the schemas and double as JSON-schema constraints.
- **Apple Foundation Models:** a small Swift shim exposes a local endpoint. It uses guided generation (`@Generable`) for structured output. This needs macOS 26 or later with Apple Intelligence enabled. If a Python SDK for Foundation Models proves usable, the shim can be dropped.
- **Small Qwen (3.5-class):** MLX-LM or llama.cpp with grammar-constrained or JSON-schema decoding.
- **Storage:** SQLite with FTS5 and sqlite-vec.
- **Embeddings:** a small local model (bge-small class, or Apple's NLEmbedding).
- **Agent interface:** a Python library API and an MCP server.

## Job state

The `chunks` table is the queue. Each job is idempotent, keyed by `hash(chunk, prompt_version, model, run)`, so a crash resumes with no duplicate work. Chunks run sequentially, since accuracy outranks latency and the on-device model is effectively serial.

## Observability

Structured logs per document and chunk, recording validation-failure rate, retry rate, run-disagreement rate, coverage percentage and tokens per call.

## Release gate

The [evaluation](evaluation.md) suite must pass before any prompt, schema or model change ships.
