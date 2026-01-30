def exon_overlap(e1, e2):
    overlap_start = max(e1.start, e2.start)
    overlap_end = min(e1.end, e2.end)
    return max(0, overlap_end - overlap_start)

def overlaps(e1, e2):
    return exon_overlap(e1, e2) > 0

def compare_transcripts(ref_tx, pred_tx):
    results = {
        "matched": [],
        "missing": [],
        "extra": [],
        "partial": []
    }

    for ref_exon in ref_tx.exons:
        overlaps_pred = [
            p for p in pred_tx.exons if overlaps(ref_exon, p)
        ]
        if not overlaps_pred:
            results["missing"].append(ref_exon)
        else:
            for p in overlaps_pred:
                if ref_exon.start == p.start and ref_exon.end == p.end:
                    results["matched"].append((ref_exon, p))
                else:
                    results["partial"].append((ref_exon, p))

    for pred_exon in pred_tx.exons:
        if not any(overlaps(pred_exon, r) for r in ref_tx.exons):
            results["extra"].append(pred_exon)

    return results
