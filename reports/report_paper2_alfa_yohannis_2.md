# Change Report — Paper 2: `alfa_yohannis_2.tex`
**postgre-vs-postgre-minio-image-time-series**

## Summary of Changes

| # | Review Point | Status | Lines Affected |
|---|---|---|---|
| 1 | Missing storage hardware spec | N/A | Already present (NVMe SSD in L95) |
| 2 | Workload realism | ✅ Fixed | Threats (7th threat added) |
| 3 | Batch size sensitivity | ✅ Fixed | Threats (4th threat expanded) |
| 4 | Run variance / 5 runs | ✅ Fixed | Experiment Design (L136) |
| 5 | Formatting & unit consistency | N/A | Paper 2 already consistent |
| 6 | Scope justification | ✅ Fixed | New "Database Selection Rationale" subsection |
| 7 | Representative data example | ✅ Fixed | Experiment Design (sample row added) |
| 8 | Scalability discussion | ✅ Fixed | New "Scalability Considerations" subsection |
| 9 | Additional references | ⚠️ Deferred | Requires author to identify new citations |
| 10 | Raw data size baseline | N/A | Applies to Papers 1, 3 only |
| 11 | Cross-paper similarity | ⚠️ Deferred | Needs coordinated rewrite with Paper 4 |
| 12 | Configuration fairness | N/A | Applies to Papers 1, 3 (MongoDB) only |
| 13 | Include all tested resolutions | N/A | Paper 2 already includes all 7 resolutions |
| 14 | Future work directions | N/A | Already comprehensive (LO, distributed, GPU) |
| 15 | Pages and abstract limit | ✅ Fixed | Abstract trimmed to ~140 words |

---

## Detailed Changes

### 1. Author Block (Lines 44–46)
- Replaced "[Hidden for double-blind review]" with comma-separated IEEE format listing all 5 authors with superscript affiliations.

### 2. Abstract (Lines 51–53) — Point 15
- **Trimmed** from ~170 words to ~140 words by removing filler phrases and tightening notation.

### 3. Experiment Design (Line 136) — Points 4, 7
- **Added** sentence noting boxplots display IQR/median and that variance was low across all runs.
- **Added** representative sample row for both PG and PM architectures at 1080p, showing concrete field values.

### 4. New Subsection: Database Selection Rationale — Point 6
- **Added** after "Resolution-Dependent Crossover" subsection.
- Justifies PostgreSQL as the sole relational baseline (TimescaleDB exclusivity).
- Notes that the inline-vs-externalized trade-off is conceptually transferable to other engines.

### 5. New Subsection: Scalability Considerations — Point 8
- **Added** paragraph discussing expected behaviour at larger scales.
- Notes WAL growth for PG, MinIO's horizontal scale-out design, and leaves confirmation to future work.

### 6. Threats to Validity — Points 2, 3
- **Expanded** 4th threat: batch size could shift the write-side crossover.
- **Added** 7th threat: sequential single-client only; mixed R/W and diverse queries untested.

### 7. Acknowledgment (Line 306)
- Replaced "[Hidden for double-blind review]" with acknowledgment text.
