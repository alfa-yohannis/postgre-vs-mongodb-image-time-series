import time
import csv
import os
import statistics
from datetime import datetime, timezone

from pymongo import MongoClient


# =========================
# CONFIGURATION
# =========================

MONGO_URI = "mongodb://localhost:27017"
ENGINE_NAME = "mongodb+pymongo-driver"

# Benchmark parameters
WARMUP_RUNS = 20      # not logged
N_RUNS = 30          # more runs = more stable std-dev

SUMMARY_CSV_PATH = "results_mongo_driver_summary.csv"


# =========================
# DRIVER OVERHEAD COMMAND
# =========================

# Minimal roundtrip, analogous to SELECT 1 for PostgreSQL
QUERY_ID = "Q_driver_roundtrip_ping"


# =========================
# CSV HELPER (SUMMARY ONLY)
# =========================

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
    client = MongoClient(MONGO_URI)
    admin_db = client["admin"]

    print("\n==============================")
    print("MONGODB DRIVER OVERHEAD TEST")
    print("(SUMMARY ONLY)")
    print("==============================")
    print(f"Engine        : {ENGINE_NAME}")
    print(f"Query ID      : {QUERY_ID}")
    print(f"Warm-up runs  : {WARMUP_RUNS}")
    print(f"Measured runs : {N_RUNS}")
    print("==============================\n")

    # -------------------------
    # 1) WARM-UP RUNS (NOT LOGGED)
    # -------------------------
    for i in range(1, WARMUP_RUNS + 1):
        admin_db.command({"ping": 1})

    # -------------------------
    # 2) MEASURED RUNS
    # -------------------------
    latencies = []

    for run_id in range(1, N_RUNS + 1):
        t0 = time.perf_counter()
        admin_db.command({"ping": 1})
        t1 = time.perf_counter()

        latency_ms = (t1 - t0) * 1000.0
        latencies.append(latency_ms)

        print(f"Run {run_id}: {latency_ms:.4f} ms")

    # -------------------------
    # 3) SUMMARY STATISTICS
    # -------------------------

    mean_latency = statistics.mean(latencies)
    std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0.0

    print("\n==============================")
    print("DRIVER OVERHEAD SUMMARY")
    print("==============================")
    print(f"Engine        : {ENGINE_NAME}")
    print(f"Query ID      : {QUERY_ID}")
    print(f"Runs          : {N_RUNS}")
    print(f"Latency (ms)  : {mean_latency:.5f} ± {std_latency:.5f}")
    print("==============================\n")

    # -------------------------
    # 4) WRITE SUMMARY TO CSV
    # -------------------------

    summary_row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine": ENGINE_NAME,
        "query_id": QUERY_ID,
        "mean_latency_ms": round(mean_latency, 6),
        "std_latency_ms": round(std_latency, 6),
        "n_runs": N_RUNS,
    }

    append_summary_to_csv(summary_row)

    client.close()

    print(f"Summary saved to: {SUMMARY_CSV_PATH}")
    print("MongoDB driver overhead benchmark (summary-only) finished.\n")


if __name__ == "__main__":
    main()
