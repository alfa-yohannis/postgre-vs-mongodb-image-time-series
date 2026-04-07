"""Benchmark: retrieve all binary payloads within a time range (PostgreSQL)."""
from __future__ import annotations

import statistics
import time
from datetime import datetime, timezone

import psycopg2

from benchmark_config import describe_settings, load_settings
from benchmark_utils import append_row
from media_payloads import load_media_payload

ENGINE_NAME = "postgresql+timescaledb"
QUERY_ID = "Q_retrieve_binaries_time_range"

RUN_FIELDNAMES = [
    "timestamp", "engine", "profile", "payload_kind", "query_id",
    "run_id", "latency_ms", "rows_returned", "total_bytes_returned",
]

SUMMARY_FIELDNAMES = [
    "timestamp", "engine", "profile", "payload_kind", "query_id",
    "mean_latency_ms", "std_latency_ms", "n_runs",
    "rows_returned", "total_bytes_returned",
]


def main() -> None:
    settings = load_settings()
    payload = load_media_payload(settings)

    run_csv = settings.result_csv("results_postgres_retrieve_runs")
    summary_csv = settings.result_csv("results_postgres_retrieve_summary")

    conn = psycopg2.connect(**settings.postgres_config)
    try:
        with conn.cursor() as cur:
            print("PostgreSQL binary-retrieval benchmark")
            print(describe_settings(settings))

            # Get the time range of existing data
            cur.execute(
                f"SELECT MIN(ts), MAX(ts) FROM {settings.postgres_table_name} "
                f"WHERE device_id = %s;",
                (settings.device_id,),
            )
            ts_min, ts_max = cur.fetchone()
            if ts_min is None:
                print("ERROR: No data found. Run insert benchmark first.")
                return
            print(f"Time range: {ts_min} -> {ts_max}")

            query = f"""
            SELECT ts, payload_data
            FROM {settings.postgres_table_name}
            WHERE device_id = %s
              AND ts >= %s AND ts <= %s
            ORDER BY ts;
            """

            # Warmup
            for _ in range(settings.aggregation_warmup_runs):
                with conn.cursor(name="warmup_cur") as named_cur:
                    named_cur.itersize = 20
                    named_cur.execute(query, (settings.device_id, ts_min, ts_max))
                    for row in named_cur: pass

            latencies = []
            rows_returned = 0
            total_bytes = 0

            for run_id in range(1, settings.aggregation_runs + 1):
                t0 = time.perf_counter()
                with conn.cursor(name=f"run_cur_{run_id}") as named_cur:
                    named_cur.itersize = 20
                    named_cur.execute(query, (settings.device_id, ts_min, ts_max))
                    byte_sum = 0
                    count = 0
                    for row in named_cur:
                        byte_sum += len(row[1])
                        count += 1
                t1 = time.perf_counter()

                latency_ms = (t1 - t0) * 1000.0
                latencies.append(latency_ms)
                rows_returned = count
                total_bytes = byte_sum

                print(
                    f"Run {run_id}/{settings.aggregation_runs}: "
                    f"{latency_ms:.2f} ms, {rows_returned} rows, "
                    f"{total_bytes / 1e6:.1f} MB returned"
                )
                append_row(run_csv, RUN_FIELDNAMES, {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "engine": ENGINE_NAME,
                    "profile": settings.profile_slug,
                    "payload_kind": payload.payload_kind,
                    "query_id": QUERY_ID,
                    "run_id": run_id,
                    "latency_ms": round(latency_ms, 3),
                    "rows_returned": rows_returned,
                    "total_bytes_returned": total_bytes,
                })
    finally:
        conn.close()

    mean_lat = statistics.mean(latencies)
    std_lat = statistics.stdev(latencies) if len(latencies) > 1 else 0.0

    append_row(summary_csv, SUMMARY_FIELDNAMES, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine": ENGINE_NAME,
        "profile": settings.profile_slug,
        "payload_kind": payload.payload_kind,
        "query_id": QUERY_ID,
        "mean_latency_ms": round(mean_lat, 3),
        "std_latency_ms": round(std_lat, 3),
        "n_runs": settings.aggregation_runs,
        "rows_returned": rows_returned,
        "total_bytes_returned": total_bytes,
    })

    print(f"Summary: {mean_lat:.2f} ± {std_lat:.2f} ms")


if __name__ == "__main__":
    main()
