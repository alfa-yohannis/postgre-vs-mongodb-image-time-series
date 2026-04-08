#!/bin/bash
set -e

source ~/venv/bin/activate
PYTHON_BIN="$HOME/venv/bin/python"

export BENCHMARK_INSERT_RUNS=1
export BENCHMARK_POINT_READ_RUNS=1
export BENCHMARK_DRIVER_WARMUP_RUNS=5
export BENCHMARK_DRIVER_RUNS=10

PROFILES=("480p_sd_image" "720p_hd_image" "1080p_fhd_image" "1440p_qhd_image" "4k_uhd_image")

echo "=============================================="
echo "PHASE 1: PG BYTEA (fast insert + point read)"
echo "=============================================="
docker compose down -v
docker compose up -d timescaledb
sleep 15

for PROFILE in "${PROFILES[@]}"; do
    export MEDIA_PROFILE=$PROFILE
    echo "--- PG PROFILE: $PROFILE ---"
    "$PYTHON_BIN" insert_postgre.py
    "$PYTHON_BIN" point_read_postgre.py
done

echo "=============================================="
echo "PHASE 2: PG + MINIO (fast insert + point read)"
echo "=============================================="
docker compose down -v
docker compose up -d timescaledb minio
sleep 15

for PROFILE in "${PROFILES[@]}"; do
    export MEDIA_PROFILE=$PROFILE
    echo "--- PM PROFILE: $PROFILE ---"
    "$PYTHON_BIN" insert_postgre_minio.py
    "$PYTHON_BIN" point_read_postgre_minio.py
done

"$PYTHON_BIN" boxplot.py
"$PYTHON_BIN" stat_summary.py
docker compose down -v
