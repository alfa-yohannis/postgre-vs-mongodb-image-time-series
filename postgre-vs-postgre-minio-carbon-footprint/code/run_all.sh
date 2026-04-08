#!/bin/bash
set -e

source ~/venv/bin/activate
PYTHON_BIN="$HOME/venv/bin/python"
RESULTS_DIR="results"

TOTAL_START=$(date +%s)

echo "=============================================="
echo "IOT IMAGE TIME-SERIES BENCHMARK RUNNER"
echo "PostgreSQL (BYTEA) vs PostgreSQL+MinIO"
echo "WITH CARBON FOOTPRINT MEASUREMENT"
echo "=============================================="
echo ""

echo "Cleaning old benchmark artifacts..."
rm -rf "$RESULTS_DIR"
mkdir -p "$RESULTS_DIR"
rm -f final_stats_summary.csv
rm -f all_summaries.txt

echo "=============================================="
echo "PHASE 1: POSTGRESQL (BYTEA)"
echo "=============================================="
"$PYTHON_BIN" tracker.py postgres_phase bash ./run_postgres_phase.sh

echo "=============================================="
echo "PHASE 2: POSTGRESQL + MINIO"
echo "=============================================="
"$PYTHON_BIN" tracker.py postgres_minio_phase bash ./run_postgres_minio_phase.sh

echo "=============================================="
echo "PHASE 3: PLOTTING & CARBON ANALYSIS"
echo "=============================================="
"$PYTHON_BIN" boxplot.py
"$PYTHON_BIN" carbon_summary.py
"$PYTHON_BIN" aggregate_results.py
"$PYTHON_BIN" stat_summary.py

TOTAL_END=$(date +%s)
TOTAL_DELTA=$((TOTAL_END - TOTAL_START))

echo "=============================================="
printf "ALL BENCHMARKS FINISHED SUCCESSFULLY\n"
printf "TOTAL RUNTIME: %02d:%02d:%02d (hh:mm:ss)\n" \
    $((TOTAL_DELTA / 3600)) \
    $(((TOTAL_DELTA % 3600) / 60)) \
    $((TOTAL_DELTA % 60))
echo "=============================================="

echo "Shutting down Docker containers..."
docker compose down -v
