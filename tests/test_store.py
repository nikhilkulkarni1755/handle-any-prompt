from hap.schemas import Modality, Record, RecordType, Specificity
from hap.store import Store


def make(quote, start):
    return Record(
        type=RecordType.claim, quote=quote, modality=Modality.hedged, specificity=Specificity.vague,
        entities=["Bob"], start=start, end=start + len(quote), chunk_index=0, run=0, confidence=0.5,
    )


def test_document_is_content_addressed_and_span_is_verbatim():
    s = Store()
    a = s.add_document("hello world")
    assert s.add_document("hello world") == a
    assert s.get_span(a, 6, 11) == "world"


def test_records_roundtrip_preserving_vagueness():
    s = Store()
    d = s.add_document("Bob might fix it soon.")
    s.add_records(d, [make("Bob might fix it soon.", 0)], "fake", "v1")
    row = s.records(d)[0]
    assert (row["modality"], row["specificity"], row["model"]) == ("hedged", "vague", "fake")


def test_search_finds_records_by_text_within_document():
    s = Store()
    d1, d2 = s.add_document("a"), s.add_document("b")
    s.add_records(d1, [make("Deploy on Friday", 0)], "fake", "v1")
    s.add_records(d2, [make("Deploy on Monday", 0)], "fake", "v1")
    assert [r["quote"] for r in s.search(d1, "Deploy")] == ["Deploy on Friday"]


def test_unprocessed_spans_are_kept():
    s = Store()
    d = s.add_document("abc")
    s.add_unprocessed(d, [(0, 3)], "no records")
    assert s.unprocessed(d)[0]["reason"] == "no records"
