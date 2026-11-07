from enum import Enum

from pydantic import BaseModel


class RecordType(str, Enum):
    claim = "claim"
    requirement = "requirement"
    constraint = "constraint"
    decision = "decision"
    question = "question"
    reference = "reference"
    tangent = "tangent"


class Modality(str, Enum):
    stated = "stated"
    hedged = "hedged"
    implied = "implied"
    unspecified = "unspecified"


class Specificity(str, Enum):
    exact = "exact"
    approximate = "approximate"
    vague = "vague"
    unspecified = "unspecified"


class ExtractedRecord(BaseModel):
    """What the model returns. Offsets are computed by us from the quote."""

    type: RecordType
    quote: str
    modality: Modality
    specificity: Specificity
    entities: list[str] = []


class Extraction(BaseModel):
    """Schema the model's output is constrained to, one per chunk."""

    records: list[ExtractedRecord]


class Chunk(BaseModel):
    index: int
    start: int
    end: int
    text: str


class Record(ExtractedRecord):
    """A validated record anchored to absolute offsets in the source."""

    start: int
    end: int
    chunk_index: int
    run: int
    confidence: float
