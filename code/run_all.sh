#!/bin/bash
set -e  # stop immediately if any command fails

echo "======================================"
echo "IOT IMAGE TIME-SERIES BENCHMARK RUNNER"
echo "WITH STEP-BY-STEP TIMING"
echo "======================================"
echo ""

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

    printf "✅ Completed in %02d:%02d (mm:ss)\n\n" \
        $((STEP_DELTA / 60)) $((STEP_DELTA % 60))
}

# --------------------------------------
# 1) DRIVER OVERHEAD BENCHMARKS
# --------------------------------------

run_step "[1/7] Running PostgreSQL driver overhead benchmark..." \
         "python driver_overhead_postgre.py"

run_step "[2/7] Running MongoDB driver overhead benchmark..." \
         "python driver_overhead_mongodb.py"
         
# --------------------------------------
# 2) INSERT BENCHMARKS
# --------------------------------------

run_step "[3/7] Running PostgreSQL insert benchmark..." \
         "python insert_postgre.py"

run_step "[4/7] Running MongoDB insert benchmark..." \
         "python insert_mongodb.py"


# --------------------------------------
# 3) AGGREGATION BENCHMARKS
# --------------------------------------

run_step "[5/7] Running PostgreSQL aggregation benchmark..." \
         "python aggregate_postgre.py"

run_step "[6/7] Running MongoDB aggregation benchmark..." \
         "python aggregate_mongodb.py"

# --------------------------------------
# 4) GENERATE FINAL BOXPLOTS (LAST!)
# --------------------------------------

run_step "[7/7] Generating boxplot PDFs (FINAL STEP)..." \
         "python boxplot.py"

# --------------------------------------
# TOTAL TIME REPORT
# --------------------------------------

TOTAL_END=$(date +%s)
TOTAL_DELTA=$((TOTAL_END - TOTAL_START))

echo "======================================"
printf "✅ ALL BENCHMARKS FINISHED SUCCESSFULLY\n"
printf "⏱️  TOTAL RUNTIME: %02d:%02d:%02d (hh:mm:ss)\n" \
    $((TOTAL_DELTA / 3600)) \
    $(((TOTAL_DELTA % 3600) / 60)) \
    $((TOTAL_DELTA % 60))
echo "======================================"
