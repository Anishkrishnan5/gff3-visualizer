class Exon:
    def __init__(self, start: int, end: int, feature_type: str):
        self.start = start
        self.end = end
        self.feature_type = feature_type  # "exon" or "CDS"

    def length(self):
        return self.end - self.start + 1


class Transcript:
    def __init__(self, transcript_id: str):
        self.id = transcript_id
        self.exons = []

    def add_exon(self, exon: Exon):
        self.exons.append(exon)

    def sort_exons(self):
        self.exons.sort(key=lambda e: e.start)


class Gene:
    def __init__(self, gene_id: str, chrom: str, strand: str):
        self.id = gene_id
        self.chrom = chrom
        self.strand = strand
        self.transcripts = []

    def add_transcript(self, transcript: Transcript):
        self.transcripts.append(transcript)
