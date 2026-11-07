# handle-any-prompt

A component that ingests input of any size, from 4 characters to a War and Peace-length prompt that zigzags and goes on tangents. It uses a small model (Apple Foundation Models, a small Qwen, Haiku or Opus) to turn the input into a structured memory that a downstream agent can query.

The goal is no telephone-game drift. After one pass, meaning is preserved: vague input stays vague, specific input keeps every specific detail.

Design docs:

- [Principles](docs/principles.md)
- [Pipeline](docs/pipeline.md)
- [Memory model](docs/memory-model.md)
- [Stack and deployment](docs/stack-and-deployment.md)
- [Evaluation](docs/evaluation.md)

Status: core pipeline (segmenter, validation, store, dual-run ingest) is implemented and tested against a fake backend. Real model backends are not yet written.
