#!/bin/bash
set -e

source ~/venv/bin/activate

export BENCHMARK_INSERT_RUNS=1
PROFILES=("1080p_fhd_image" "1440p_qhd_image" "4k_uhd_image" "5k_image" "6k_image")

echo "======================================"
echo "PHASE 1: MONGODB (fast insert & retrieve)"
echo "======================================"
docker compose down -v
docker compose up -d mongodb
sleep 15

for PROFILE in "${PROFILES[@]}"; do
    export MEDIA_PROFILE=$PROFILE
    echo "--- MongoDB PROFILE: $PROFILE ---"
    python insert_mongodb.py
    python retrieve_mongodb.py
done

echo "======================================"
echo "PHASE 2: POSTGRESQL (fast insert & retrieve)"
echo "======================================"
docker compose down -v
docker compose up -d timescaledb
sleep 15

for PROFILE in "${PROFILES[@]}"; do
    export MEDIA_PROFILE=$PROFILE
    echo "--- PostgreSQL PROFILE: $PROFILE ---"
    python insert_postgre.py
    python retrieve_postgre.py
done

python boxplot.py
docker compose down -v
