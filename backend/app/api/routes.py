from fastapi import APIRouter, UploadFile
from app.parsing.gff3_parser import parse_gff3
from app.comparison.align import compare_transcripts
import tempfile
import os

router = APIRouter()


def best_reference_transcript(pred_tx, ref_transcripts):
    """Find the best matching reference transcript for a predicted transcript."""
    # Simple implementation: return first transcript for now
    # Can be enhanced with better matching logic
    return ref_transcripts[0] if ref_transcripts else None


def serialize_gene(gene):
    """Convert Gene object to JSON-serializable dict."""
    return {
        "gene_id": gene.id,
        "chrom": gene.chrom,
        "start": gene.start,
        "end": gene.end,
        "strand": gene.strand,
        "transcripts": [
            {
                "transcript_id": tx.id,
                "exons": [
                    {
                        "start": exon.start,
                        "end": exon.end,
                        "type": exon.feature_type
                    }
                    for exon in tx.exons
                ]
            }
            for tx in gene.transcripts
        ]
    }


@router.post("/parse")
async def parse_gff3_file(file: UploadFile):
    """Parse a single GFF3 file and return all genes."""
    content = await file.read()
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.gff3') as temp:
        temp.write(content.decode('utf-8'))
        temp_path = temp.name
    
    try:
        genes = parse_gff3(temp_path)
        return {
            "genes": [serialize_gene(gene) for gene in genes.values()],
            "gene_ids": list(genes.keys())
        }
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/gene")
async def get_gene(ref_file: UploadFile, pred_file: UploadFile, gene_id: str):
    """Get gene data from both files for visualization."""
    ref_content = await ref_file.read()
    pred_content = await pred_file.read()
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.gff3') as ref_temp:
        ref_temp.write(ref_content.decode('utf-8'))
        ref_temp_path = ref_temp.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.gff3') as pred_temp:
        pred_temp.write(pred_content.decode('utf-8'))
        pred_temp_path = pred_temp.name
    
    try:
        ref_genes = parse_gff3(ref_temp_path)
        pred_genes = parse_gff3(pred_temp_path)
        
        ref_gene = ref_genes.get(gene_id)
        pred_gene = pred_genes.get(gene_id)
        
        if not ref_gene:
            return {"error": f"Gene {gene_id} not found in reference file"}
        if not pred_gene:
            return {"error": f"Gene {gene_id} not found in predicted file"}
        
        return {
            "gene_id": gene_id,
            "reference": serialize_gene(ref_gene),
            "predicted": serialize_gene(pred_gene)
        }
    finally:
        if os.path.exists(ref_temp_path):
            os.unlink(ref_temp_path)
        if os.path.exists(pred_temp_path):
            os.unlink(pred_temp_path)


@router.post("/compare")
async def compare_gff3(ref_file: UploadFile, pred_file: UploadFile, gene_id: str):
    # Save uploaded files temporarily
    ref_content = await ref_file.read()
    pred_content = await pred_file.read()
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.gff3') as ref_temp:
        ref_temp.write(ref_content.decode('utf-8'))
        ref_temp_path = ref_temp.name
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.gff3') as pred_temp:
        pred_temp.write(pred_content.decode('utf-8'))
        pred_temp_path = pred_temp.name
    
    try:
        # Parse GFF3 files
        ref_genes = parse_gff3(ref_temp_path)
        pred_genes = parse_gff3(pred_temp_path)
        
        ref_gene = ref_genes.get(gene_id)
        pred_gene = pred_genes.get(gene_id)
        
        if not ref_gene or not pred_gene:
            return {"error": f"Gene {gene_id} not found in one or both files"}
        
        comparisons = []

        for pred_tx in pred_gene.transcripts:
            ref_tx = best_reference_transcript(pred_tx, ref_gene.transcripts)
            if ref_tx:
                diff = compare_transcripts(ref_tx, pred_tx)
                # Serialize Exon objects to dictionaries
                serialized_diff = {
                    "reference_transcript": ref_tx.id,
                    "predicted_transcript": pred_tx.id,
                    "matched": [
                        {"ref": {"start": r.start, "end": r.end, "type": r.feature_type},
                         "pred": {"start": p.start, "end": p.end, "type": p.feature_type}}
                        for r, p in diff["matched"]
                    ],
                    "missing": [
                        {"start": e.start, "end": e.end, "type": e.feature_type}
                        for e in diff["missing"]
                    ],
                    "extra": [
                        {"start": e.start, "end": e.end, "type": e.feature_type}
                        for e in diff["extra"]
                    ],
                    "partial": [
                        {"ref": {"start": r.start, "end": r.end, "type": r.feature_type},
                         "pred": {"start": p.start, "end": p.end, "type": p.feature_type}}
                        for r, p in diff["partial"]
                    ]
                }
                comparisons.append(serialized_diff)

        return {
            "gene_id": gene_id,
            "comparisons": comparisons
        }
    finally:
        # Clean up temporary files
        if os.path.exists(ref_temp_path):
            os.unlink(ref_temp_path)
        if os.path.exists(pred_temp_path):
            os.unlink(pred_temp_path)