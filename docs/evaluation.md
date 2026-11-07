# Evaluation

Accuracy is the top priority, so evaluation gates every change.

- **Needle test:** plant facts at random positions in a 100K-token document and measure recall.
- **Vagueness test:** feed deliberately vague statements and count records that gained specificity. The target is zero.
- **Specificity test:** feed exact numbers, names and conditions and check they survive character for character.
- **Hallucination rate:** the share of records whose quote does not support them. Validation should push this near zero.
- **Agreement rate:** how often the two extraction runs agree per chunk. A drop signals a prompt or model regression.
- **Zigzag test:** a document that leaves topics and returns, to check tangent handling and reference resolution.
- **Cross-model comparison:** run the same document through Apple FM and Qwen and diff the memories to see where each model is weak.
- **Coverage:** every sentence maps to a record or an explicit no-content marker. The target is 100%.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Small model paraphrases and loses nuance | Verbatim quote requirement and substring validation |
| Meaning that spans chunks (pronouns, "as above") | Name-only ledger, overlap and deferred reference resolution |
| Model invents detail | `unspecified` is an explicit value, and validation rejects numbers or names absent from the quote |
| Window overflow | Conservative token estimate and a hard cap on chunk size |
| Wrong entity merges | Merges are reversible and aliases are kept |
| Silent drift from model or prompt changes | Per-record version stamps and the eval gate |
