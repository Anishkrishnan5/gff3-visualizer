def exon_overlap(e1, e2):
    overlap_start = max(e1.start, e2.start)
    overlap_end = min(e1.end, e2.end)
    return max(0, overlap_end - overlap_start + 1)

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

def transcript_overlap_ratio(tx1, tx2):
    if tx1.start is None or tx2.start is None:
        return 0.0

    overlap_start = max(tx1.start, tx2.start)
    overlap_end = min(tx1.end, tx2.end)

    if overlap_start > overlap_end:
        return 0.0

    overlap_len = overlap_end - overlap_start + 1
    len1 = tx1.end - tx1.start + 1
    len2 = tx2.end - tx2.start + 1

    return overlap_len / min(len1, len2)

def best_matching_transcript(pred_tx, ref_transcripts, min_overlap=0.1):
    best = None
    best_score = 0.0

    for ref_tx in ref_transcripts:
        if ref_tx.strand != pred_tx.strand:
            continue

        score = transcript_overlap_ratio(pred_tx, ref_tx)
        if score > best_score:
            best = ref_tx
            best_score = score

    return best if best_score >= min_overlap else None