#!/bin/bash
set -e

echo "=============================================="
echo "IOT IMAGE TIME-SERIES BENCHMARK RUNNER"
echo "WITH ISOLATED EXECUTION (PG BYTEA ONLY)"
echo "=============================================="
echo ""

source ~/venv/bin/activate
PYTHON_BIN="$HOME/venv/bin/python"
RESULTS_DIR="results"

if [ "$#" -eq 0 ]; then
    PROFILES=("480p_sd_image" "720p_hd_image" "1080p_fhd_image" "1440p_qhd_image" "4k_uhd_image")
else
    PROFILES=("$@")
fi

echo "Cleaning PostgreSQL-only result files..."
rm -f results_postgres_driver_summary.csv
mkdir -p "$RESULTS_DIR"
rm -f "$RESULTS_DIR"/results_postgres_driver_summary.csv
for PROFILE in "${PROFILES[@]}"; do
    rm -f "results_postgres_insert_runs_${PROFILE}.csv"
    rm -f "results_postgres_insert_summary_${PROFILE}.csv"
    rm -f "results_postgres_point_read_runs_${PROFILE}.csv"
    rm -f "results_postgres_point_read_summary_${PROFILE}.csv"
    rm -f "$RESULTS_DIR/results_postgres_insert_runs_${PROFILE}.csv"
    rm -f "$RESULTS_DIR/results_postgres_insert_summary_${PROFILE}.csv"
    rm -f "$RESULTS_DIR/results_postgres_point_read_runs_${PROFILE}.csv"
    rm -f "$RESULTS_DIR/results_postgres_point_read_summary_${PROFILE}.csv"
done

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

docker compose down -v
docker compose up -d timescaledb
echo "Waiting 15 seconds for PostgreSQL to initialize..."
sleep 15

for PROFILE in "${PROFILES[@]}"; do
    export MEDIA_PROFILE=$PROFILE
    echo "=============================================="
    echo "RUNNING PG PROFILE: $PROFILE"
    echo "=============================================="
    run_step "[$PROFILE] PG Driver overhead..." "\"$PYTHON_BIN\" driver_overhead_postgre.py"
    run_step "[$PROFILE] PG Insert benchmark..." "\"$PYTHON_BIN\" insert_postgre.py"
    run_step "[$PROFILE] PG Point-read benchmark..." "\"$PYTHON_BIN\" point_read_postgre.py"
done

TOTAL_END=$(date +%s)
TOTAL_DELTA=$((TOTAL_END - TOTAL_START))

echo "=============================================="
printf "PG BENCHMARKS FINISHED SUCCESSFULLY\n"
printf "TOTAL RUNTIME: %02d:%02d:%02d (hh:mm:ss)\n" \
    $((TOTAL_DELTA / 3600)) \
    $(((TOTAL_DELTA % 3600) / 60)) \
    $((TOTAL_DELTA % 60))
echo "=============================================="

docker compose down -v
