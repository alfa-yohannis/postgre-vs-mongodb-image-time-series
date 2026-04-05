from __future__ import annotations

import statistics
import time
import uuid
from datetime import datetime, timezone
from io import BytesIO

import psycopg2
from psycopg2.extras import execute_batch

from benchmark_config import describe_settings, load_settings
from benchmark_utils import append_row, bytes_to_mb
from database_setup import open_minio, recreate_minio_bucket, recreate_postgres_minio_table
from media_payloads import load_media_payload


ENGINE_NAME = "postgresql+timescaledb+minio"

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


def get_table_and_db_sizes(cur, table_name: str, minio_client, bucket: str) -> dict[str, int]:
    try:
        cur.execute(
            f"""
            SELECT
                COALESCE(table_bytes, 0),
                COALESCE(index_bytes, 0),
                COALESCE(toast_bytes, 0),
                COALESCE(total_bytes, 0)
            FROM hypertable_detailed_size('{table_name}');
            """
        )
        table_bytes, index_bytes, toast_bytes, total_bytes = cur.fetchone()
        table_data_bytes = table_bytes + toast_bytes
        table_total_bytes = total_bytes
    except psycopg2.Error:
        cur.connection.rollback()
        cur.execute(
            f"""
            SELECT
                COALESCE(pg_total_relation_size('{table_name}'), 0),
                COALESCE(pg_relation_size('{table_name}'), 0),
                COALESCE(pg_indexes_size('{table_name}'), 0)
            """
        )
        table_total_bytes, table_data_bytes, index_bytes = cur.fetchone()

    cur.execute("SELECT pg_database_size(current_database());")
    (db_bytes,) = cur.fetchone()

    minio_bytes = 0
    try:
        for obj in minio_client.list_objects(bucket, recursive=True):
            minio_bytes += obj.size
    except Exception:
        pass

    return {
        "table_total_bytes": int(table_total_bytes) + minio_bytes,
        "table_data_bytes": int(table_data_bytes) + minio_bytes,
        "table_index_bytes": int(index_bytes),
        "db_bytes": int(db_bytes) + minio_bytes,
    }


def get_row_count(cur, table_name: str) -> int:
    cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    (count,) = cur.fetchone()
    return int(count)


def insert_rows(cur, minio_client, bucket, settings, payload) -> tuple[int, float]:
    table_name = settings.postgres_minio_table_name
    t0 = time.perf_counter()
    batch = []
    inserted = 0

    while inserted < settings.total_rows:
        ts = datetime.now(timezone.utc)
        object_key = f"{settings.device_id}/{ts.strftime('%Y%m%d%H%M%S%f')}_{uuid.uuid4().hex[:8]}"

        minio_client.put_object(
            bucket,
            object_key,
            BytesIO(payload.payload_bytes),
            length=payload.payload_size_bytes,
            content_type=payload.mime_type,
        )

        batch.append(
            (
                settings.device_id,
                ts,
                payload.profile_name,
                payload.payload_kind,
                object_key,
                payload.payload_size_bytes,
                payload.width,
                payload.height,
                payload.mime_type,
                payload.codec,
                payload.duration_ms,
            )
        )

        if len(batch) >= settings.batch_size:
            execute_batch(
                cur,
                f"""
                INSERT INTO {table_name} (
                    device_id,
                    ts,
                    profile_name,
                    payload_kind,
                    minio_object_key,
                    payload_size_bytes,
                    width,
                    height,
                    mime_type,
                    codec,
                    duration_ms
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                batch,
            )
            inserted += len(batch)
            batch.clear()

    if batch:
        execute_batch(
            cur,
            f"""
            INSERT INTO {table_name} (
                device_id,
                ts,
                profile_name,
                payload_kind,
                minio_object_key,
                payload_size_bytes,
                width,
                height,
                mime_type,
                codec,
                duration_ms
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            batch,
        )
        inserted += len(batch)

    duration = time.perf_counter() - t0
    return inserted, duration


def main() -> None:
    settings = load_settings()
    payload = load_media_payload(settings)
    minio_client = open_minio(settings)
    table_name = settings.postgres_minio_table_name

    run_csv_path = settings.result_csv("results_postgres_minio_insert_runs")
    summary_csv_path = settings.result_csv("results_postgres_minio_insert_summary")

    print("PostgreSQL+MinIO insert benchmark")
    print(describe_settings(settings))
    print(
        f"payload_size={payload.payload_size_bytes} bytes "
        f"({payload.payload_size_mb:.3f} MB/sample)"
    )

    if settings.warmup_rows > 0:
        recreate_postgres_minio_table(settings)
        recreate_minio_bucket(settings)
        conn = psycopg2.connect(**settings.postgres_config)
        conn.autocommit = False
        try:
            with conn.cursor() as cur:
                warmup_settings = settings.__class__(
                    **{
                        **settings.__dict__,
                        "total_rows": settings.warmup_rows,
                        "batch_size": settings.batch_size,
                    }
                )
                print(f"Warm-up: inserting {settings.warmup_rows} rows...")
                rows_warm, dur_warm = insert_rows(cur, minio_client, settings.minio_bucket, warmup_settings, payload)
                conn.commit()
                print(f"Warm-up completed: {rows_warm} rows in {dur_warm:.2f} s")
        finally:
            conn.close()

    run_durations = []
    run_rows_per_sec = []
    run_mb_per_sec = []
    run_db_sizes_after = []
    run_table_sizes_after = []
    run_storage_amplification = []

    for run_id in range(1, settings.insert_runs + 1):
        recreate_postgres_minio_table(settings)
        recreate_minio_bucket(settings)
        conn = psycopg2.connect(**settings.postgres_config)
        conn.autocommit = False

        try:
            with conn.cursor() as cur:
                sizes_before = get_table_and_db_sizes(cur, table_name, minio_client, settings.minio_bucket)
                rows_inserted, duration = insert_rows(cur, minio_client, settings.minio_bucket, settings, payload)
                conn.commit()
                sizes_after = get_table_and_db_sizes(cur, table_name, minio_client, settings.minio_bucket)
                rows_in_table_after = get_row_count(cur, table_name)
        finally:
            conn.close()

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
            f"{rows_per_sec:.2f} rows/s, {logical_mb_per_sec:.2f} MB/s, "
            f"table+minio={table_total_after_mb:.2f} MB"
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
                "rows_in_table_after": rows_in_table_after,
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
        f"Summary: {mean_rows_per_sec:.2f} rows/s, "
        f"{mean_mb_per_sec:.2f} MB/s, "
        f"storage amplification {mean_amplification:.2f}x"
    )


if __name__ == "__main__":
    main()
