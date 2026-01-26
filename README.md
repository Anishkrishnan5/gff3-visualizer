# GFF3 Structure Visualizer & Comparator

## Overview

This project is a lightweight tool for **visualizing and comparing gene structures encoded in GFF3 files**, with a focus on **debugging gene prediction models**.

In genomics research, predicted gene structures are typically evaluated against reference annotations stored in GFF3 format. While GFF3 is expressive, it is difficult to reason about differences directly from raw files—especially when comparing exon boundaries, alternative splicing, or partial overlaps.

This tool parses GFF3 annotations into a hierarchical model (**gene → transcript → exon/CDS**), compares **predicted vs ground-truth gene structures**, and renders a clear visual representation of their structural differences.

This tool deliberately focuses on **single-gene or localized region analysis** to prioritize interpretability and correctness over genome-scale complexity.

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

## Motivation

This tool was initially built to support research on **fine-tuning Tiberius, a deep learning-based model that can predict animal gene structure, to be able to support fungal gene structure prediction**.

Comparing predicted annotations to reference gene structures using raw GFF3 files proved slow and error-prone, motivating the need for a focused visualization and comparison tool designed specifically for **model debugging and error analysis**.

---

## Design Philosophy

- **Deliberately constrained scope** for clarity and correctness
- **Separation of concerns** between parsing, comparison logic, and visualization
- **Human interpretability first**: visuals over tables, structure over aggregate metrics
- **Extensible architecture** to support future evaluation and batch analysis

---

## Tech Stack

### Backend
- Python
- FastAPI
- Custom GFF3 parsing and comparison logic

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
│   │   ├── main.py              # FastAPI entry point
│   │   ├── api/
│   │   │   └── routes.py        # API endpoints
│   │   ├── parsing/
│   │   │   ├── gff3_parser.py   # GFF3 parsing logic
│   │   │   └── models.py        # Gene / Transcript / Exon classes
│   │   ├── comparison/
│   │   │   ├── align.py         # Transcript matching logic
│   │   │   └── metrics.py       # Overlap / comparison metrics
│   │   ├── schemas/
│   │   │   └── response.py      # API response schemas
│   │   └── utils/
│   │       └── helpers.py       # Shared utilities
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── index.html               # Main UI
│   ├── styles.css               # Minimal styling
│   ├── app.js                   # Frontend logic / API calls
│   └── viz/
│       └── geneViz.js           # D3 visualization logic
│
├── data/
│   └── examples/
│       ├── reference.gff3
│       └── predicted.gff3
│
├── README.md
└── .gitignore
