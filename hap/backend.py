from typing import Protocol

from hap.schemas import Extraction, Record


class Backend(Protocol):
    name: str

    def extract(self, chunk_text: str, ledger: list[str], seed: int) -> Extraction:
        """Return schema-constrained records for one chunk. The ledger is entity names only, never prose."""

    def verify(self, record: Record) -> bool:
        """Does record.quote support the record's type, modality and specificity?"""
