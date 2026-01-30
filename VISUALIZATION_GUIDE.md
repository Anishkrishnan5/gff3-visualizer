# Automatic Visualization Guide

## What's New

The tool now **automatically generates visual comparisons** when you upload files! No more clicking through genes one by one - you'll see:

1. **Overview Visualization** - Shows all matched genes at once
2. **Detailed Comparisons** - Automatically generated for each matched gene pair
3. **Matplotlib Backend** - Generates high-quality static images

## How It Works

### Step-by-Step Workflow

1. **Upload Files**
   - Upload reference GFF3 file
   - Upload predicted GFF3 file
   - Click "Parse Files"

2. **Automatic Processing**
   - System finds genes that match by genomic coordinates
   - Generates overview visualization showing all matches
   - Automatically creates detailed visualizations for each match

3. **View Results**
   - **Overview**: See all matches at a glance (blue=reference, orange=predicted, green=overlap)
   - **Detailed Views**: Scroll down to see individual gene comparisons
   - **Interactive**: Click images to zoom, use dropdown to select specific genes

## Features

### Overview Visualization
- Shows all matched genes on a single plot
- Color-coded by type (reference, predicted, overlap)
- Sorted by genomic position
- Shows overlap percentages

### Detailed Gene Comparisons
- Side-by-side transcript views
- Color-coded exons:
  - **Blue** = Reference exons
  - **Orange** = Predicted exons  
  - **Green** = Overlapping regions
  - **Red** = Missing in predicted
  - **Yellow** = Extra in predicted
- Shows CDS vs non-CDS regions
- Includes comparison tracks

### Backend Visualization
- Uses **matplotlib** for high-quality static images
- Base64 encoded for easy display in browser
- Can be saved/downloaded as PNG

## API Endpoints

### `/api/find-matches`
Finds matching genes and optionally generates overview visualization.

**Parameters:**
- `ref_file`: Reference GFF3 file
- `pred_file`: Predicted GFF3 file
- `overlap_threshold`: Minimum overlap ratio (default: 0.5)
- `include_overview`: Generate overview image (default: false)

**Response:**
```json
{
  "matches": [...],
  "total_matches": 10,
  "overview_image": "base64_encoded_png..."
}
```

### `/api/visualize-gene`
Generates detailed visualization for a specific gene pair.

**Parameters:**
- `ref_file`: Reference GFF3 file
- `pred_file`: Predicted GFF3 file
- `ref_gene_id`: Reference gene ID
- `pred_gene_id`: Predicted gene ID

**Response:**
```json
{
  "ref_gene_id": "gene_10221",
  "pred_gene_id": "g1",
  "image": "base64_encoded_png...",
  "comparison_data": [...]
}
```

## Installation

Make sure to install the new dependencies:

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

This will install:
- `matplotlib` - For generating visualizations
- `numpy` - Required by matplotlib

## Usage Tips

1. **First 10 Matches**: Detailed visualizations are automatically generated for the first 10 matches to keep page load times reasonable. Use the dropdown to view specific genes beyond that.

2. **Image Zoom**: Click any detailed visualization image to zoom in/out.

3. **Overview First**: Always check the overview visualization first to get a sense of how well the predictions match the reference.

4. **Overlap Threshold**: Adjust the overlap threshold (currently 30%) if you want more or fewer matches. Lower = more matches, Higher = only very similar genes.

## Technical Details

### Visualization Generation
- Backend uses matplotlib to create publication-quality figures
- Images are base64 encoded and embedded directly in HTML
- No file storage needed - everything is in-memory

### Performance
- Overview generation: ~1-2 seconds for typical files
- Detailed visualization: ~0.5-1 second per gene
- First 10 genes are generated automatically
- Additional genes generated on-demand when selected

## Troubleshooting

**No visualizations appearing?**
- Check browser console for errors
- Verify backend is running and matplotlib is installed
- Check that files contain matching genes

**Images not loading?**
- Check network tab in browser dev tools
- Verify API endpoints are responding
- Check for CORS issues

**Slow generation?**
- Reduce number of matches by increasing overlap threshold
- Limit automatic generation to fewer genes (edit `generateAllGeneVisualizations()`)

