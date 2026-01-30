from pydantic import BaseModel
from typing import List, Optional


class ExonDiff(BaseModel):
    start: int
    end: int
    status: str  # matched, missing, extra, partial


class TranscriptComparison(BaseModel):
    gene_id: str
    reference_transcript: str
    predicted_transcript: str
    exons: List[ExonDiff]
