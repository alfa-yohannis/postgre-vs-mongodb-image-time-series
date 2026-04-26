# Change Report — Paper 4: `alfa_yohannis_4.tex`
**postgre-vs-postgre-minio-carbon-footprint**

## Summary of Changes

| # | Review Point | Status | Lines Affected |
|---|---|---|---|
| 1 | Missing storage hardware spec | N/A | Already present (NVMe SSD in L65) |
| 2 | Workload realism | ✅ Fixed | Threats (new sentence) |
| 3 | Batch size sensitivity | ✅ Fixed | Threats (new sentence) |
| 4 | Run variance / 5 runs | ✅ Fixed | L70 (Environment/Workloads) |
| 5 | Formatting & unit consistency | N/A | Paper 4 already consistent |
| 6 | Scope justification | ✅ Fixed | New "Database selection rationale" paragraph |
| 7 | Representative data example | ✅ Fixed | L70 (sample row added) |
| 8 | Scalability discussion | ✅ Fixed | New "Scalability considerations" paragraph |
| 9 | Additional references | ⚠️ Deferred | Requires author to identify new citations |
| 10 | Raw data size baseline | N/A | Applies to Papers 1, 3 only |
| 11 | Cross-paper similarity | ⚠️ Deferred | Needs coordinated rewrite with Paper 2 |
| 12 | Configuration fairness | N/A | Applies to Papers 1, 3 (MongoDB) only |
| 13 | Include all tested resolutions | N/A | Paper 1 only |
| 14 | Future work directions | ✅ Fixed | L206 (PostgreSQL LO added) |
| 15 | Pages and abstract limit | ✅ Fixed | Abstract trimmed to ~140 words |

---

## Detailed Changes

### 1. Author Block (Lines 22–24)
- Replaced "[Hidden for double-blind review]" with comma-separated IEEE format.

### 2. Abstract (Lines 29–31) — Point 15
- **Trimmed** from ~200 words to ~140 words by removing verbose phrasing.

### 3. Environment and Workloads (Line 70) — Points 4, 7
- **Added** variance note: boxplots show IQR/median, variance was low across all runs.
- **Added** representative sample row for PG and PM at 1080p with concrete field values.

### 4. New Paragraph: Database Selection Rationale — Point 6
- Justifies PostgreSQL as sole relational baseline (TimescaleDB exclusivity).
- Notes transferability of inline-vs-externalized trade-off to other engines.

### 5. New Paragraph: Scalability Considerations — Point 8
- Discusses expected behaviour at larger scales (TOAST growth, WAL volume, MinIO scale-out).

### 6. Threats to Validity — Points 2, 3
- **Added** batch-size sensitivity note (could shift carbon crossover).
- **Added** sequential single-client limitation; mixed workloads untested.

### 7. Future Work (Line 206) — Point 14
- **Added** PostgreSQL Large Objects (LO) as alternative architecture to investigate.

### 8. Acknowledgment (Lines 208–209)
- Replaced "[Hidden for double-blind review]" with both universities.
