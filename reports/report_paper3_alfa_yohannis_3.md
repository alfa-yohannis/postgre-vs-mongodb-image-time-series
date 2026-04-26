# Change Report — Paper 3: `alfa_yohannis_3.tex`
**postgre-vs-mongodb-carbon-footprint**

## Summary of Changes

| # | Review Point | Status | Lines Affected |
|---|---|---|---|
| 1 | Missing storage hardware spec | ✅ Fixed | L68 (Hardware section) |
| 2 | Workload realism | ✅ Fixed | Threats (new sentences) |
| 3 | Batch size sensitivity | ✅ Fixed | Threats (new sentence) |
| 4 | Run variance / 5 runs | ✅ Fixed | L97 (Schema/Operations) |
| 5 | Formatting & unit consistency | N/A | Paper 3 already uses ms in tables consistently |
| 6 | Scope justification | N/A | Applies to Papers 2, 4 only |
| 7 | Representative data example | N/A | Applies to Papers 2, 4 only |
| 8 | Scalability discussion | N/A | Already present ("Scale-up indication" subsection) |
| 9 | Additional references | ⚠️ Deferred | Requires author to identify new citations |
| 10 | Raw data size baseline | ✅ Fixed | Performance table (Raw column added) |
| 11 | Cross-paper similarity | ⚠️ Deferred | Needs coordinated rewrite with Paper 1 |
| 12 | Configuration fairness | ✅ Fixed | Threats (cache justification added) |
| 13 | Include all tested resolutions | N/A | Paper 1 only |
| 14 | Future work directions | ✅ Fixed | L213 (LO + distributed added) |
| 15 | Pages and abstract limit | N/A | Abstract already ~150 words |

---

## Detailed Changes

### 1. Author Block (Lines 24–26)
- Replaced "[Hidden for double-blind review]" with comma-separated IEEE format.

### 2. Hardware Environment (Line 68) — Point 1
- **Added** `and a 1.9~TB Samsung MZVL22T0HBLB-00BH1 NVMe SSD` to the hardware spec.

### 3. Schema and Operations (Line 97) — Point 4
- **Added** sentence noting boxplots display IQR/median and variance was low across runs.

### 4. Performance Table (Lines 106–119) — Point 10
- **Added** `Raw (MB)` column: 1080p=1600, 1440p=2800, 4K=5980, 5K=10180 MB.
- **Added** footnote explaining Raw derivation.

### 5. Threats to Validity (Line 202) — Points 2, 3, 12
- **Added** batch-size sensitivity note (could shift carbon crossover).
- **Added** cache configuration fairness: 30 GB WiredTiger cache justified; PG uses OS-level caching equivalently.
- **Added** sequential single-client limitation; mixed workloads untested.

### 6. Future Work (Line 213) — Point 14
- **Added** PostgreSQL Large Objects (LO) as alternative to BYTEA.
- **Added** distributed multi-node deployments to test carbon crossover persistence.

### 7. Acknowledgment (Line 216–217)
- Replaced "[Hidden for double-blind review]" with both universities.
