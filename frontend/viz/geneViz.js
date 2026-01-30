/**
 * GFF3 Gene Structure Visualizer
 * 
 * Visual Grammar:
 * - X-axis: genomic coordinate (bp), linear scale
 * - Y-axis: one row per transcript
 *   - Reference transcripts on top
 *   - Predicted transcripts below
 * - Rectangles: exon = rectangle
 *   - width = end - start
 *   - x = start
 * - Colors (simple and loud):
 *   - matched → green
 *   - partial → orange
 *   - missing → red
 *   - extra → purple
 * 
 * This is NOT a genome browser.
 * This is a whiteboard for debugging one gene at a time.
 * No zooming. No panning. Just coordinates → rectangles.
 */

function renderGene(data) {
    const svg = d3.select("#viz");
    svg.selectAll("*").remove();

    if (!data || !data.comparisons || data.comparisons.length === 0) {
        svg.append("text")
            .attr("x", 600)
            .attr("y", 300)
            .attr("text-anchor", "middle")
            .text("No comparison data available");
        return;
    }

    const margin = { top: 60, left: 120, right: 40, bottom: 80 };
    const width = 1200 - margin.left - margin.right;
    const height = Math.max(400, data.comparisons.length * 60 + 100) - margin.top - margin.bottom;

    svg.attr("width", width + margin.left + margin.right)
       .attr("height", height + margin.top + margin.bottom);

    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    // Step 6: Compute coordinate scale
    const allExons = [];
    data.comparisons.forEach(comp => {
        if (comp.matched) {
            comp.matched.forEach(m => {
                if (m.ref) allExons.push({ start: m.ref.start, end: m.ref.end });
                if (m.pred) allExons.push({ start: m.pred.start, end: m.pred.end });
            });
        }
        if (comp.partial) {
            comp.partial.forEach(p => {
                if (p.ref) allExons.push({ start: p.ref.start, end: p.ref.end });
                if (p.pred) allExons.push({ start: p.pred.start, end: p.pred.end });
            });
        }
        if (comp.missing) {
            comp.missing.forEach(m => allExons.push({ start: m.start, end: m.end }));
        }
        if (comp.extra) {
            comp.extra.forEach(e => allExons.push({ start: e.start, end: e.end }));
        }
    });

    if (allExons.length === 0) {
        g.append("text")
            .attr("x", width / 2)
            .attr("y", height / 2)
            .attr("text-anchor", "middle")
            .text("No exon data found");
        return;
    }

    const minCoord = d3.min(allExons, d => d.start);
    const maxCoord = d3.max(allExons, d => d.end);
    const padding = (maxCoord - minCoord) * 0.05;

    const xScale = d3.scaleLinear()
        .domain([minCoord - padding, maxCoord + padding])
        .range([0, width]);

    // Step 7: Draw transcript rows
    const rowHeight = 35;
    const rowSpacing = 60;

    // Color map
    const colorMap = {
        matched: "#50c878",    // green
        partial: "#f5a623",    // orange
        missing: "#e74c3c",     // red
        extra: "#9b59b6"        // purple
    };

    data.comparisons.forEach((comp, i) => {
        const y = i * rowSpacing;

        // Label transcript
        const isRef = i === 0 || comp.reference_transcript;
        g.append("text")
            .attr("x", -15)
            .attr("y", y + rowHeight / 2)
            .attr("text-anchor", "end")
            .attr("font-size", "12px")
            .attr("font-weight", "bold")
            .text(isRef ? `Ref: ${comp.reference_transcript || 'Reference'}` : `Pred: ${comp.predicted_transcript || 'Predicted'}`);

        // Draw connecting line for transcript span
        let transcriptStart = Infinity;
        let transcriptEnd = -Infinity;
        
        if (comp.matched) {
            comp.matched.forEach(m => {
                if (m.ref) {
                    transcriptStart = Math.min(transcriptStart, m.ref.start);
                    transcriptEnd = Math.max(transcriptEnd, m.ref.end);
                }
                if (m.pred) {
                    transcriptStart = Math.min(transcriptStart, m.pred.start);
                    transcriptEnd = Math.max(transcriptEnd, m.pred.end);
                }
            });
        }
        if (comp.partial) {
            comp.partial.forEach(p => {
                if (p.ref) {
                    transcriptStart = Math.min(transcriptStart, p.ref.start);
                    transcriptEnd = Math.max(transcriptEnd, p.ref.end);
                }
                if (p.pred) {
                    transcriptStart = Math.min(transcriptStart, p.pred.start);
                    transcriptEnd = Math.max(transcriptEnd, p.pred.end);
                }
            });
        }
        if (comp.missing) {
            comp.missing.forEach(m => {
                transcriptStart = Math.min(transcriptStart, m.start);
                transcriptEnd = Math.max(transcriptEnd, m.end);
            });
        }
        if (comp.extra) {
            comp.extra.forEach(e => {
                transcriptStart = Math.min(transcriptStart, e.start);
                transcriptEnd = Math.max(transcriptEnd, e.end);
            });
        }

        if (transcriptStart !== Infinity && transcriptEnd !== -Infinity) {
            g.append("line")
                .attr("x1", xScale(transcriptStart))
                .attr("x2", xScale(transcriptEnd))
                .attr("y1", y + rowHeight / 2)
                .attr("y2", y + rowHeight / 2)
                .attr("stroke", "#999")
                .attr("stroke-width", 1)
                .attr("stroke-dasharray", "3,3")
                .attr("opacity", 0.5);
        }

        // Step 8: Draw exons as rectangles
        // Draw matched exons (green) - reference row
        if (comp.matched) {
            comp.matched.forEach(m => {
                if (m.ref) {
                    const width = xScale(m.ref.end) - xScale(m.ref.start);
                    g.append("rect")
                        .attr("x", xScale(m.ref.start))
                        .attr("y", y)
                        .attr("width", Math.max(width, 2))
                        .attr("height", rowHeight * 0.5)
                        .attr("fill", colorMap.matched)
                        .attr("opacity", 0.9)
                        .attr("stroke", "#2d7a4d")
                        .attr("stroke-width", 1.5);
                }
            });
        }

        // Draw partial overlaps (orange) - reference row
        if (comp.partial) {
            comp.partial.forEach(p => {
                if (p.ref) {
                    const width = xScale(p.ref.end) - xScale(p.ref.start);
                    g.append("rect")
                        .attr("x", xScale(p.ref.start))
                        .attr("y", y)
                        .attr("width", Math.max(width, 2))
                        .attr("height", rowHeight * 0.5)
                        .attr("fill", colorMap.partial)
                        .attr("opacity", 0.9)
                        .attr("stroke", "#cc8500")
                        .attr("stroke-width", 1.5);
                }
            });
        }

        // Draw missing exons (red) - reference row
        if (comp.missing) {
            comp.missing.forEach(m => {
                const width = xScale(m.end) - xScale(m.start);
                g.append("rect")
                    .attr("x", xScale(m.start))
                    .attr("y", y)
                    .attr("width", Math.max(width, 2))
                    .attr("height", rowHeight * 0.5)
                    .attr("fill", colorMap.missing)
                    .attr("opacity", 0.9)
                    .attr("stroke", "#c0392b")
                    .attr("stroke-width", 1.5)
                    .attr("stroke-dasharray", "4,2");
            });
        }

        // Draw matched exons (green) - predicted row (slightly offset)
        if (comp.matched) {
            comp.matched.forEach(m => {
                if (m.pred) {
                    const width = xScale(m.pred.end) - xScale(m.pred.start);
                    g.append("rect")
                        .attr("x", xScale(m.pred.start))
                        .attr("y", y + rowHeight * 0.5)
                        .attr("width", Math.max(width, 2))
                        .attr("height", rowHeight * 0.5)
                        .attr("fill", colorMap.matched)
                        .attr("opacity", 0.9)
                        .attr("stroke", "#2d7a4d")
                        .attr("stroke-width", 1.5);
                }
            });
        }

        // Draw partial overlaps (orange) - predicted row
        if (comp.partial) {
            comp.partial.forEach(p => {
                if (p.pred) {
                    const width = xScale(p.pred.end) - xScale(p.pred.start);
                    g.append("rect")
                        .attr("x", xScale(p.pred.start))
                        .attr("y", y + rowHeight * 0.5)
                        .attr("width", Math.max(width, 2))
                        .attr("height", rowHeight * 0.5)
                        .attr("fill", colorMap.partial)
                        .attr("opacity", 0.9)
                        .attr("stroke", "#cc8500")
                        .attr("stroke-width", 1.5);
                }
            });
        }

        // Draw extra exons (purple) - predicted row
        if (comp.extra) {
            comp.extra.forEach(e => {
                const width = xScale(e.end) - xScale(e.start);
                g.append("rect")
                    .attr("x", xScale(e.start))
                    .attr("y", y + rowHeight * 0.5)
                    .attr("width", Math.max(width, 2))
                    .attr("height", rowHeight * 0.5)
                    .attr("fill", colorMap.extra)
                    .attr("opacity", 0.9)
                    .attr("stroke", "#7d3c98")
                    .attr("stroke-width", 1.5)
                    .attr("stroke-dasharray", "4,2");
            });
        }
    });

    // Step 9: Add x-axis
    const xAxis = d3.axisBottom(xScale)
        .ticks(10)
        .tickFormat(d => d.toLocaleString());

    g.append("g")
        .attr("transform", `translate(0, ${data.comparisons.length * rowSpacing})`)
        .call(xAxis)
        .selectAll("text")
        .attr("font-size", "10px");

    // X-axis label
    g.append("text")
        .attr("x", width / 2)
        .attr("y", data.comparisons.length * rowSpacing + 60)
        .attr("text-anchor", "middle")
        .attr("font-size", "13px")
        .attr("font-weight", "bold")
        .text("Genomic Position (bp)");

    // Legend
    const legendY = data.comparisons.length * rowSpacing + 20;
    const legendX = width - 180;
    const legendItems = [
        { color: colorMap.matched, label: "Matched" },
        { color: colorMap.partial, label: "Partial" },
        { color: colorMap.missing, label: "Missing" },
        { color: colorMap.extra, label: "Extra" }
    ];

    legendItems.forEach((item, i) => {
        const legendYPos = legendY + i * 20;
        g.append("rect")
            .attr("x", legendX)
            .attr("y", legendYPos)
            .attr("width", 15)
            .attr("height", 15)
            .attr("fill", item.color)
            .attr("opacity", 0.9)
            .attr("stroke", "#333")
            .attr("stroke-width", 1);

        g.append("text")
            .attr("x", legendX + 20)
            .attr("y", legendYPos + 12)
            .attr("font-size", "11px")
            .text(item.label);
    });
}
