import time
import csv
import os
import statistics
from datetime import datetime, timezone

import psycopg2


# =========================
# CONFIGURATION
# =========================

DB_CONFIG = {
    "dbname": "iot_ts",
    "user": "postgres",
    "password": "1234",   # adjust if needed
    "host": "localhost",
    "port": 5432,
}

ENGINE_NAME = "postgres+timescaledb"

# Benchmark parameters
WARMUP_RUNS = 10      # not logged
N_RUNS = 20           # measured runs

RUN_CSV_PATH = "results_postgres_aggregate_runs.csv"
SUMMARY_CSV_PATH = "results_postgres_aggregate_summary.csv"


# =========================
# AGGREGATION QUERY
# =========================

QUERY_ID = "Q_time_bucket_1min_count_avg_size"

AGG_QUERY_SQL = """
SELECT
    time_bucket('1 minute', ts) AS bucket,
    COUNT(*) AS frames,
    AVG(octet_length(frame_data)) AS avg_image_size
FROM sensor_frames
GROUP BY bucket
ORDER BY bucket;
"""


# =========================
# CSV HELPERS
# =========================

def append_run_to_csv(row_dict):
    file_exists = os.path.exists(RUN_CSV_PATH)
    fieldnames = [
        "timestamp",
        "engine",
        "query_id",
        "run_id",
        "latency_ms",
    ]

    with open(RUN_CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_dict)


def append_summary_to_csv(summary_dict):
    file_exists = os.path.exists(SUMMARY_CSV_PATH)
    fieldnames = [
        "timestamp",
        "engine",
        "query_id",
        "mean_latency_ms",
        "std_latency_ms",
        "n_runs",
    ]

    with open(SUMMARY_CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(summary_dict)


# =========================
# MAIN
# =========================

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print("\n==============================")
    print("AGGREGATION BENCHMARK STARTED")
    print("==============================")
    print(f"Engine        : {ENGINE_NAME}")
    print(f"Query ID      : {QUERY_ID}")
    print(f"Warm-up runs  : {WARMUP_RUNS}")
    print(f"Measured runs: {N_RUNS}")
    print("==============================\n")

    # -------------------------
    # 1) WARM-UP RUNS (NOT LOGGED)
    # -------------------------
    for i in range(1, WARMUP_RUNS + 1):
        print(f"Warm-up run {i}/{WARMUP_RUNS} ...")
        cur.execute(AGG_QUERY_SQL)
        cur.fetchall()

    # -------------------------
    # 2) MEASURED RUNS
    # -------------------------
    latencies = []

    for run_id in range(1, N_RUNS + 1):
        t0 = time.perf_counter()
        cur.execute(AGG_QUERY_SQL)
        cur.fetchall()
        t1 = time.perf_counter()

        latency_ms = (t1 - t0) * 1000.0
        latencies.append(latency_ms)

        print(f"Run {run_id}: {latency_ms:.2f} ms")

        append_run_to_csv({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engine": ENGINE_NAME,
            "query_id": QUERY_ID,
            "run_id": run_id,
            "latency_ms": round(latency_ms, 3),
        })

    # -------------------------
    # 3) SUMMARY STATISTICS
    # -------------------------

    mean_latency = statistics.mean(latencies)
    std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0.0

    print("\n==============================")
    print("AGGREGATION SUMMARY (MEAN ± STD)")
    print("==============================")
    print(f"Engine        : {ENGINE_NAME}")
    print(f"Query ID      : {QUERY_ID}")
    print(f"Runs          : {N_RUNS}")
    print(f"Latency (ms)  : {mean_latency:.2f} ± {std_latency:.2f}")
    print("==============================\n")

    append_summary_to_csv({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine": ENGINE_NAME,
        "query_id": QUERY_ID,
        "mean_latency_ms": round(mean_latency, 3),
        "std_latency_ms": round(std_latency, 3),
        "n_runs": N_RUNS,
    })

    cur.close()
    conn.close()

    print(f"Per-run results saved to  : {RUN_CSV_PATH}")
    print(f"Summary results saved to  : {SUMMARY_CSV_PATH}")
    print("Aggregation benchmark finished.\n")


if __name__ == "__main__":
    main()
