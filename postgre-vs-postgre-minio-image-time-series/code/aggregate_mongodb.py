from __future__ import annotations

import statistics
import time
from datetime import datetime, timezone

from pymongo import MongoClient

from benchmark_config import describe_settings, load_settings
from benchmark_utils import append_row
from media_payloads import load_media_payload


ENGINE_NAME = "mongodb_timeseries+minio"
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

    run_csv_path = settings.result_csv("results_mongo_aggregate_runs")
    summary_csv_path = settings.result_csv("results_mongo_aggregate_summary")

    pipeline = [
        {"$match": {"meta.device_id": settings.device_id}},
        {
            "$addFields": {
                "bucket": {
                    "$dateTrunc": {
                        "date": "$ts",
                        "unit": "minute",
                    }
                }
            }
        },
        {
            "$group": {
                "_id": "$bucket",
                "samples": {"$sum": 1},
                "avg_payload_size_bytes": {"$avg": "$payload_size_bytes"},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    client = MongoClient(settings.mongo_uri)
    try:
        coll = client[settings.mongo_db_name][settings.mongo_collection_name]
        print("MongoDB+MinIO aggregation benchmark")
        print(describe_settings(settings))

        for _ in range(settings.aggregation_warmup_runs):
            list(coll.aggregate(pipeline, allowDiskUse=True))

        latencies = []
        for run_id in range(1, settings.aggregation_runs + 1):
            t0 = time.perf_counter()
            list(coll.aggregate(pipeline, allowDiskUse=True))
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
        client.close()

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
