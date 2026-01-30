"""
Matplotlib-based visualization for gene structure comparisons.
Generates static images showing gene comparisons.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle, FancyBboxPatch
import numpy as np
from io import BytesIO
import base64


def plot_gene_comparison(ref_gene, pred_gene, ref_transcripts, pred_transcripts, 
                         comparison_data=None, figsize=(14, 8)):
    """
    Create a matplotlib figure comparing reference and predicted gene structures.
    
    Args:
        ref_gene: Reference gene dict with start, end, chrom, strand
        pred_gene: Predicted gene dict with start, end, chrom, strand
        ref_transcripts: List of reference transcript dicts
        pred_transcripts: List of predicted transcript dicts
        comparison_data: Optional comparison results
        figsize: Figure size tuple
    
    Returns:
        matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    # Calculate bounds
    min_start = min(ref_gene['start'], pred_gene['start'])
    max_end = max(ref_gene['end'], pred_gene['end'])
    range_size = max_end - min_start
    padding = range_size * 0.05
    
    # Set up coordinate system
    x_min = min_start - padding
    x_max = max_end + padding
    
    # Track positions
    y_pos = 0
    track_height = 0.8
    track_spacing = 1.2
    
    # Colors
    ref_color = '#4a90e2'  # Blue
    pred_color = '#f5a623'  # Orange
    overlap_color = '#50c878'  # Green
    missing_color = '#e74c3c'  # Red
    extra_color = '#f39c12'  # Yellow
    
    # Draw reference transcripts
    ax.text(x_min - range_size * 0.1, y_pos + track_height/2, 
            'Reference', ha='right', va='center', fontweight='bold', fontsize=11)
    
    for tx_idx, tx in enumerate(ref_transcripts):
        tx_y = y_pos - tx_idx * track_spacing
        
        # Draw connecting line
        if tx['exons']:
            tx_start = min(e['start'] for e in tx['exons'])
            tx_end = max(e['end'] for e in tx['exons'])
            ax.plot([tx_start, tx_end], [tx_y, tx_y], 
                   color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=1)
        
        # Draw exons
        for exon in tx['exons']:
            width = exon['end'] - exon['start']
            height = track_height * 0.6
            y_offset = tx_y - height/2
            
            # Different style for CDS vs exon
            alpha = 1.0 if exon['type'] == 'CDS' else 0.7
            
            rect = Rectangle((exon['start'], y_offset), width, height,
                           facecolor=ref_color, edgecolor='black', 
                           linewidth=1.5, alpha=alpha, zorder=2)
            ax.add_patch(rect)
        
        # Transcript label
        ax.text(x_min - range_size * 0.08, tx_y, 
               tx['transcript_id'], ha='right', va='center', 
               fontsize=9, style='italic')
    
    y_pos -= len(ref_transcripts) * track_spacing + 0.5
    
    # Draw predicted transcripts
    ax.text(x_min - range_size * 0.1, y_pos + track_height/2, 
            'Predicted', ha='right', va='center', fontweight='bold', fontsize=11)
    
    for tx_idx, tx in enumerate(pred_transcripts):
        tx_y = y_pos - tx_idx * track_spacing
        
        # Draw connecting line
        if tx['exons']:
            tx_start = min(e['start'] for e in tx['exons'])
            tx_end = max(e['end'] for e in tx['exons'])
            ax.plot([tx_start, tx_end], [tx_y, tx_y], 
                   color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=1)
        
        # Draw exons
        for exon in tx['exons']:
            width = exon['end'] - exon['start']
            height = track_height * 0.6
            y_offset = tx_y - height/2
            
            alpha = 1.0 if exon['type'] == 'CDS' else 0.7
            
            rect = Rectangle((exon['start'], y_offset), width, height,
                           facecolor=pred_color, edgecolor='black', 
                           linewidth=1.5, alpha=alpha, zorder=2)
            ax.add_patch(rect)
        
        # Transcript label
        ax.text(x_min - range_size * 0.08, tx_y, 
               tx['transcript_id'], ha='right', va='center', 
               fontsize=9, style='italic')
    
    y_pos -= len(pred_transcripts) * track_spacing + 0.5
    
    # Draw comparison track if comparison data provided
    if comparison_data and len(comparison_data) > 0:
        ax.text(x_min - range_size * 0.1, y_pos + track_height/2, 
                'Comparison', ha='right', va='center', fontweight='bold', fontsize=11)
        
        for comp_idx, comp in enumerate(comparison_data):
            comp_y = y_pos - comp_idx * track_spacing
            
            # Draw overlaps
            if 'matched' in comp:
                for match in comp['matched']:
                    if 'ref' in match and 'pred' in match:
                        ref_exon = match['ref']
                        pred_exon = match['pred']
                        overlap_start = max(ref_exon['start'], pred_exon['start'])
                        overlap_end = min(ref_exon['end'], pred_exon['end'])
                        if overlap_start < overlap_end:
                            width = overlap_end - overlap_start
                            height = track_height * 0.6
                            rect = Rectangle((overlap_start, comp_y - height/2), 
                                           width, height,
                                           facecolor=overlap_color, 
                                           edgecolor='black', linewidth=1.5, zorder=3)
                            ax.add_patch(rect)
            
            # Draw missing (in ref but not pred)
            if 'missing' in comp:
                for exon in comp['missing']:
                    width = exon['end'] - exon['start']
                    height = track_height * 0.4
                    rect = Rectangle((exon['start'], comp_y - height/2), 
                                   width, height,
                                   facecolor=missing_color, 
                                   edgecolor='black', linewidth=1.5,
                                   linestyle='--', zorder=2)
                    ax.add_patch(rect)
            
            # Draw extra (in pred but not ref)
            if 'extra' in comp:
                for exon in comp['extra']:
                    width = exon['end'] - exon['start']
                    height = track_height * 0.4
                    rect = Rectangle((exon['start'], comp_y + height/2), 
                                   width, height,
                                   facecolor=extra_color, 
                                   edgecolor='black', linewidth=1.5,
                                   linestyle='--', zorder=2)
                    ax.add_patch(rect)
    
    # Set axis properties
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_pos - 1, 1)
    ax.set_xlabel(f'Genomic Position on {ref_gene["chrom"]}', fontsize=12, fontweight='bold')
    ax.set_ylabel('Transcripts', fontsize=12, fontweight='bold')
    
    # Add strand indicator
    strand_symbol = '→' if ref_gene['strand'] == '+' else '←'
    ax.text((x_min + x_max) / 2, 0.5, 
           f'Strand: {strand_symbol} ({ref_gene["strand"]})',
           ha='center', va='center', fontsize=11, 
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Add title
    title = f"Gene Comparison: {ref_gene.get('gene_id', 'Unknown')} vs {pred_gene.get('gene_id', 'Unknown')}"
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor=ref_color, label='Reference Exon', alpha=0.7),
        mpatches.Patch(facecolor=pred_color, label='Predicted Exon', alpha=0.7),
        mpatches.Patch(facecolor=overlap_color, label='Overlap'),
        mpatches.Patch(facecolor=missing_color, label='Missing in Predicted'),
        mpatches.Patch(facecolor=extra_color, label='Extra in Predicted'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
    
    # Format x-axis
    ax.tick_params(axis='x', labelsize=9)
    ax.tick_params(axis='y', labelsize=9)
    ax.grid(axis='x', alpha=0.3, linestyle=':', linewidth=0.5)
    
    plt.tight_layout()
    return fig


def plot_to_base64(fig):
    """Convert matplotlib figure to base64 encoded PNG."""
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64


def create_overview_plot(matches, figsize=(16, 10)):
    """
    Create an overview plot showing all gene matches.
    
    Args:
        matches: List of match dicts with ref_gene, pred_gene, overlap_ratio
        figsize: Figure size tuple
    
    Returns:
        matplotlib.figure.Figure
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    if not matches:
        ax.text(0.5, 0.5, 'No gene matches found', 
               ha='center', va='center', fontsize=14)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return fig
    
    # Sort matches by genomic position
    sorted_matches = sorted(matches, key=lambda m: m['ref_gene']['start'])
    
    # Plot each match
    y_pos = 0
    track_height = 0.6
    track_spacing = 1.5
    
    ref_color = '#4a90e2'
    pred_color = '#f5a623'
    overlap_color = '#50c878'
    
    for match_idx, match in enumerate(sorted_matches[:50]):  # Limit to 50 for readability
        ref_gene = match['ref_gene']
        pred_gene = match['pred_gene']
        overlap_ratio = match['overlap_ratio']
        
        y = y_pos - match_idx * track_spacing
        
        # Draw reference gene
        ref_width = ref_gene['end'] - ref_gene['start']
        ref_rect = Rectangle((ref_gene['start'], y - track_height/2), 
                           ref_width, track_height,
                           facecolor=ref_color, edgecolor='black', 
                           linewidth=1.5, alpha=0.7, zorder=2)
        ax.add_patch(ref_rect)
        
        # Draw predicted gene
        pred_width = pred_gene['end'] - pred_gene['start']
        pred_rect = Rectangle((pred_gene['start'], y - track_height/2), 
                            pred_width, track_height,
                            facecolor=pred_color, edgecolor='black', 
                            linewidth=1.5, alpha=0.7, zorder=2)
        ax.add_patch(pred_rect)
        
        # Draw overlap region
        overlap_start = max(ref_gene['start'], pred_gene['start'])
        overlap_end = min(ref_gene['end'], pred_gene['end'])
        if overlap_start < overlap_end:
            overlap_width = overlap_end - overlap_start
            overlap_rect = Rectangle((overlap_start, y - track_height/2), 
                                    overlap_width, track_height,
                                    facecolor=overlap_color, 
                                    edgecolor='black', linewidth=2, zorder=3)
            ax.add_patch(overlap_rect)
        
        # Add labels
        label_x = min(ref_gene['start'], pred_gene['start']) - 5000
        ax.text(label_x, y, 
               f"{ref_gene['gene_id'][:15]}... ↔ {pred_gene['gene_id'][:15]}... ({overlap_ratio:.0%})",
               ha='right', va='center', fontsize=8)
    
    # Set axis
    if sorted_matches:
        min_start = min(m['ref_gene']['start'] for m in sorted_matches)
        max_end = max(m['ref_gene']['end'] for m in sorted_matches)
        ax.set_xlim(min_start - 10000, max_end + 10000)
        ax.set_ylim(-len(sorted_matches) * track_spacing, 1)
    
    ax.set_xlabel('Genomic Position', fontsize=12, fontweight='bold')
    ax.set_ylabel('Gene Matches', fontsize=12, fontweight='bold')
    ax.set_title(f'Gene Match Overview ({len(matches)} matches found)', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor=ref_color, label='Reference', alpha=0.7),
        mpatches.Patch(facecolor=pred_color, label='Predicted', alpha=0.7),
        mpatches.Patch(facecolor=overlap_color, label='Overlap'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    ax.grid(axis='x', alpha=0.3, linestyle=':', linewidth=0.5)
    plt.tight_layout()
    return fig

