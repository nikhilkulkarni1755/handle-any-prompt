from hap.pipeline import AGREED, UNVERIFIED, VERIFIED, ingest
from hap.store import Store
from tests.fake import FakeBackend


def test_agreeing_runs_get_full_confidence_and_no_verification():
    s, b = Store(), FakeBackend()
    d = ingest("Bob will fix it. Nothing else here", s, b)
    rows = s.records(d)
    assert [(r["quote"], r["confidence"]) for r in rows] == [("Bob will fix it", AGREED)]
    assert b.verified == []


def test_record_offsets_point_at_verbatim_source():
    s = Store()
    text = "Intro text. Bob will fix it. Outro"
    d = ingest(text, s, FakeBackend())
    r = s.records(d)[0]
    assert s.get_span(d, r["start"], r["end"]) == r["quote"] == "Bob will fix it"


def test_disagreement_is_verified_and_kept_not_discarded():
    s, b = Store(), FakeBackend(skip_on_seed=(1, 3))
    d = ingest("Bob will fix it.", s, b)
    assert [r["confidence"] for r in s.records(d)] == [VERIFIED]
    assert b.verified == ["Bob will fix it."]


def test_failed_verification_lowers_confidence_but_keeps_record():
    s = Store()
    d = ingest("Bob will fix it.", s, FakeBackend(skip_on_seed=(1, 3), verify_result=False))
    assert [r["confidence"] for r in s.records(d)] == [UNVERIFIED]


def test_paraphrased_output_is_never_stored_and_text_is_flagged():
    s = Store()
    d = ingest("Bob will fix it.", s, FakeBackend(paraphrase=True))
    assert s.records(d) == []
    assert len(s.unprocessed(d)) == 1


def test_uncovered_sentences_are_recorded_as_unprocessed():
    s = Store()
    d = ingest("Bob will fix it. Weather was nice.", s, FakeBackend())
    spans = [s.get_span(d, u["start"], u["end"]) for u in s.unprocessed(d)]
    assert spans == ["Weather was nice."]


def test_ledger_carries_entity_names_forward_only():
    s, b = Store(), FakeBackend()
    ingest("Bob will fix it. " * 400, s, b)  # forces multiple chunks
    assert b.ledgers[0] == [] and len(b.ledgers) > 2


def test_overlapping_chunks_do_not_duplicate_records():
    s = Store()
    text = "".join(f"Task {i} will ship. " for i in range(300))
    d = ingest(text, s, FakeBackend())
    quotes = [r["quote"] for r in s.records(d)]
    assert len(quotes) == len(set((r["start"] for r in s.records(d)))) == 300


def test_tiny_input_goes_through_same_path():
    s = Store()
    d = ingest("Hi", s, FakeBackend())
    assert s.records(d) == [] and len(s.unprocessed(d)) == 1
