from fastapi import APIRouter, UploadFile, Form
from fastapi.responses import JSONResponse
from app.parsing.gff3_parser import parse_gff3
from app.comparison.align import best_matching_transcript, compare_transcripts
from app.visualization.plotter import plot_gene_comparison, plot_to_base64, create_overview_plot
import tempfile
import os
import time
from collections import defaultdict


router = APIRouter()

def index_genes_by_locus(genes):
    index = defaultdict(list)
    for gene in genes.values():
        key = (gene.chrom, gene.strand)
        index[key].append(gene)
    return index


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


def find_matching_genes(ref_genes, pred_genes, overlap_threshold=0.5):
    matches = []

    ref_index = index_genes_by_locus(ref_genes)
    pred_index = index_genes_by_locus(pred_genes)

    for key in ref_index:
        if key not in pred_index:
            continue

        for ref_gene in ref_index[key]:
            for pred_gene in pred_index[key]:

                # 🚀 EARLY EXIT — ADD THIS HERE
                if pred_gene.end < ref_gene.start or pred_gene.start > ref_gene.end:
                    continue

                overlap_start = max(ref_gene.start, pred_gene.start)
                overlap_end = min(ref_gene.end, pred_gene.end)

                overlap_length = overlap_end - overlap_start + 1
                ref_length = ref_gene.end - ref_gene.start + 1
                pred_length = pred_gene.end - pred_gene.start + 1

                overlap_ratio = overlap_length / min(ref_length, pred_length)

                if overlap_ratio >= overlap_threshold:
                    matches.append(
                        (ref_gene.id, pred_gene.id, overlap_ratio)
                    )

    matches.sort(key=lambda x: x[2], reverse=True)
    return matches

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


@router.post("/find-matches")
async def find_matches(ref_file: UploadFile, pred_file: UploadFile, overlap_threshold: float = Form(0.5), include_overview: bool = Form(False)):
    """Find matching genes between two files by genomic coordinates. Optionally generate overview visualization."""
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
        
        matches = find_matching_genes(ref_genes, pred_genes, overlap_threshold)
        
        match_data = [
            {
                "ref_gene_id": ref_id,
                "pred_gene_id": pred_id,
                "overlap_ratio": round(ratio, 3),
                "ref_gene": serialize_gene(ref_genes[ref_id]),
                "pred_gene": serialize_gene(pred_genes[pred_id])
            }
            for ref_id, pred_id, ratio in matches
        ]
        
        result = {
            "matches": match_data,
            "total_matches": len(matches)
        }
        
        # Generate overview visualization if requested
        if include_overview and match_data:
            overview_fig = create_overview_plot(match_data)
            result["overview_image"] = plot_to_base64(overview_fig)
        
        return result
    finally:
        if os.path.exists(ref_temp_path):
            os.unlink(ref_temp_path)
        if os.path.exists(pred_temp_path):
            os.unlink(pred_temp_path)


@router.post("/visualize-gene")
async def visualize_gene(ref_file: UploadFile, pred_file: UploadFile, 
                         ref_gene_id: str = Form(...), pred_gene_id: str = Form(...)):
    """Generate a detailed visualization comparing two specific genes."""
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
        
        ref_gene = ref_genes.get(ref_gene_id)
        pred_gene = pred_genes.get(pred_gene_id)
        
        if not ref_gene:
            return JSONResponse({"error": f"Gene {ref_gene_id} not found in reference file"}, status_code=404)
        if not pred_gene:
            return JSONResponse({"error": f"Gene {pred_gene_id} not found in predicted file"}, status_code=404)
        
        # Serialize genes
        ref_gene_dict = serialize_gene(ref_gene)
        pred_gene_dict = serialize_gene(pred_gene)
        
        # Get comparison data
        comparisons = []
        for pred_tx in pred_gene.transcripts:
            ref_tx = best_matching_transcript(pred_tx, ref_gene.transcripts)
            if ref_tx:
                diff = compare_transcripts(ref_tx, pred_tx)
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
        
        # Generate visualization
        fig = plot_gene_comparison(
            ref_gene_dict, pred_gene_dict,
            ref_gene_dict['transcripts'], pred_gene_dict['transcripts'],
            comparisons
        )
        
        image_base64 = plot_to_base64(fig)
        
        return {
            "ref_gene_id": ref_gene_id,
            "pred_gene_id": pred_gene_id,
            "image": image_base64,
            "comparison_data": comparisons
        }
    finally:
        if os.path.exists(ref_temp_path):
            os.unlink(ref_temp_path)
        if os.path.exists(pred_temp_path):
            os.unlink(pred_temp_path)


@router.post("/gene")
async def get_gene(ref_file: UploadFile, pred_file: UploadFile, gene_id: str = Form(...)):
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


@router.post("/compare-genes")
async def compare_genes(ref_file: UploadFile, pred_file: UploadFile, 
                        ref_gene_id: str = Form(...), pred_gene_id: str = Form(...)):
    """Compare two genes with different IDs from different files."""
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
        
        ref_gene = ref_genes.get(ref_gene_id)
        pred_gene = pred_genes.get(pred_gene_id)
        
        if not ref_gene:
            return {"error": f"Gene {ref_gene_id} not found in reference file"}
        if not pred_gene:
            return {"error": f"Gene {pred_gene_id} not found in predicted file"}
        
        comparisons = []

        for pred_tx in pred_gene.transcripts:
            ref_tx = best_reference_transcript(pred_tx, ref_gene.transcripts)
            if ref_tx:
                diff = compare_transcripts(ref_tx, pred_tx)
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
            "gene_id": f"{ref_gene_id} ↔ {pred_gene_id}",
            "ref_gene_id": ref_gene_id,
            "pred_gene_id": pred_gene_id,
            "comparisons": comparisons
        }
    finally:
        if os.path.exists(ref_temp_path):
            os.unlink(ref_temp_path)
        if os.path.exists(pred_temp_path):
            os.unlink(pred_temp_path)


@router.post("/compare")
async def compare_gff3(ref_file: UploadFile, pred_file: UploadFile, gene_id: str = Form(...)):
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