"""Benchmark: retrieve all binary payloads within a time range (MongoDB)."""
from __future__ import annotations

import statistics
import time
from datetime import datetime, timezone

from pymongo import MongoClient

from benchmark_config import describe_settings, load_settings
from benchmark_utils import append_row
from media_payloads import load_media_payload

ENGINE_NAME = "mongodb_timeseries"
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

    run_csv = settings.result_csv("results_mongo_retrieve_runs")
    summary_csv = settings.result_csv("results_mongo_retrieve_summary")

    client = MongoClient(settings.mongo_uri)
    try:
        coll = client[settings.mongo_db_name][settings.mongo_collection_name]
        print("MongoDB binary-retrieval benchmark")
        print(describe_settings(settings))

        # Get the time range of existing data
        pipeline_range = [
            {"$match": {"meta.device_id": settings.device_id}},
            {"$group": {
                "_id": None,
                "min_ts": {"$min": "$ts"},
                "max_ts": {"$max": "$ts"},
            }},
        ]
        range_result = list(coll.aggregate(pipeline_range))
        if not range_result:
            print("ERROR: No data found. Run insert benchmark first.")
            return
        ts_min = range_result[0]["min_ts"]
        ts_max = range_result[0]["max_ts"]
        print(f"Time range: {ts_min} -> {ts_max}")

        query_filter = {
            "meta.device_id": settings.device_id,
            "ts": {"$gte": ts_min, "$lte": ts_max},
        }
        projection = {"ts": 1, "payload_data": 1, "_id": 0}

        # Warmup
        for _ in range(2):
            docs = list(coll.find(query_filter, projection).sort("ts", 1))

        latencies = []
        rows_returned = 0
        total_bytes = 0

        for run_id in range(1, settings.aggregation_runs + 1):
            t0 = time.perf_counter()
            docs = list(coll.find(query_filter, projection).sort("ts", 1))
            # Force materialization of all binary payloads
            byte_sum = sum(len(d["payload_data"]) for d in docs)
            t1 = time.perf_counter()

            latency_ms = (t1 - t0) * 1000.0
            latencies.append(latency_ms)
            rows_returned = len(docs)
            total_bytes = byte_sum

            print(
                f"Run {run_id}/{settings.aggregation_runs}: "
                f"{latency_ms:.2f} ms, {rows_returned} docs, "
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
        client.close()

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
