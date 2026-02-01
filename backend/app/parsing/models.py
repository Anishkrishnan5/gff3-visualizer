class Exon:
    def __init__(self, start: int, end: int, feature_type: str):
        self.start = start
        self.end = end
        self.feature_type = feature_type  # "exon" or "CDS"

    def length(self):
        return self.end - self.start + 1


class Transcript:
    def __init__(self, transcript_id: str, chrom: str, strand: str):
        self.id = transcript_id
        self.chrom = chrom
        self.strand = strand
        self.exons = []
        self.cds = []

    def add_exon(self, exon: Exon):
        self.exons.append(exon)

    def sort_exons(self):
        self.exons.sort(key=lambda e: e.start)

    @property
    def start(self):
        return min(e.start for e in self.exons) if self.exons else None

    @property
    def end(self):
        return max(e.end for e in self.exons) if self.exons else None


class Gene:
    def __init__(self, gene_id: str, chrom: str, strand: str, start: int = None, end: int = None):
        self.id = gene_id
        self.chrom = chrom
        self.strand = strand
        self.start = start
        self.end = end
        self.transcripts = []

    def add_transcript(self, transcript: Transcript):
        self.transcripts.append(transcript)
    
    def calculate_bounds(self):
        """Calculate gene start/end from all transcripts if not already set."""
        if self.start is not None and self.end is not None:
            return
        
        if not self.transcripts:
            return
        
        all_starts = []
        all_ends = []
        for tx in self.transcripts:
            if tx.exons:
                all_starts.append(min(e.start for e in tx.exons))
                all_ends.append(max(e.end for e in tx.exons))
        
        if all_starts and all_ends:
            self.start = min(all_starts)
            self.end = max(all_ends)
