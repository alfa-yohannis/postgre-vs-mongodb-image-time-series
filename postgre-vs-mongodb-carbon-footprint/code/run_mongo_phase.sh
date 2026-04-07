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
echo "PHASE 1: MONGODB FULL BENCHMARK"
echo "======================================"
docker compose down -v
docker compose up -d mongodb
echo "Waiting 10 seconds for MongoDB to initialize..."
sleep 10

for PROFILE in "${PROFILES[@]}"; do
    export MEDIA_PROFILE=$PROFILE
    echo "======================================"
    echo "RUNNING MONGODB PROFILE: $PROFILE"
    echo "======================================"
    run_step "[$PROFILE] Mongo Driver overhead..." "~/venv/bin/python driver_overhead_mongodb.py"
    run_step "[$PROFILE] Mongo Insert benchmark..." "~/venv/bin/python insert_mongodb.py"
    run_step "[$PROFILE] Mongo Retrieval benchmark..." "~/venv/bin/python retrieve_mongodb.py"
done
