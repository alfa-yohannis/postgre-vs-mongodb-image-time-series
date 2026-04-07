#!/bin/bash
set -e  # stop immediately if any command fails

echo "======================================"
echo "IOT IMAGE TIME-SERIES BENCHMARK RUNNER"
echo "WITH ISOLATED ENGINE EXECUTION"
echo "======================================"
echo ""

source ~/venv/bin/activate

echo "Cleaning up old CSV results..."
rm -rf results/
mkdir -p results/

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

    printf "✅ Completed in %02d:%02d (mm:ss)\n\n" \
        $((STEP_DELTA / 60)) $((STEP_DELTA % 60))
}

export BENCHMARK_INSERT_RUNS=5
export BENCHMARK_DRIVER_RUNS=5

PROFILES=("1080p_fhd_image" "1440p_qhd_image" "4k_uhd_image" "5k_image" "6k_image")

echo "======================================"
echo "PHASE 1: MONGODB FULL BENCHMARK"
echo "======================================"
docker compose down -v
docker compose up -d mongodb
echo "Waiting 5 seconds for MongoDB to initialize..."
sleep 5

for PROFILE in "${PROFILES[@]}"; do
    export MEDIA_PROFILE=$PROFILE
    echo "======================================"
    echo "RUNNING MONGODB PROFILE: $PROFILE"
    echo "======================================"
    run_step "[$PROFILE] Mongo Driver overhead..." "python driver_overhead_mongodb.py"
    run_step "[$PROFILE] Mongo Insert benchmark..." "python insert_mongodb.py"
    run_step "[$PROFILE] Mongo Retrieval benchmark..." "python retrieve_mongodb.py"
done

echo "======================================"
echo "PHASE 2: POSTGRESQL FULL BENCHMARK"
echo "======================================"
docker compose down -v
docker compose up -d timescaledb
echo "Waiting 5 seconds for PostgreSQL to initialize..."
sleep 5

for PROFILE in "${PROFILES[@]}"; do
    export MEDIA_PROFILE=$PROFILE
    echo "======================================"
    echo "RUNNING POSTGRESQL PROFILE: $PROFILE"
    echo "======================================"
    run_step "[$PROFILE] PG Driver overhead..." "python driver_overhead_postgre.py"
    run_step "[$PROFILE] PG Insert benchmark..." "python insert_postgre.py"
    run_step "[$PROFILE] PG Retrieval benchmark..." "python retrieve_postgre.py"
done

run_step "Generating plotting scaling PDFs..." "python boxplot.py"

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
