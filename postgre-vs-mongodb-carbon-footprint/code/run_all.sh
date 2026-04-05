#!/bin/bash
set -e  # stop immediately if any command fails

echo "======================================"
echo "IOT IMAGE TIME-SERIES BENCHMARK RUNNER"
echo "WITH ISOLATED ENGINE EXECUTION"
echo "AND CARBON FOOTPRINT MEASUREMENT"
echo "======================================"
echo ""

source ~/venv/bin/activate

echo "Cleaning up old CSV results..."
rm -f *.csv
rm -f emissions.csv

TOTAL_START=$(date +%s)

# Execute Mongo Phase tracked by CodeCarbon
python tracker.py mongodb_phase bash ./run_mongo_phase.sh

# Execute PG Phase tracked by CodeCarbon
python tracker.py postgres_phase bash ./run_postgres_phase.sh

echo "======================================"
echo "PHASE 3: PLOTTING & CARBON ANALYSIS"
echo "======================================"
python boxplot.py
python carbon_summary.py

TOTAL_END=$(date +%s)
TOTAL_DELTA=$((TOTAL_END - TOTAL_START))

echo "======================================"
printf "✅ ALL BENCHMARKS FINISHED SUCCESSFULLY\n"
printf "⏱️  TOTAL RUNTIME: %02d:%02d:%02d (hh:mm:ss)\n" \
    $((TOTAL_DELTA / 3600)) \
    $(((TOTAL_DELTA % 3600) / 60)) \
    $((TOTAL_DELTA % 60))
echo "======================================"

echo "Shutting down Docker containers..."
docker compose down -v
