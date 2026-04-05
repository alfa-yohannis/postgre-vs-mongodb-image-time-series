from __future__ import annotations

import statistics
import time
import uuid
from datetime import datetime, timezone
from io import BytesIO

from pymongo import MongoClient
from minio import Minio

from benchmark_config import describe_settings, load_settings
from benchmark_utils import append_row, bytes_to_mb
from database_setup import open_minio, recreate_minio_bucket, recreate_mongo_collection
from media_payloads import load_media_payload


ENGINE_NAME = "mongodb_timeseries+minio"

RUN_FIELDNAMES = [
    "timestamp",
    "engine",
    "profile",
    "payload_kind",
    "payload_size_bytes",
    "payload_size_mb",
    "run_id",
    "total_rows_requested",
    "rows_inserted",
    "batch_size",
    "duration_sec",
    "rows_per_sec",
    "logical_mb_inserted",
    "logical_mb_per_sec",
    "db_size_before_mb",
    "db_size_after_mb",
    "table_total_before_mb",
    "table_total_after_mb",
    "table_data_before_mb",
    "table_data_after_mb",
    "table_index_before_mb",
    "table_index_after_mb",
    "rows_in_table_after",
    "table_storage_amplification",
]

SUMMARY_FIELDNAMES = [
    "timestamp",
    "engine",
    "profile",
    "payload_kind",
    "payload_size_bytes",
    "payload_size_mb",
    "warmup_rows",
    "total_rows_per_run",
    "batch_size",
    "n_runs",
    "mean_duration_sec",
    "std_duration_sec",
    "mean_rows_per_sec",
    "std_rows_per_sec",
    "mean_logical_mb_per_sec",
    "std_logical_mb_per_sec",
    "mean_db_size_after_mb",
    "std_db_size_after_mb",
    "mean_table_total_after_mb",
    "std_table_total_after_mb",
    "mean_storage_amplification",
    "std_storage_amplification",
]


def get_collection_and_db_sizes(db, coll_name: str, minio_client: Minio, bucket: str) -> dict[str, int]:
    dbstats = db.command("dbStats")
    collstats = db.command("collStats", coll_name)

    coll_storage_bytes = collstats.get("storageSize", collstats.get("size", 0))
    coll_index_bytes = collstats.get("totalIndexSize", 0)
    coll_total_bytes = coll_storage_bytes + coll_index_bytes

    # Add MinIO object storage size to the totals
    minio_bytes = 0
    try:
        objects = minio_client.list_objects(bucket, recursive=True)
        for obj in objects:
            minio_bytes += obj.size
    except Exception:
        pass

    db_storage_bytes = dbstats.get("storageSize", dbstats.get("dataSize", 0))
    db_index_bytes = dbstats.get("indexSize", 0)
    db_total_bytes = db_storage_bytes + db_index_bytes + minio_bytes

    return {
        "table_total_bytes": int(coll_total_bytes + minio_bytes),
        "table_data_bytes": int(coll_storage_bytes + minio_bytes),
        "table_index_bytes": int(coll_index_bytes),
        "db_bytes": int(db_total_bytes),
    }


def get_row_count(coll) -> int:
    return int(coll.count_documents({}))


def insert_docs(coll, minio_client: Minio, bucket: str, settings, payload) -> tuple[int, float]:
    t0 = time.perf_counter()
    batch = []
    inserted = 0

    while inserted < settings.total_rows:
        ts = datetime.now(timezone.utc)
        object_key = f"{settings.device_id}/{ts.strftime('%Y%m%d%H%M%S%f')}_{uuid.uuid4().hex[:8]}"

        # Upload payload to MinIO
        minio_client.put_object(
            bucket,
            object_key,
            BytesIO(payload.payload_bytes),
            length=payload.payload_size_bytes,
            content_type=payload.mime_type,
        )

        batch.append(
            {
                "meta": {
                    "device_id": settings.device_id,
                    "profile": payload.profile_name,
                    "payload_kind": payload.payload_kind,
                },
                "ts": ts,
                "minio_object_key": object_key,
                "payload_size_bytes": payload.payload_size_bytes,
                "width": payload.width,
                "height": payload.height,
                "mime_type": payload.mime_type,
                "codec": payload.codec,
                "duration_ms": payload.duration_ms,
            }
        )

        if len(batch) >= settings.batch_size:
            coll.insert_many(batch, ordered=False)
            inserted += len(batch)
            batch.clear()

    if batch:
        coll.insert_many(batch, ordered=False)
        inserted += len(batch)

    duration = time.perf_counter() - t0
    return inserted, duration


def main() -> None:
    settings = load_settings()
    payload = load_media_payload(settings)

    run_csv_path = settings.result_csv("results_mongo_insert_runs")
    summary_csv_path = settings.result_csv("results_mongo_insert_summary")

    print("MongoDB+MinIO insert benchmark")
    print(describe_settings(settings))
    print(
        f"payload_size={payload.payload_size_bytes} bytes "
        f"({payload.payload_size_mb:.3f} MB/sample)"
    )

    minio_client = open_minio(settings)

    if settings.warmup_rows > 0:
        recreate_mongo_collection(settings)
        recreate_minio_bucket(settings)
        client = MongoClient(settings.mongo_uri)
        try:
            coll = client[settings.mongo_db_name][settings.mongo_collection_name]
            warmup_settings = settings.__class__(
                **{**settings.__dict__, "total_rows": settings.warmup_rows}
            )
            print(f"Warm-up: inserting {settings.warmup_rows} docs...")
            rows_warm, dur_warm = insert_docs(coll, minio_client, settings.minio_bucket, warmup_settings, payload)
            print(f"Warm-up completed: {rows_warm} docs in {dur_warm:.2f} s")
        finally:
            client.close()

    run_durations = []
    run_rows_per_sec = []
    run_mb_per_sec = []
    run_db_sizes_after = []
    run_table_sizes_after = []
    run_storage_amplification = []

    for run_id in range(1, settings.insert_runs + 1):
        recreate_mongo_collection(settings)
        recreate_minio_bucket(settings)
        client = MongoClient(settings.mongo_uri)
        try:
            db = client[settings.mongo_db_name]
            coll = db[settings.mongo_collection_name]

            sizes_before = get_collection_and_db_sizes(db, settings.mongo_collection_name, minio_client, settings.minio_bucket)
            rows_inserted, duration = insert_docs(coll, minio_client, settings.minio_bucket, settings, payload)
            sizes_after = get_collection_and_db_sizes(db, settings.mongo_collection_name, minio_client, settings.minio_bucket)
            rows_in_coll_after = get_row_count(coll)
        finally:
            client.close()

        logical_mb_inserted = bytes_to_mb(rows_inserted * payload.payload_size_bytes)
        rows_per_sec = rows_inserted / duration if duration else 0.0
        logical_mb_per_sec = logical_mb_inserted / duration if duration else 0.0
        table_total_after_mb = bytes_to_mb(sizes_after["table_total_bytes"])
        amplification = (
            table_total_after_mb / logical_mb_inserted if logical_mb_inserted else 0.0
        )

        run_durations.append(duration)
        run_rows_per_sec.append(rows_per_sec)
        run_mb_per_sec.append(logical_mb_per_sec)
        run_db_sizes_after.append(bytes_to_mb(sizes_after["db_bytes"]))
        run_table_sizes_after.append(table_total_after_mb)
        run_storage_amplification.append(amplification)

        print(
            f"Run {run_id}/{settings.insert_runs}: "
            f"{rows_per_sec:.2f} docs/s, {logical_mb_per_sec:.2f} MB/s, "
            f"collection+minio={table_total_after_mb:.2f} MB"
        )

        append_row(
            run_csv_path,
            RUN_FIELDNAMES,
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "engine": ENGINE_NAME,
                "profile": settings.profile_slug,
                "payload_kind": payload.payload_kind,
                "payload_size_bytes": payload.payload_size_bytes,
                "payload_size_mb": round(payload.payload_size_mb, 6),
                "run_id": run_id,
                "total_rows_requested": settings.total_rows,
                "rows_inserted": rows_inserted,
                "batch_size": settings.batch_size,
                "duration_sec": round(duration, 4),
                "rows_per_sec": round(rows_per_sec, 2),
                "logical_mb_inserted": round(logical_mb_inserted, 3),
                "logical_mb_per_sec": round(logical_mb_per_sec, 3),
                "db_size_before_mb": round(bytes_to_mb(sizes_before["db_bytes"]), 3),
                "db_size_after_mb": round(bytes_to_mb(sizes_after["db_bytes"]), 3),
                "table_total_before_mb": round(
                    bytes_to_mb(sizes_before["table_total_bytes"]), 3
                ),
                "table_total_after_mb": round(table_total_after_mb, 3),
                "table_data_before_mb": round(
                    bytes_to_mb(sizes_before["table_data_bytes"]), 3
                ),
                "table_data_after_mb": round(
                    bytes_to_mb(sizes_after["table_data_bytes"]), 3
                ),
                "table_index_before_mb": round(
                    bytes_to_mb(sizes_before["table_index_bytes"]), 3
                ),
                "table_index_after_mb": round(
                    bytes_to_mb(sizes_after["table_index_bytes"]), 3
                ),
                "rows_in_table_after": rows_in_coll_after,
                "table_storage_amplification": round(amplification, 4),
            },
        )

    mean_duration = statistics.mean(run_durations)
    std_duration = statistics.stdev(run_durations) if len(run_durations) > 1 else 0.0
    mean_rows_per_sec = statistics.mean(run_rows_per_sec)
    std_rows_per_sec = (
        statistics.stdev(run_rows_per_sec) if len(run_rows_per_sec) > 1 else 0.0
    )
    mean_mb_per_sec = statistics.mean(run_mb_per_sec)
    std_mb_per_sec = statistics.stdev(run_mb_per_sec) if len(run_mb_per_sec) > 1 else 0.0
    mean_db_after = statistics.mean(run_db_sizes_after)
    std_db_after = statistics.stdev(run_db_sizes_after) if len(run_db_sizes_after) > 1 else 0.0
    mean_table_after = statistics.mean(run_table_sizes_after)
    std_table_after = (
        statistics.stdev(run_table_sizes_after) if len(run_table_sizes_after) > 1 else 0.0
    )
    mean_amplification = statistics.mean(run_storage_amplification)
    std_amplification = (
        statistics.stdev(run_storage_amplification)
        if len(run_storage_amplification) > 1
        else 0.0
    )

    append_row(
        summary_csv_path,
        SUMMARY_FIELDNAMES,
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engine": ENGINE_NAME,
            "profile": settings.profile_slug,
            "payload_kind": payload.payload_kind,
            "payload_size_bytes": payload.payload_size_bytes,
            "payload_size_mb": round(payload.payload_size_mb, 6),
            "warmup_rows": settings.warmup_rows,
            "total_rows_per_run": settings.total_rows,
            "batch_size": settings.batch_size,
            "n_runs": settings.insert_runs,
            "mean_duration_sec": round(mean_duration, 4),
            "std_duration_sec": round(std_duration, 4),
            "mean_rows_per_sec": round(mean_rows_per_sec, 2),
            "std_rows_per_sec": round(std_rows_per_sec, 2),
            "mean_logical_mb_per_sec": round(mean_mb_per_sec, 3),
            "std_logical_mb_per_sec": round(std_mb_per_sec, 3),
            "mean_db_size_after_mb": round(mean_db_after, 3),
            "std_db_size_after_mb": round(std_db_after, 3),
            "mean_table_total_after_mb": round(mean_table_after, 3),
            "std_table_total_after_mb": round(std_table_after, 3),
            "mean_storage_amplification": round(mean_amplification, 4),
            "std_storage_amplification": round(std_amplification, 4),
        },
    )

    print(
        f"Summary: {mean_rows_per_sec:.2f} docs/s, "
        f"{mean_mb_per_sec:.2f} MB/s, "
        f"storage amplification {mean_amplification:.2f}x"
    )


if __name__ == "__main__":
    main()
