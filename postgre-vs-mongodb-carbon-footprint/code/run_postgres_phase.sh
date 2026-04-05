#!/bin/bash
set -e
source ~/venv/bin/activate
export BENCHMARK_INSERT_RUNS=5
export BENCHMARK_DRIVER_RUNS=5
PROFILES=("1080p_fhd_image" "1440p_qhd_image" "4k_uhd_image" "5k_image")

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
    printf "✅ Completed in %02d:%02d (mm:ss)\n\n" $((STEP_DELTA / 60)) $((STEP_DELTA % 60))
}

echo "======================================"
echo "PHASE 2: POSTGRESQL FULL BENCHMARK"
echo "======================================"
docker compose down -v
docker compose up -d timescaledb
echo "Waiting 15 seconds for PostgreSQL to initialize..."
sleep 15

for PROFILE in "${PROFILES[@]}"; do
    export MEDIA_PROFILE=$PROFILE
    echo "======================================"
    echo "RUNNING POSTGRESQL PROFILE: $PROFILE"
    echo "======================================"
    run_step "[$PROFILE] PG Driver overhead..." "python driver_overhead_postgre.py"
    run_step "[$PROFILE] PG Insert benchmark..." "python insert_postgre.py"
    run_step "[$PROFILE] PG Retrieval benchmark..." "python retrieve_postgre.py"
done
