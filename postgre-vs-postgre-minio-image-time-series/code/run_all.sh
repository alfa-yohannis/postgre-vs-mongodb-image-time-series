#!/bin/bash
set -e

echo "=============================================="
echo "IOT IMAGE TIME-SERIES BENCHMARK RUNNER"
echo "PostgreSQL (BYTEA) vs PostgreSQL+MinIO"
echo "WITH ISOLATED ENGINE EXECUTION"
echo "=============================================="
echo ""

# --------------------------------------
# ENV SETUP
# --------------------------------------
source ~/venv/bin/activate
PYTHON_BIN="$HOME/venv/bin/python"
RESULTS_DIR="results"

echo "Cleaning up old CSV results..."
rm -f *.csv
rm -f all_summaries.txt
mkdir -p "$RESULTS_DIR"
rm -f "$RESULTS_DIR"/*.csv

# --------------------------------------
# GLOBAL TIMER
# --------------------------------------

TOTAL_START=$(date +%s)

run_step () {
    STEP_NAME="$1"
    STEP_CMD="$2"

    echo "--------------------------------------"
    echo "$STEP_NAME"
    echo "--------------------------------------"

    STEP_START=$(date +%s)

    eval "$STEP_CMD"

    STEP_END=$(date +%s)
    STEP_DELTA=$((STEP_END - STEP_START))

    printf "Completed in %02d:%02d (mm:ss)\n\n" \
        $((STEP_DELTA / 60)) $((STEP_DELTA % 60))
}

export BENCHMARK_INSERT_RUNS=5
export BENCHMARK_POINT_READ_RUNS=5
export BENCHMARK_DRIVER_WARMUP_RUNS=20
export BENCHMARK_DRIVER_RUNS=30

PROFILES=("480p_sd_image" "720p_hd_image" "1080p_fhd_image" "1440p_qhd_image" "4k_uhd_image")

# --------------------------------------
# PHASE 1: POSTGRESQL (BYTEA) ONLY
# --------------------------------------
echo "=============================================="
echo "PHASE 1: POSTGRESQL (BYTEA) — isolated"
echo "=============================================="

docker compose down -v
docker compose up -d timescaledb
echo "Waiting 15 seconds for PostgreSQL to initialize..."
sleep 15

for PROFILE in "${PROFILES[@]}"; do
    export MEDIA_PROFILE=$PROFILE
    echo "=============================================="
    echo "RUNNING PROFILE: $PROFILE"
    echo "=============================================="

    run_step "[$PROFILE] PG Driver overhead..." "\"$PYTHON_BIN\" driver_overhead_postgre.py"
    run_step "[$PROFILE] PG (BYTEA) Insert benchmark..." "\"$PYTHON_BIN\" insert_postgre.py"
    run_step "[$PROFILE] PG (BYTEA) Retrieval benchmark..." "\"$PYTHON_BIN\" point_read_postgre.py"
done

# --------------------------------------
# PHASE 2: POSTGRESQL + MINIO
# --------------------------------------
echo "=============================================="
echo "PHASE 2: POSTGRESQL + MINIO — isolated"
echo "=============================================="

docker compose down -v
docker compose up -d timescaledb minio
echo "Waiting 15 seconds for PostgreSQL and MinIO to initialize..."
sleep 15

for PROFILE in "${PROFILES[@]}"; do
    export MEDIA_PROFILE=$PROFILE
    echo "=============================================="
    echo "RUNNING PROFILE: $PROFILE"
    echo "=============================================="

    run_step "[$PROFILE] MinIO Driver overhead..." "\"$PYTHON_BIN\" driver_overhead_minio.py"
    run_step "[$PROFILE] PG+MinIO Insert benchmark..." "\"$PYTHON_BIN\" insert_postgre_minio.py"
    run_step "[$PROFILE] PG+MinIO Retrieval benchmark..." "\"$PYTHON_BIN\" point_read_postgre_minio.py"
done

# --------------------------------------
# GENERATE FINAL PLOTS
# --------------------------------------
run_step "Generating scaling PDFs..." "\"$PYTHON_BIN\" boxplot.py"
run_step "Generating aggregate helper outputs..." "\"$PYTHON_BIN\" aggregate_results.py"
run_step "Generating final summary CSV..." "\"$PYTHON_BIN\" stat_summary.py"

# --------------------------------------
# TOTAL TIME REPORT
# --------------------------------------
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
