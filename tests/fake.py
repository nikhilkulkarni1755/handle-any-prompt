from hap.schemas import Extraction, ExtractedRecord, Modality, RecordType, Specificity


class FakeBackend:
    """Deterministic stand-in: one 'claim' per sentence that contains a trigger word."""

    name = "fake"

    def __init__(self, trigger="will", skip_on_seed=(), paraphrase=False, verify_result=True):
        self.trigger, self.skip_on_seed, self.paraphrase, self.verify_result = trigger, skip_on_seed, paraphrase, verify_result
        self.ledgers, self.verified = [], []

    def extract(self, chunk_text, ledger, seed):
        self.ledgers.append(list(ledger))
        if seed in self.skip_on_seed:
            return Extraction(records=[])
        recs = []
        for sentence in chunk_text.split(". "):
            s = sentence.strip()
            if self.trigger in s:
                quote = "PARAPHRASED" if self.paraphrase else s
                recs.append(ExtractedRecord(type=RecordType.claim, quote=quote, modality=Modality.stated,
                                            specificity=Specificity.vague))
        return Extraction(records=recs)

    def verify(self, record):
        self.verified.append(record.quote)
        return self.verify_result
