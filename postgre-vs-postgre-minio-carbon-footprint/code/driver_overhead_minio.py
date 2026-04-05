import time
import csv
import os
import statistics
from datetime import datetime, timezone

from minio import Minio


MINIO_ENDPOINT = "127.0.0.1:59000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
ENGINE_NAME = "minio+minio-py-driver"
WARMUP_RUNS = 20
N_RUNS = 30

SUMMARY_CSV_PATH = "results_minio_driver_summary.csv"
QUERY_ID = "Q_driver_roundtrip_list_buckets"


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


def main():
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )

    print("\n==============================")
    print("MINIO DRIVER OVERHEAD TEST")
    print("(SUMMARY ONLY)")
    print("==============================")
    print(f"Engine        : {ENGINE_NAME}")
    print(f"Query ID      : {QUERY_ID}")
    print(f"Warm-up runs  : {WARMUP_RUNS}")
    print(f"Measured runs : {N_RUNS}")
    print("==============================\n")

    for _ in range(1, WARMUP_RUNS + 1):
        client.list_buckets()

    latencies = []
    for run_id in range(1, N_RUNS + 1):
        t0 = time.perf_counter()
        client.list_buckets()
        t1 = time.perf_counter()
        latency_ms = (t1 - t0) * 1000.0
        latencies.append(latency_ms)
        print(f"Run {run_id}: {latency_ms:.4f} ms")

    mean_latency = statistics.mean(latencies)
    std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0.0

    print("\n==============================")
    print("DRIVER OVERHEAD SUMMARY")
    print("==============================")
    print(f"Engine        : {ENGINE_NAME}")
    print(f"Query ID      : {QUERY_ID}")
    print(f"Runs          : {N_RUNS}")
    print(f"Latency (ms)  : {mean_latency:.5f} +/- {std_latency:.5f}")
    print("==============================\n")

    append_summary_to_csv({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine": ENGINE_NAME,
        "query_id": QUERY_ID,
        "mean_latency_ms": round(mean_latency, 6),
        "std_latency_ms": round(std_latency, 6),
        "n_runs": N_RUNS,
    })

    print(f"Summary saved to: {SUMMARY_CSV_PATH}")


if __name__ == "__main__":
    main()
