import json
import logging
import subprocess
from pathlib import Path

from hap.schemas import Extraction, Record

SHIM = Path(__file__).resolve().parent.parent / "apple-fm-shim/.build/release/apple-fm-shim"
log = logging.getLogger(__name__)


class AppleFMBackend:
    """Talks to the Swift shim over line-delimited JSON on stdio."""

    name = "apple-fm"

    def __init__(self, shim: Path = SHIM):
        self.proc = subprocess.Popen([str(shim)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        info = self._call({"op": "info"})
        if not info.get("available"):
            self.close()
            raise RuntimeError(f"Apple Foundation Models unavailable: {info.get('reason', info)}")
        self.context_size = info["contextSize"]

    def _call(self, request: dict) -> dict:
        self.proc.stdin.write(json.dumps(request) + "\n")
        self.proc.stdin.flush()
        return json.loads(self.proc.stdout.readline())

    def extract(self, chunk_text: str, ledger: list[str], seed: int) -> Extraction:
        resp = self._call({"op": "extract", "chunk": chunk_text, "ledger": ledger, "seed": seed})
        if "error" in resp:
            # Surfaces later as unprocessed spans, so the text is flagged rather than lost.
            log.warning("apple-fm extract failed: %s", resp["error"])
            return Extraction(records=[])
        return Extraction.model_validate(resp)

    def verify(self, record: Record) -> bool:
        resp = self._call({"op": "verify", "quote": record.quote, "type": record.type.value,
                           "modality": record.modality.value, "specificity": record.specificity.value})
        return resp.get("supported", False)

    def close(self) -> None:
        self.proc.stdin.close()
        self.proc.wait()
