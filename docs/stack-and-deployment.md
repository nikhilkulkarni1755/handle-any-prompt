# Stack and deployment

## Deployment: Tier 1, local

A CLI and library plus a single SQLite file on one Apple Silicon Mac. No network calls by default, so no input data leaves the machine.

Cloud models (Haiku, Opus) are an opt-in escalation backend for `unprocessed_spans` and unresolved verification cases. They are off by default.

## Stack

- **Orchestrator:** Python. It handles segmentation, validation, queueing and consolidation, and defines a model-agnostic `Backend.extract(chunk, schema)` interface. Pydantic models define the schemas and double as JSON-schema constraints.
- **Apple Foundation Models:** `apple-fm-shim/` is a Swift executable that speaks line-delimited JSON over stdio (ops: `info`, `tokens`, `extract`, `verify`). A fresh session is used per call so nothing leaks between chunks. The output schema is built with `DynamicGenerationSchema` because the `@Generable` macros need Xcode's macro plugin, which Command Line Tools lack. Seed 0 uses greedy sampling and other seeds use seeded random sampling. This needs macOS 26 or later with Apple Intelligence enabled. On the development machine the reported context size is 8192 tokens, and `tokenCount` needs macOS 26.4 or later.
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
