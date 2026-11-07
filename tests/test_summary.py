from hap.pipeline import ingest
from hap.store import Store
from hap.summary import render
from tests.fake import FakeBackend


def test_summary_contains_captured_quotes_in_prompt_order():
    s = Store()
    d = ingest("First step will run. Then the second will finish.", s, FakeBackend())
    out = render(s, d)
    assert out.index("First step will run") < out.index("Then the second will finish")


def test_uncaptured_text_is_quoted_verbatim_so_nothing_is_lost():
    s = Store()
    d = ingest("Bob will fix it. The password is hunter2 and the port is 8443.", s, FakeBackend())
    out = render(s, d)
    assert "The password is hunter2 and the port is 8443." in out
    assert "Text not captured" in out


def test_every_alphanumeric_detail_survives():
    text = "Ship will go on March 14th. Budget 40,000 dollars. Call Dana on 555-0142. will confirm."
    s = Store()
    out = render(s, ingest(text, s, FakeBackend()))
    for token in ["March 14th", "40,000", "Dana", "555-0142"]:
        assert token in out
