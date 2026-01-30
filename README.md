# GFF3 Structure Visualizer & Comparator

## Overview

This project is a tool for **visualizing and comparing gene structures encoded in GFF3 files**, with a focus on **debugging gene prediction models**.

In genomics research, predicted gene structures are typically evaluated against reference annotations stored in GFF3 format. While GFF3 is expressive, it is difficult to reason about differences directly from raw files—especially when comparing exon boundaries, alternative splicing, or partial overlaps.

This tool parses GFF3 annotations into a hierarchical model (**gene → transcript → exon/CDS**), compares **predicted vs ground-truth gene structures**, and renders a clear visual representation of their structural differences.

---

## Key Features

### GFF3 Parsing
- Supports `gene`, `mRNA` / `transcript`, `exon`, and `CDS` features
- Reconstructs hierarchical relationships using `ID` and `Parent` attributes
- Normalizes and sorts features independently of file order

### Structural Comparison
- Aligns predicted transcripts to reference transcripts using exon-overlap heuristics
- Identifies:
  - missing exons
  - extra exons
  - partially overlapping exons
- Computes simple overlap metrics to highlight structural disagreement

### Visualization
- Gene-level visualization using genomic coordinates
- Stacked transcript views
- Color-coded exon intervals:
  - ground truth
  - predicted
  - overlapping regions
- Strand direction displayed for biological context

### Web-Based Interface
- Upload reference and predicted GFF3 files
- Select a gene ID or coordinate range
- Render data-driven visualizations using **D3.js**

---

## Tech Stack

### Backend
- Python
- FastAPI
- 
### Frontend
- HTML / CSS
- D3.js for data-driven visualization

---

## Project Structure

```text
gff3-visualizer/
│
├── backend/
│   ├── app/
│   │   ├── main.py              
│   │   ├── api/
│   │   │   └── routes.py
│   │   ├── parsing/
│   │   │   ├── gff3_parser.py
│   │   │   └── models.py
│   │   ├── comparison/
│   │   │   ├── align.py
│   │   │   └── metrics.py
│   │   ├── schemas/
│   │   │   └── response.py
│   │   └── utils/
│   │       └── helpers.py
│   │
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── viz/
│       └── geneViz.js
│
├── data/
│   └── examples/
│       ├── reference.gff3
│       └── predicted.gff3
│
├── .gitignore
└── README.md
