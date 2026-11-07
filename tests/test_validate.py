from hap.schemas import Chunk, ExtractedRecord, Modality, RecordType, Specificity
from hap.validate import uncovered, validate

CHUNK = Chunk(index=2, start=100, end=130, text="Ship by Friday. Maybe add SSO.")


def rec(quote, entities=()):
    return ExtractedRecord(
        type=RecordType.requirement,
        quote=quote,
        modality=Modality.stated,
        specificity=Specificity.exact,
        entities=list(entities),
    )


def test_verbatim_quote_gets_absolute_offsets():
    ok, bad = validate(CHUNK, [rec("Maybe add SSO.", ["SSO"])], run=0)
    assert not bad
    assert (ok[0].start, ok[0].end) == (116, 130)
    assert ok[0].chunk_index == 2


def test_paraphrased_quote_is_rejected():
    ok, bad = validate(CHUNK, [rec("Deliver on Friday")], run=0)
    assert not ok and len(bad) == 1


def test_empty_quote_is_rejected():
    ok, bad = validate(CHUNK, [rec("")], run=0)
    assert not ok and len(bad) == 1


def test_entity_absent_from_quote_is_rejected():
    ok, bad = validate(CHUNK, [rec("Ship by Friday.", ["Monday"])], run=0)
    assert not ok and len(bad) == 1


def test_uncovered_reports_sentences_without_records():
    ok, _ = validate(CHUNK, [rec("Ship by Friday.")], run=0)
    gaps = uncovered(CHUNK.text, [r.model_copy(update={"start": r.start - 100, "end": r.end - 100}) for r in ok])
    assert [CHUNK.text[a:b] for a, b in gaps] == ["Maybe add SSO."]


def test_fully_covered_has_no_gaps():
    ok, _ = validate(Chunk(index=0, start=0, end=3, text="Hi."), [rec("Hi.")], run=0)
    assert uncovered("Hi.", ok) == []


def test_repeated_quote_maps_to_successive_occurrences():
    chunk = Chunk(index=0, start=0, end=19, text="Yes. No. Yes. Done.")
    ok, _ = validate(chunk, [rec("Yes."), rec("Yes.")], run=0)
    assert [(r.start, r.end) for r in ok] == [(0, 4), (9, 13)]


def test_partially_captured_sentence_is_flagged():
    text = "Ship by Friday, budget is 5k."
    ok, _ = validate(Chunk(index=0, start=0, end=len(text), text=text), [rec("Ship by Friday")], run=0)
    assert uncovered(text, ok) == [(0, len(text))]
