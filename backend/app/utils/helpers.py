from typing import Any

from app.parsing.gff3_parser import parse_gff3

genes = parse_gff3("data/examples/Cylto1_FilteredModels1.gff3")

print(f"Parsed {len(genes)} genes")

for gene_id, gene in list[tuple](genes.items())[:1]:
    print("Gene:", gene_id)
    for tx in gene.transcripts:
        print("  Transcript:", tx.id)
        for exon in tx.exons:
            print(f"    Exon {exon.start}-{exon.end}")