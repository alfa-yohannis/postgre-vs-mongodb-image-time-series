from __future__ import annotations

import statistics
import time
from datetime import datetime, timezone

import psycopg2

from benchmark_config import describe_settings, load_settings
from benchmark_utils import append_row
from media_payloads import load_media_payload


ENGINE_NAME = "postgresql+timescaledb+minio"
QUERY_ID = "Q_time_bucket_1min_count_avg_payload"

RUN_FIELDNAMES = [
    "timestamp",
    "engine",
    "profile",
    "payload_kind",
    "query_id",
    "run_id",
    "latency_ms",
]

SUMMARY_FIELDNAMES = [
    "timestamp",
    "engine",
    "profile",
    "payload_kind",
    "query_id",
    "mean_latency_ms",
    "std_latency_ms",
    "n_runs",
]


def main() -> None:
    settings = load_settings()
    payload = load_media_payload(settings)

    run_csv_path = settings.result_csv("results_postgres_minio_aggregate_runs")
    summary_csv_path = settings.result_csv("results_postgres_minio_aggregate_summary")

    query = f"""
    SELECT
        time_bucket(INTERVAL '1 minute', ts) AS bucket,
        COUNT(*) AS samples,
        AVG(payload_size_bytes) AS avg_payload_size_bytes
    FROM {settings.postgres_minio_table_name}
    WHERE device_id = %s
    GROUP BY bucket
    ORDER BY bucket;
    """

    conn = psycopg2.connect(**settings.postgres_config)
    try:
        with conn.cursor() as cur:
            print("PostgreSQL+MinIO aggregation benchmark")
            print(describe_settings(settings))

            for _ in range(settings.aggregation_warmup_runs):
                cur.execute(query, (settings.device_id,))
                cur.fetchall()

            latencies = []
            for run_id in range(1, settings.aggregation_runs + 1):
                t0 = time.perf_counter()
                cur.execute(query, (settings.device_id,))
                cur.fetchall()
                t1 = time.perf_counter()
                latency_ms = (t1 - t0) * 1000.0
                latencies.append(latency_ms)

                print(f"Run {run_id}/{settings.aggregation_runs}: {latency_ms:.2f} ms")
                append_row(
                    run_csv_path,
                    RUN_FIELDNAMES,
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "engine": ENGINE_NAME,
                        "profile": settings.profile_slug,
                        "payload_kind": payload.payload_kind,
                        "query_id": QUERY_ID,
                        "run_id": run_id,
                        "latency_ms": round(latency_ms, 3),
                    },
                )
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
            "payload_kind": payload.payload_kind,
            "query_id": QUERY_ID,
            "mean_latency_ms": round(mean_latency, 3),
            "std_latency_ms": round(std_latency, 3),
            "n_runs": settings.aggregation_runs,
        },
    )

    print(f"Summary: {mean_latency:.2f} +/- {std_latency:.2f} ms")


if __name__ == "__main__":
    main()
