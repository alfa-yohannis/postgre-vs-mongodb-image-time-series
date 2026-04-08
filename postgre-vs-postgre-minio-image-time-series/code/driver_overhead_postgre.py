from __future__ import annotations

import statistics
import time
from datetime import datetime, timezone

import psycopg2

from benchmark_config import describe_settings, load_settings
from benchmark_utils import append_row


ENGINE_NAME = "postgres+psycopg2-driver"
QUERY_ID = "Q_driver_roundtrip_select_1"
DRIVER_QUERY_SQL = "SELECT 1;"

SUMMARY_FIELDNAMES = [
    "timestamp",
    "engine",
    "profile",
    "query_id",
    "mean_latency_ms",
    "std_latency_ms",
    "n_runs",
]


def main() -> None:
    settings = load_settings()
    summary_csv_path = settings.results_dir / "results_postgres_driver_summary.csv"

    conn = psycopg2.connect(**settings.postgres_config)
    try:
        with conn.cursor() as cur:
            print("PostgreSQL driver overhead benchmark")
            print(describe_settings(settings))
            print(
                f"warmup_runs={settings.driver_warmup_runs}, "
                f"measured_runs={settings.driver_runs}"
            )

            for _ in range(settings.driver_warmup_runs):
                cur.execute(DRIVER_QUERY_SQL)
                cur.fetchone()

            latencies = []
            for run_id in range(1, settings.driver_runs + 1):
                t0 = time.perf_counter()
                cur.execute(DRIVER_QUERY_SQL)
                cur.fetchone()
                t1 = time.perf_counter()
                latency_ms = (t1 - t0) * 1000.0
                latencies.append(latency_ms)
                print(f"Run {run_id}/{settings.driver_runs}: {latency_ms:.4f} ms")
    finally:
        conn.close()

    mean_latency = statistics.mean(latencies)
    std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0.0

    append_row(
        summary_csv_path,
        SUMMARY_FIELDNAMES,
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engine": ENGINE_NAME,
            "profile": settings.profile_slug,
            "query_id": QUERY_ID,
            "mean_latency_ms": round(mean_latency, 6),
            "std_latency_ms": round(std_latency, 6),
            "n_runs": settings.driver_runs,
        },
    )

    print(f"Summary: {mean_latency:.5f} +/- {std_latency:.5f} ms")
    print(f"Saved summary to {summary_csv_path.name}")


if __name__ == "__main__":
    main()
