// Global state
let geneMatches = [];
let comparisonData = {};

// Upload files and compare
document.getElementById("runBtn").onclick = async () => {
  const refFile = document.getElementById("refFile").files[0];
  const predFile = document.getElementById("predFile").files[0];

  if (!refFile || !predFile) {
    alert("Please select both files");
    return;
  }

  // Show loading state
  const btn = document.getElementById("runBtn");
  const loadingMsg = document.getElementById("loading-message");
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Processing...";
  loadingMsg.style.display = "block";

  try {
    console.log("Step 1: Finding matching genes...");
    
    // Find matching genes
    const matchFormData = new FormData();
    matchFormData.append("ref_file", refFile);
    matchFormData.append("pred_file", predFile);
    matchFormData.append("overlap_threshold", "0.3");

    const matchResponse = await fetch("http://localhost:8000/api/find-matches", {
      method: "POST",
      body: matchFormData
    });

    if (!matchResponse.ok) {
      const errorData = await matchResponse.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${matchResponse.status}: Failed to find gene matches`);
    }

    const matchData = await matchResponse.json();
    console.log("Match data received:", matchData);
    geneMatches = matchData.matches || [];

    if (geneMatches.length === 0) {
      alert("No matching genes found between the two files");
      btn.disabled = false;
      btn.textContent = originalText;
      return;
    }

    console.log(`Found ${geneMatches.length} matching genes`);

    // Get detailed comparison for each gene
    console.log("Step 2: Loading detailed comparisons...");
    await loadAllComparisons(refFile, predFile);

    console.log("Step 3: Categorizing genes...");
    // Categorize and display
    categorizeAndDisplay();

    console.log("Done!");

  } catch (error) {
    console.error("Error details:", error);
    alert(`Error: ${error.message}\n\nCheck browser console for details.`);
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
    loadingMsg.style.display = "none";
  }
};

// Load comparison data for all matched genes
async function loadAllComparisons(refFile, predFile) {
  comparisonData = {};
  
  // The /api/compare endpoint expects the gene_id to exist in BOTH files
  // But we have different IDs, so we need to use a different approach
  // Let's parse both files and get the actual gene data, then compare manually
  
  console.log(`Loading comparisons for ${geneMatches.length} genes...`);
  
  for (let i = 0; i < geneMatches.length; i++) {
    const match = geneMatches[i];
    try {
      // Use the new endpoint that accepts both gene IDs
      const formData = new FormData();
      formData.append("ref_file", refFile);
      formData.append("pred_file", predFile);
      formData.append("ref_gene_id", match.ref_gene_id);
      formData.append("pred_gene_id", match.pred_gene_id);

      const response = await fetch("http://localhost:8000/api/compare-genes", {
        method: "POST",
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        comparisonData[match.ref_gene_id] = {
          ...data,
          pred_gene_id: match.pred_gene_id,
          overlap_ratio: match.overlap_ratio
        };
        console.log(`Loaded comparison ${i+1}/${geneMatches.length}: ${match.ref_gene_id} ↔ ${match.pred_gene_id}`);
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.warn(`Failed to compare ${match.ref_gene_id} ↔ ${match.pred_gene_id}:`, errorData.error || response.status);
        // Create empty comparison so we don't skip it
        comparisonData[match.ref_gene_id] = {
          gene_id: match.ref_gene_id,
          comparisons: [],
          pred_gene_id: match.pred_gene_id,
          overlap_ratio: match.overlap_ratio
        };
      }
    } catch (err) {
      console.error(`Error comparing ${match.ref_gene_id}:`, err);
      // Create empty comparison
      comparisonData[match.ref_gene_id] = {
        gene_id: match.ref_gene_id,
        comparisons: [],
        pred_gene_id: match.pred_gene_id,
        overlap_ratio: match.overlap_ratio
      };
    }
  }
  
  console.log(`Loaded ${Object.keys(comparisonData).length} comparisons`);
}

// Categorize genes and calculate statistics
function categorizeAndDisplay() {
  const SIGNIFICANT_THRESHOLD = 0.30; // 30% non-overlap = significant difference
  const REASONABLE_THRESHOLD = 0.30; // <30% non-overlap = reasonable

  const perfect = [];
  const reasonable = [];
  const significant = [];

  let totalOverlap = 0;
  let totalGenes = 0;

  geneMatches.forEach(match => {
    const comp = comparisonData[match.ref_gene_id];
    if (!comp) {
      console.warn(`No comparison data for ${match.ref_gene_id}`);
      return;
    }

    // Use the overlap ratio from the match if available, otherwise calculate
    let overlapRatio = match.overlap_ratio || 0;
    let nonOverlapRatio = 1 - overlapRatio;

    // If we have comparison data, calculate more precisely
    if (comp.comparisons && comp.comparisons.length > 0) {
      const totalRefBp = calculateTotalBp(comp.comparisons, 'ref');
      const totalPredBp = calculateTotalBp(comp.comparisons, 'pred');
      const matchedBp = calculateMatchedBp(comp.comparisons);
      const totalBp = Math.max(totalRefBp, totalPredBp);
      
      if (totalBp > 0) {
        overlapRatio = matchedBp / totalBp;
        nonOverlapRatio = 1 - overlapRatio;
      }
    }

    totalOverlap += overlapRatio;
    totalGenes++;

    const geneInfo = {
      ref_id: match.ref_gene_id,
      pred_id: match.pred_gene_id,
      overlap_ratio: overlapRatio,
      non_overlap_ratio: nonOverlapRatio,
      comparison: comp
    };

    if (nonOverlapRatio === 0) {
      perfect.push(geneInfo);
    } else if (nonOverlapRatio < SIGNIFICANT_THRESHOLD) {
      reasonable.push(geneInfo);
    } else {
      significant.push(geneInfo);
    }
  });

  if (totalGenes === 0) {
    console.error("No genes with comparison data found!");
    alert("No comparison data could be loaded. Check console for details.");
    return;
  }

  // Display statistics
  displayStatistics(totalGenes, totalOverlap / totalGenes, perfect.length, significant.length);

  // Populate dropdowns
  populateDropdown("perfect-select", perfect, "perfect");
  populateDropdown("reasonable-select", reasonable, "reasonable");
  populateDropdown("significant-select", significant, "significant");

  // Update counts
  document.getElementById("perfect-count").textContent = perfect.length;
  document.getElementById("reasonable-count").textContent = reasonable.length;
  document.getElementById("significant-count").textContent = significant.length;

  // Show sections
  document.getElementById("stats-section").style.display = "block";
  document.getElementById("gene-categories").style.display = "block";
}

// Calculate total base pairs for reference or predicted
function calculateTotalBp(comparisons, type) {
  let total = 0;
  comparisons.forEach(comp => {
    if (type === 'ref') {
      if (comp.matched) comp.matched.forEach(m => {
        if (m.ref) total += m.ref.end - m.ref.start + 1;
      });
      if (comp.partial) comp.partial.forEach(p => {
        if (p.ref) total += p.ref.end - p.ref.start + 1;
      });
      if (comp.missing) comp.missing.forEach(m => total += m.end - m.start + 1);
    } else {
      if (comp.matched) comp.matched.forEach(m => {
        if (m.pred) total += m.pred.end - m.pred.start + 1;
      });
      if (comp.partial) comp.partial.forEach(p => {
        if (p.pred) total += p.pred.end - p.pred.start + 1;
      });
      if (comp.extra) comp.extra.forEach(e => total += e.end - e.start + 1);
    }
  });
  return total;
}

// Calculate matched base pairs
function calculateMatchedBp(comparisons) {
  let matched = 0;
  comparisons.forEach(comp => {
    if (comp.matched) {
      comp.matched.forEach(m => {
        if (m.ref && m.pred) {
          const overlapStart = Math.max(m.ref.start, m.pred.start);
          const overlapEnd = Math.min(m.ref.end, m.pred.end);
          if (overlapStart <= overlapEnd) {
            matched += overlapEnd - overlapStart + 1;
          }
        }
      });
    }
    if (comp.partial) {
      comp.partial.forEach(p => {
        if (p.ref && p.pred) {
          const overlapStart = Math.max(p.ref.start, p.pred.start);
          const overlapEnd = Math.min(p.ref.end, p.pred.end);
          if (overlapStart <= overlapEnd) {
            matched += overlapEnd - overlapStart + 1;
          }
        }
      });
    }
  });
  return matched;
}

// Display statistics
function displayStatistics(total, avgOverlap, perfect, significant) {
  document.getElementById("total-matches").textContent = total;
  document.getElementById("avg-overlap").textContent = (avgOverlap * 100).toFixed(1) + "%";
  document.getElementById("perfect-matches").textContent = perfect;
  document.getElementById("significant-diffs").textContent = significant;
}

// Populate dropdown
function populateDropdown(selectId, genes, category) {
  const select = document.getElementById(selectId);
  select.innerHTML = '<option value="">-- Select a gene --</option>';
  
  genes.forEach((gene, idx) => {
    const option = document.createElement("option");
    option.value = idx;
    option.textContent = `${gene.ref_id} ↔ ${gene.pred_id} (${(gene.overlap_ratio * 100).toFixed(1)}% overlap)`;
    option.dataset.geneInfo = JSON.stringify(gene);
    select.appendChild(option);
  });

  // Add event listener
  select.onchange = function() {
    if (this.value !== "") {
      const geneInfo = JSON.parse(this.options[this.selectedIndex].dataset.geneInfo);
      displayGeneComparison(geneInfo);
    }
  };
}

// Display gene comparison visualization
function displayGeneComparison(geneInfo) {
  document.getElementById("selected-gene-title").textContent = 
    `Gene Comparison: ${geneInfo.ref_id} ↔ ${geneInfo.pred_id}`;
  
  // Display gene info
  const infoDiv = document.getElementById("gene-info");
  infoDiv.innerHTML = `
    <div class="info-grid">
      <div><strong>Overlap:</strong> ${(geneInfo.overlap_ratio * 100).toFixed(1)}%</div>
      <div><strong>Non-overlap:</strong> ${(geneInfo.non_overlap_ratio * 100).toFixed(1)}%</div>
      <div><strong>Status:</strong> ${
        geneInfo.non_overlap_ratio === 0 ? "Perfect Match" :
        geneInfo.non_overlap_ratio < 0.30 ? "Reasonable Overlap" :
        "Significant Difference"
      }</div>
    </div>
  `;

  // Render visualization
  renderGene(geneInfo.comparison);
  document.getElementById("visualization-section").style.display = "block";
}
