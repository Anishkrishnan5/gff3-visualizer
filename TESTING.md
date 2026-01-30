# Testing Guide for GFF3 Visualizer

## Prerequisites

1. **Python 3.8+** installed
2. **Virtual environment** (recommended)

## Step-by-Step Testing Instructions

### 1. Install Backend Dependencies

```bash
cd backend
python3 -m venv venv  # If not already created
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
cd backend
source venv/bin/activate  # If not already activated
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3. Test Backend API Endpoints

Open a **new terminal** and test the API:

#### Test 1: Check API is running
```bash
curl http://localhost:8000/api
```
Expected: `{"message":"GFF3 Visualizer API","version":"1.0.0"}`

#### Test 2: Parse a GFF3 file
```bash
curl -X POST "http://localhost:8000/api/parse" \
  -F "file=@../data/examples/Cylto1__FilteredModels1.gff3"
```
Expected: JSON with `genes` array and `gene_ids` list

#### Test 3: Get gene data (requires both files)
```bash
curl -X POST "http://localhost:8000/api/gene" \
  -F "ref_file=@../data/examples/Cylto1__FilteredModels1.gff3" \
  -F "pred_file=@../data/examples/Cylto1_predicted.gff3" \
  -F "gene_id=gene_10221"
```
Expected: JSON with `gene_id`, `reference`, and `predicted` gene data

**Note:** The gene IDs must exist in both files. Check available genes first.

### 4. Test Frontend

1. **Open browser** and navigate to: `http://localhost:8000`
2. You should see the GFF3 Visualizer interface

3. **Upload files:**
   - Click "Reference GFF3 File" → Select `data/examples/Cylto1__FilteredModels1.gff3`
   - Click "Predicted GFF3 File" → Select `data/examples/Cylto1_predicted.gff3`
   - Click "Parse Files"

4. **Select a gene:**
   - Choose a gene from the dropdown (only common genes will appear)
   - Click "Visualize"

5. **Verify visualization:**
   - Should see gene tracks with exons
   - Reference exons in blue
   - Predicted exons in orange
   - Overlapping regions in green
   - Missing/extra exons highlighted
   - Coordinate axis at the bottom
   - Strand indicator at the top

### 5. Test Interactive Features

- **Zoom:** Use mouse wheel or zoom buttons
- **Pan:** Click and drag
- **Tooltips:** Hover over exons to see details
- **Reset:** Click "Reset View" to return to original zoom

## Troubleshooting

### Backend won't start
- Check if port 8000 is already in use: `lsof -i :8000`
- Make sure dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python3 --version` (needs 3.8+)

### "No module named 'fastapi'"
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

### Frontend shows "Failed to fetch"
- Check backend is running on port 8000
- Check browser console for CORS errors
- Verify API_BASE in `frontend/app.js` matches your backend URL

### No genes found
- Make sure both files contain common gene IDs
- Check file format is valid GFF3
- Verify files uploaded correctly

### Visualization not showing
- Open browser developer console (F12)
- Check for JavaScript errors
- Verify D3.js is loaded (check Network tab)

## Expected File Structure

```
gff3-visualizer/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/routes.py
│   │   ├── parsing/
│   │   └── comparison/
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   └── viz/geneViz.js
└── data/examples/
    ├── Cylto1__FilteredModels1.gff3
    └── Cylto1_predicted.gff3
```

## Quick Test Script

Save this as `test_backend.sh`:

```bash
#!/bin/bash
echo "Testing GFF3 Visualizer Backend..."

# Test 1: API root
echo -e "\n1. Testing API root..."
curl -s http://localhost:8000/api | jq .

# Test 2: Parse reference file
echo -e "\n2. Testing parse endpoint..."
curl -s -X POST "http://localhost:8000/api/parse" \
  -F "file=@data/examples/Cylto1__FilteredModels1.gff3" | jq '.gene_ids | length'

echo -e "\n✓ Backend tests complete!"
```

Run with: `chmod +x test_backend.sh && ./test_backend.sh`

