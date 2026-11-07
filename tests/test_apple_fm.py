import pytest

from hap.apple_fm import SHIM, AppleFMBackend
from hap.pipeline import ingest
from hap.store import Store

pytestmark = pytest.mark.skipif(not SHIM.exists(), reason="build the shim: cd apple-fm-shim && swift build -c release")


@pytest.fixture(scope="module")
def fm():
    try:
        backend = AppleFMBackend()
    except RuntimeError as e:
        pytest.skip(str(e))
    yield backend
    backend.close()


def test_extract_returns_verbatim_quotes_and_preserves_hedging(fm):
    text = "Bob will probably ship the beta by Friday."
    records = fm.extract(text, [], 0).records
    assert records and all(r.quote in text for r in records)
    assert records[0].modality.value == "hedged"


def test_ingest_end_to_end_stores_records(fm):
    store = Store()
    d = ingest("We might add SSO later, not sure.", store, fm)
    assert store.records(d)


def test_context_size_is_reported(fm):
    assert fm.context_size > 0
