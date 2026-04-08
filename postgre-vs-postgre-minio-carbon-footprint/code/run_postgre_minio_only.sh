#!/bin/bash
set -e

echo "=============================================="
echo "IOT IMAGE TIME-SERIES BENCHMARK RUNNER"
echo "WITH ISOLATED EXECUTION (PG + MINIO ONLY)"
echo "=============================================="
echo ""

source ~/venv/bin/activate
PYTHON_BIN="$HOME/venv/bin/python"
RESULTS_DIR="results"

normalize_profile () {
    case "$1" in
        360_sd_image) echo "360p_sd_image" ;;
        480_sd_image) echo "480p_sd_image" ;;
        720_hd_image) echo "720p_hd_image" ;;
        1080_fhd_image) echo "1080p_fhd_image" ;;
        1440_qhd_image) echo "1440p_qhd_image" ;;
        *) echo "$1" ;;
    esac
}

if [ "$#" -eq 0 ]; then
    PROFILES=(
        "360p_sd_image"
        "480p_sd_image"
        "720p_hd_image"
        "1080p_fhd_image"
        "1440p_qhd_image"
        "4k_uhd_image"
        "5k_uhd_image"
    )
else
    PROFILES=()
    for PROFILE in "$@"; do
        PROFILES+=("$(normalize_profile "$PROFILE")")
    done
fi

echo "Cleaning PostgreSQL+MinIO result files..."
rm -f results_minio_driver_summary.csv
mkdir -p "$RESULTS_DIR"
rm -f "$RESULTS_DIR"/results_minio_driver_summary.csv
for PROFILE in "${PROFILES[@]}"; do
    rm -f "results_postgres_minio_insert_runs_${PROFILE}.csv"
    rm -f "results_postgres_minio_insert_summary_${PROFILE}.csv"
    rm -f "results_postgres_minio_retrieve_runs_${PROFILE}.csv"
    rm -f "results_postgres_minio_retrieve_summary_${PROFILE}.csv"
    rm -f "results_postgres_minio_point_read_runs_${PROFILE}.csv"
    rm -f "results_postgres_minio_point_read_summary_${PROFILE}.csv"
    rm -f "$RESULTS_DIR/results_postgres_minio_insert_runs_${PROFILE}.csv"
    rm -f "$RESULTS_DIR/results_postgres_minio_insert_summary_${PROFILE}.csv"
    rm -f "$RESULTS_DIR/results_postgres_minio_retrieve_runs_${PROFILE}.csv"
    rm -f "$RESULTS_DIR/results_postgres_minio_retrieve_summary_${PROFILE}.csv"
    rm -f "$RESULTS_DIR/results_postgres_minio_point_read_runs_${PROFILE}.csv"
    rm -f "$RESULTS_DIR/results_postgres_minio_point_read_summary_${PROFILE}.csv"
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
export BENCHMARK_DRIVER_WARMUP_RUNS=10
export BENCHMARK_DRIVER_RUNS=10

docker compose down -v
docker compose up -d timescaledb minio
echo "Waiting 10 seconds for PostgreSQL and MinIO to initialize..."
sleep 10

for PROFILE in "${PROFILES[@]}"; do
    export MEDIA_PROFILE=$PROFILE
    echo "=============================================="
    echo "RUNNING PM PROFILE: $PROFILE"
    echo "=============================================="
    run_step "[$PROFILE] MinIO Driver overhead..." "\"$PYTHON_BIN\" driver_overhead_minio.py"
    run_step "[$PROFILE] PG+MinIO Insert benchmark..." "\"$PYTHON_BIN\" insert_postgre_minio.py"
    run_step "[$PROFILE] PG+MinIO Retrieval benchmark..." "\"$PYTHON_BIN\" retrieve_postgre_minio.py"
done

TOTAL_END=$(date +%s)
TOTAL_DELTA=$((TOTAL_END - TOTAL_START))

echo "=============================================="
printf "PM BENCHMARKS FINISHED SUCCESSFULLY\n"
printf "TOTAL RUNTIME: %02d:%02d:%02d (hh:mm:ss)\n" \
    $((TOTAL_DELTA / 3600)) \
    $(((TOTAL_DELTA % 3600) / 60)) \
    $((TOTAL_DELTA % 60))
echo "=============================================="

docker compose down -v
