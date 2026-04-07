#!/bin/bash
set -e  # stop immediately if any command fails

echo "======================================"
echo "IOT IMAGE TIME-SERIES BENCHMARK RUNNER"
echo "WITH ISOLATED ENGINE EXECUTION (POSTGRES ONLY)"
echo "======================================"
echo ""

source ~/venv/bin/activate

if [ "$#" -eq 0 ]; then
    PROFILES=("1080p_fhd_image" "1440p_qhd_image" "4k_uhd_image" "5k_image" "6k_image")
else
    PROFILES=("$@")
fi

echo "Cleaning up old CSV results for selected profiles (Postgres only)..."
mkdir -p results/
for PROFILE in "${PROFILES[@]}"; do
    rm -f results/*postgres*_${PROFILE}.csv
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

    printf "✅ Completed in %02d:%02d (mm:ss)\n\n" \
        $((STEP_DELTA / 60)) $((STEP_DELTA % 60))
}

export BENCHMARK_INSERT_RUNS=5
export BENCHMARK_DRIVER_RUNS=5

echo "======================================"
echo "PHASE 2: POSTGRESQL FULL BENCHMARK"
echo "======================================"
docker compose down -v
docker compose up -d timescaledb
echo "Waiting 10 seconds for PostgreSQL to initialize..."
sleep 10

for PROFILE in "${PROFILES[@]}"; do
    export MEDIA_PROFILE=$PROFILE
    echo "======================================"
    echo "RUNNING POSTGRESQL PROFILE: $PROFILE"
    echo "======================================"
    run_step "[$PROFILE] PG Driver overhead..." "python driver_overhead_postgre.py"
    run_step "[$PROFILE] PG Insert benchmark..." "python insert_postgre.py"
    run_step "[$PROFILE] PG Retrieval benchmark..." "python retrieve_postgre.py"
done

TOTAL_END=$(date +%s)
TOTAL_DELTA=$((TOTAL_END - TOTAL_START))

echo "======================================"
printf "✅ POSTGRES BENCHMARKS FINISHED SUCCESSFULLY\n"
printf "⏱️  TOTAL RUNTIME: %02d:%02d:%02d (hh:mm:ss)\n" \
    $((TOTAL_DELTA / 3600)) \
    $(((TOTAL_DELTA % 3600) / 60)) \
    $((TOTAL_DELTA % 60))
echo "======================================"

echo "Shutting down Docker containers..."
docker compose down -v
