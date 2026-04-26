# Change Report — Paper 1: `alfa_yohannis_1.tex`
**postgre-vs-mongodb-image-time-series**

## Summary of Changes

| # | Review Point | Status | Lines Affected |
|---|---|---|---|
| 1 | Missing storage hardware spec | ✅ Fixed | L97 |
| 2 | Workload realism | ✅ Fixed | L277 (Threats) |
| 3 | Batch size sensitivity | ✅ Fixed | L277 (Threats) |
| 4 | Run variance / 5 runs | ✅ Fixed | L144 (Experiment Design) |
| 5 | Formatting & unit consistency | ✅ Fixed | L54 (Abstract), L233, L286 |
| 6 | Scope justification | N/A | Applies to Papers 2, 4 only |
| 7 | Representative data example | N/A | Paper 1 already has schema listings |
| 8 | Scalability discussion | ⚠️ Partial | Addressed via future work (L290) |
| 9 | Additional references | ⚠️ Deferred | Requires author to identify new citations |
| 10 | Raw data size baseline | ✅ Fixed | L187–200 (Storage table) |
| 11 | Cross-paper similarity | ⚠️ Deferred | Paper 1 is the "original"; other papers need rewriting |
| 12 | Configuration fairness | ✅ Fixed | L277 (Threats — cache typo 2GB→30GB) |
| 13 | Include all tested resolutions | ⚠️ Partial | Text already notes 360p–720p tested; no data to add rows |
| 14 | Future work directions | ✅ Fixed | L290 (Conclusions) |
| 15 | Pages and abstract limit | ✅ Fixed | Abstract trimmed to ~145 words |

---

## Detailed Changes

### 1. Abstract (Line 54) — Points 5, 15
- **Trimmed** from ~170 words to ~145 words (target: ~150).
- **Fixed multiplier formatting**: `0.1 times` → `$0.10\times$`, `3 times` → `$3.00\times$`, `1.04 times` → `$1.04\times$`.

### 2. Environment and Configuration (Line 97) — Point 1
- **Added** NVMe SSD specification: `and a 1.9~TB Samsung MZVL22T0HBLB-00BH1 NVMe SSD`.

### 3. Experiment Design (Line 144) — Point 4
- **Added** sentence noting that boxplot figures display IQR and median, and that observed variance was low, supporting the adequacy of 5 runs.

### 4. Storage Amplification Table (Lines 187–200) — Point 10
- **Added** `Raw (MB)` column showing the total logical payload size for each resolution, computed as `Disk Size / Amplification`.
- **Added** footnote explaining the derivation.
- Values: 1080p=1607, 1440p=2796, 4K=5973, 5K=10149, 6K=14232 MB.

### 5. Binary Retrieval Latency Section (Line 233) — Point 5
- **Converted** all time values from seconds to milliseconds to match the table units:
  - `2.5 s` → `2,542 ms`, `6.6 s` → `6,618 ms`
  - `10.2 s` → `10,218 ms`, `25.8 s` → `25,883 ms`
  - `29.5 s` → `29,534 ms`, `48.5 s` → `48,575 ms`
  - `68.5 s` → `68,568 ms`

### 6. WiredTiger Discussion (Line 255) — Data correction
- **Fixed stale throughput values** that did not match Table 1:
  - `133.2 rows/s` → `329.5 rows/s` (MongoDB at 1080p)
  - `4.6 rows/s` → `17.8 rows/s` (MongoDB at 4K)

### 7. Threats to Validity (Line 277) — Points 2, 3, 12
- **Fixed cache size typo**: `2 GB` → `30 GB` (matching the methodology section).
- **Added** justification that PostgreSQL operates under equivalent memory via OS-level page caching.
- **Added** note that alternative batch sizes could shift the crossover point.
- **Added** fifth threat: sequential single-client access; concurrent multi-client workloads, mixed read/write patterns, and diverse query types were not evaluated.

### 8. RQ2 Conclusion (Line 286) — Point 5
- **Fixed** `binary execution` → `binary retrieval` (typo).
- **Converted** `29.5 s vs 48.5 s` → `29,534 ms vs 48,575 ms`.

### 9. Future Work (Line 290) — Point 14
- **Added** distributed multi-node deployments and PostgreSQL Large Objects (LO) as future work directions.
