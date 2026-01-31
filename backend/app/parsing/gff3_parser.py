from collections import defaultdict
from .models import Gene, Transcript, Exon


def parse_attributes(attr_string: str) -> dict:
    """
    Parse the 9th column of a GFF3 line into a dictionary.
    Example: "ID=tx1;Parent=gene1"
    """
    attributes = {}
    for part in attr_string.split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            attributes[key] = value
    return attributes


def parse_gff3(filepath: str) -> dict:
    """
    Parse a GFF3 file and return a dict of gene_id -> Gene objects.
    """

    genes = {}
    transcripts = {}

    # Temporary storage
    transcript_to_gene = {}
    transcript_metadata = {}  # Store chrom/strand for transcripts (for geneID-based genes)
    exon_buffer = defaultdict(list)

    with open(filepath, "r") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue

            fields = line.strip().split("\t")
            if len(fields) != 9:
                continue

            chrom, source, feature_type, start, end, score, strand, phase, attributes = fields
            start, end = int(start), int(end)
            attr_dict = parse_attributes(attributes)

            if feature_type == "gene":
                gene_id = attr_dict.get("ID")
                if gene_id:
                    genes[gene_id] = Gene(
                        gene_id=gene_id,
                        chrom=chrom,
                        strand=strand,
                        start=start,
                        end=end
                    )

            elif feature_type == "exon":
                tx_id = attr_dict.get("ID")
                # Support both Parent (standard) and geneID (alternative format)
                parent_gene = attr_dict.get("Parent") or attr_dict.get("geneID")

                if tx_id and parent_gene:
                    transcript = Transcript(tx_id, chrom=chrom, strand=strand)
                    transcripts[tx_id] = transcript
                    transcript_to_gene[tx_id] = parent_gene
                    # Store metadata for creating genes from geneID
                    transcript_metadata[tx_id] = {"chrom": chrom, "strand": strand}

            elif feature_type in ("exon", "CDS"):
                parent_tx = attr_dict.get("Parent")
                if parent_tx:
                    exon = Exon(start, end, feature_type)
                    exon_buffer[parent_tx].append(exon)

    # Link exons → transcripts
    for tx_id, exons in exon_buffer.items():
        if tx_id in transcripts:
            for exon in exons:
                transcripts[tx_id].add_exon(exon)
            transcripts[tx_id].sort_exons()

    # Create genes from geneID if they don't exist (for files without gene features)
    for tx_id, gene_id in transcript_to_gene.items():
        if gene_id not in genes and tx_id in transcript_metadata:
            # Create gene from transcript metadata (start/end will be calculated later)
            metadata = transcript_metadata[tx_id]
            genes[gene_id] = Gene(
                gene_id=gene_id,
                chrom=metadata["chrom"],
                strand=metadata["strand"]
            )

    # Link transcripts → genes
    for tx_id, gene_id in transcript_to_gene.items():
        if gene_id in genes and tx_id in transcripts:
            genes[gene_id].add_transcript(transcripts[tx_id])

    # 🚨 ENFORCE BIOLOGICAL CONSISTENCY HERE
    for gene in genes.values():
        gene.transcripts = [
            tx for tx in gene.transcripts
            if tx.chrom == gene.chrom and tx.strand == gene.strand
        ]

    # Calculate gene bounds for genes that don't have explicit start/end
    for gene in genes.values():
        gene.calculate_bounds()

    return genes