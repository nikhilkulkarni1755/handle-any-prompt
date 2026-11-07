# Principles

## Target

- **Deployment:** Tier 1, fully local on one Mac. No data leaves the machine by default.
- **Consumer:** a downstream agent, not a human reader.
- **Priority:** accuracy first. Latency is allowed to suffer.

## Problem

The input is arbitrary length and the model window is small. Apple's on-device model has about 4K tokens of input and output combined. The output must be a memory in which nothing is lost, nothing is invented, and vague statements stay vague.

The telephone game happens when model B reads model A's paraphrase and meaning decays with each hop. These rules prevent it.

1. **Raw text is the source of truth.** It is stored verbatim and never edited. Everything else is an index into it.
2. **One hop from source.** Every extraction reads raw text, never another model's prose. No summaries of summaries.
3. **Every record carries a verbatim quote and character offsets.** If the quote is not a literal substring of the source, the record is rejected.
4. **Vagueness is data.** Each record has explicit `specificity` and `modality` fields. The pipeline never fills gaps. A missing detail becomes an open question.
5. **Nothing is dropped silently.** Coverage is checked mechanically. Every sentence maps to a record or to an explicit "no extractable content" marker.
6. **Consolidation is pointers only.** Threads, outlines and task lists link back to record IDs. They never replace them.
7. **Accuracy beats speed.** When a cheaper shortcut and a redundant check disagree, run the check.
