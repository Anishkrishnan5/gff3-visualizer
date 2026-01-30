class ExonDiff(BaseModel):
    start: int
    end: int
    status: str  # matched, missing, extra, partial
{
  "gene_id": "gene123",
  "reference_transcript": "tx1",
  "predicted_transcript": "txA",
  "exons": [
    {"start": 1100, "end": 1200, "status": "matched"},
    {"start": 1250, "end": 1350, "status": "partial"},
    {"start": 2000, "end": 2100, "status": "extra"}
  ]
}
