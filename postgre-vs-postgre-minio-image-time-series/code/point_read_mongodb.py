from __future__ import annotations

import statistics
import time
from datetime import datetime, timezone

from pymongo import MongoClient

from benchmark_config import describe_settings, load_settings
from benchmark_utils import append_row
from database_setup import open_minio
from media_payloads import load_media_payload


ENGINE_NAME = "mongodb_timeseries+minio"
QUERY_ID = "Q_latest_payload_by_device"

RUN_FIELDNAMES = [
    "timestamp",
    "engine",
    "profile",
    "payload_kind",
    "query_id",
    "run_id",
    "latency_ms",
    "payload_size_bytes",
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
    "payload_size_bytes",
]


def main() -> None:
    settings = load_settings()
    payload = load_media_payload(settings)
    minio_client = open_minio(settings)

    run_csv_path = settings.result_csv("results_mongo_point_read_runs")
    summary_csv_path = settings.result_csv("results_mongo_point_read_summary")

    client = MongoClient(settings.mongo_uri)
    try:
        coll = client[settings.mongo_db_name][settings.mongo_collection_name]
        print("MongoDB+MinIO point-read benchmark")
        print(describe_settings(settings))

        for _ in range(settings.point_read_warmup_runs):
            doc = coll.find_one(
                {"meta.device_id": settings.device_id},
                sort=[("ts", -1)],
            )
            if doc and "minio_object_key" in doc:
                resp = minio_client.get_object(settings.minio_bucket, doc["minio_object_key"])
                resp.read()
                resp.close()
                resp.release_conn()

        latencies = []
        for run_id in range(1, settings.point_read_runs + 1):
            t0 = time.perf_counter()
            doc = coll.find_one(
                {"meta.device_id": settings.device_id},
                sort=[("ts", -1)],
            )
            if doc and "minio_object_key" in doc:
                resp = minio_client.get_object(settings.minio_bucket, doc["minio_object_key"])
                resp.read()
                resp.close()
                resp.release_conn()
            t1 = time.perf_counter()

            latency_ms = (t1 - t0) * 1000.0
            latencies.append(latency_ms)

            print(f"Run {run_id}/{settings.point_read_runs}: {latency_ms:.2f} ms")
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
                    "payload_size_bytes": payload.payload_size_bytes,
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
            "n_runs": settings.point_read_runs,
            "payload_size_bytes": payload.payload_size_bytes,
        },
    )

    print(f"Summary: {mean_latency:.2f} +/- {std_latency:.2f} ms")


if __name__ == "__main__":
    main()
