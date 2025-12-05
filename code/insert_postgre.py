import os
from io import BytesIO
from datetime import datetime, timezone
import time
import csv
import statistics

from PIL import Image
import psycopg2
from psycopg2.extras import execute_batch

# =========================
# CONFIGURATION
# =========================

DB_CONFIG = {
    "dbname": "iot_ts",
    "user": "postgres",
    "password": "1234",   # adjust if needed
    "host": "localhost",
    "port": 5432,
}

IMAGE_PATH = "assets/Schwarzsee.jpg"  # single source image
DEVICE_ID = 1

# Benchmark parameters
WARMUP_ROWS = 10000        # rows for warm-up (not logged)
TOTAL_ROWS = 200000        # rows per measured run
BATCH_SIZE = 1000          # batch size for both warm-up and measured runs
N_RUNS = 10                  # how many measured runs

TARGET_SIZE = (320, 240)
MIME_TYPE = "image/jpeg"

RUN_CSV_PATH = "results_postgres_insert_runs.csv"
SUMMARY_CSV_PATH = "results_postgres_insert_summary.csv"
ENGINE_NAME = "postgres+timescaledb"  # label for comparison with MongoDB later


# =========================
# IMAGE PREPARATION
# =========================

def load_and_prepare_single_image(path: str) -> bytes:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image not found: {path}")

    img = Image.open(path).convert("RGB")
    img = img.resize(TARGET_SIZE)

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


# =========================
# METRICS HELPERS (SIZE, ROW COUNT)
# =========================

def get_table_and_db_sizes(cur):
    """
    Return table/collection and DB sizes in bytes.

    For TimescaleDB hypertables, use hypertable_size('sensor_frames')
    which returns the total size of the hypertable (including all chunks).
    For plain PostgreSQL tables, fall back to pg_total_relation_size /
    pg_relation_size / pg_indexes_size.

    NOTE: On this Timescale version, hypertable_size() returns a single
    BIGINT column (total bytes), so we approximate data/index split by
    treating all of it as "data" and setting index_bytes = 0. For the
    experiment, we mainly care about table_total_bytes for comparison
    with MongoDB.
    """
    # 1) Check if TimescaleDB extension is installed
    cur.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb');"
    )
    (has_ts,) = cur.fetchone()

    is_hypertable = False

    # 2) If TimescaleDB is present, check if sensor_frames is a hypertable
    if has_ts:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT 1
                FROM _timescaledb_catalog.hypertable
                WHERE table_name = 'sensor_frames'
                  AND schema_name = 'public'
            );
            """
        )
        (is_hypertable,) = cur.fetchone()

    if has_ts and is_hypertable:
        # Use Timescale's hypertable_size to include all chunks.
        # It returns a single BIGINT (total size in bytes).
        cur.execute("SELECT hypertable_size('sensor_frames');")
        (total_bytes,) = cur.fetchone()

        table_total_bytes = total_bytes or 0
        table_data_bytes = table_total_bytes  # we don't have a split; treat as data
        table_index_bytes = 0                 # unknown; not critical for this study
    else:
        # Plain PostgreSQL table: use standard relation size functions
        cur.execute(
            """
            SELECT
                COALESCE(pg_total_relation_size('sensor_frames'), 0), -- total (data+index+toast)
                COALESCE(pg_relation_size('sensor_frames'), 0),       -- table data only
                COALESCE(pg_indexes_size('sensor_frames'), 0)         -- indexes only
            """
        )
        table_total_bytes, table_data_bytes, table_index_bytes = cur.fetchone()

    # DB size (logical, without WAL)
    cur.execute("SELECT pg_database_size(current_database());")
    (db_bytes,) = cur.fetchone()

    return {
        "table_total_bytes": table_total_bytes,
        "table_data_bytes": table_data_bytes,
        "table_index_bytes": table_index_bytes,
        "db_bytes": db_bytes,
    }




def get_row_count(cur):
    cur.execute("SELECT COUNT(*) FROM sensor_frames;")
    (count,) = cur.fetchone()
    return count


def bytes_to_mb(b):
    return b / (1024 * 1024)


# =========================
# CSV LOGGING
# =========================

def append_run_to_csv(row_dict):
    file_exists = os.path.exists(RUN_CSV_PATH)
    fieldnames = [
        "timestamp",
        "run_id",
        "engine",
        "total_rows_requested",
        "rows_inserted",
        "batch_size",
        "duration_sec",
        "rows_per_sec",
        "db_size_before_mb",
        "db_size_after_mb",
        "table_total_before_mb",
        "table_total_after_mb",
        "table_data_before_mb",
        "table_data_after_mb",
        "table_index_before_mb",
        "table_index_after_mb",
        "rows_in_table_after",
    ]

    with open(RUN_CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_dict)


def append_summary_to_csv(summary_dict):
    file_exists = os.path.exists(SUMMARY_CSV_PATH)
    fieldnames = [
        "timestamp",
        "engine",
        "warmup_rows",
        "total_rows_per_run",
        "batch_size",
        "n_runs",
        "mean_duration_sec",
        "std_duration_sec",
        "mean_rows_per_sec",
        "std_rows_per_sec",
        "mean_db_size_after_mb",
        "std_db_size_after_mb",
        "mean_table_total_after_mb",
        "std_table_total_after_mb",
    ]

    with open(SUMMARY_CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(summary_dict)


# =========================
# INSERT HELPER (USED FOR WARMUP & RUNS)
# =========================

def insert_rows(cur, frame_bytes, total_rows, batch_size):
    """
    Insert total_rows rows using the given cursor.
    Returns (rows_inserted, duration_sec).
    """
    t0 = time.perf_counter()
    batch = []
    inserted = 0

    while inserted < total_rows:
        ts = datetime.now(timezone.utc)

        batch.append(
            (
                DEVICE_ID,
                ts,
                psycopg2.Binary(frame_bytes),
                TARGET_SIZE[0],
                TARGET_SIZE[1],
                MIME_TYPE,
            )
        )

        if len(batch) >= batch_size:
            execute_batch(
                cur,
                """
                INSERT INTO sensor_frames
                    (device_id, ts, frame_data, width, height, mime_type)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                batch,
            )
            inserted += len(batch)
            batch.clear()

    # final partial batch
    if batch:
        execute_batch(
            cur,
            """
            INSERT INTO sensor_frames
                (device_id, ts, frame_data, width, height, mime_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            batch,
        )
        inserted += len(batch)

    t1 = time.perf_counter()
    duration = t1 - t0
    return inserted, duration


# =========================
# MAIN LOGIC
# =========================

def main():
    # Prepare image bytes once
    frame_bytes = load_and_prepare_single_image(IMAGE_PATH)

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()

    # 1) Ensure empty table before everything
    print("Truncating table before benchmark...")
    cur.execute("TRUNCATE TABLE sensor_frames RESTART IDENTITY;")
    conn.commit()

    # 2) Warm-up (not logged to CSV)
    if WARMUP_ROWS > 0:
        print(f"Warm-up: inserting {WARMUP_ROWS} rows (not logged)...")
        rows_warm, dur_warm = insert_rows(cur, frame_bytes, WARMUP_ROWS, BATCH_SIZE)
        conn.commit()
        print(f"Warm-up done: {rows_warm} rows in {dur_warm:.2f} sec\n")

        # Optional: empty table again after warm-up
        print("Truncating table after warm-up...")
        cur.execute("TRUNCATE TABLE sensor_frames RESTART IDENTITY;")
        conn.commit()

    # Storage for per-run stats (for mean/std)
    run_durations = []
    run_throughputs = []
    run_db_sizes_after = []
    run_table_sizes_after = []

    # 3) Measured runs
    for run_id in range(1, N_RUNS + 1):
        print(f"\n===== RUN {run_id}/{N_RUNS} =====")

        # Empty table before each run
        print("Truncating table before run...")
        cur.execute("TRUNCATE TABLE sensor_frames RESTART IDENTITY;")
        conn.commit()

        # Measure sizes BEFORE
        sizes_before = get_table_and_db_sizes(cur)

        # Do the inserts
        rows_inserted, duration = insert_rows(cur, frame_bytes, TOTAL_ROWS, BATCH_SIZE)
        conn.commit()

        rows_per_sec = rows_inserted / duration if duration > 0 else 0.0

        # Measure sizes AFTER
        sizes_after = get_table_and_db_sizes(cur)
        rows_in_table_after = get_row_count(cur)

        # Collect for summary stats
        run_durations.append(duration)
        run_throughputs.append(rows_per_sec)
        run_db_sizes_after.append(bytes_to_mb(sizes_after["db_bytes"]))
        run_table_sizes_after.append(bytes_to_mb(sizes_after["table_total_bytes"]))

        # Print to console
        print("\nRUN RESULT")
        print("------------------------------")
        print(f"Engine      : {ENGINE_NAME}")
        print(f"Run ID      : {run_id}")
        print(f"Total Rows  : {rows_inserted}")
        print(f"Batch Size  : {BATCH_SIZE}")
        print(f"Total Time  : {duration:.2f} seconds")
        print(f"Throughput  : {rows_per_sec:.2f} rows/sec")
        print(f"DB Size     : {bytes_to_mb(sizes_before['db_bytes']):.2f} MB -> "
              f"{bytes_to_mb(sizes_after['db_bytes']):.2f} MB")
        print(f"Table Total : {bytes_to_mb(sizes_before['table_total_bytes']):.2f} MB -> "
              f"{bytes_to_mb(sizes_after['table_total_bytes']):.2f} MB")
        print("------------------------------")

        # Prepare per-run CSV row
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "engine": ENGINE_NAME,
            "total_rows_requested": TOTAL_ROWS,
            "rows_inserted": rows_inserted,
            "batch_size": BATCH_SIZE,
            "duration_sec": round(duration, 4),
            "rows_per_sec": round(rows_per_sec, 2),
            "db_size_before_mb": round(bytes_to_mb(sizes_before["db_bytes"]), 3),
            "db_size_after_mb": round(bytes_to_mb(sizes_after["db_bytes"]), 3),
            "table_total_before_mb": round(bytes_to_mb(sizes_before["table_total_bytes"]), 3),
            "table_total_after_mb": round(bytes_to_mb(sizes_after["table_total_bytes"]), 3),
            "table_data_before_mb": round(bytes_to_mb(sizes_before["table_data_bytes"]), 3),
            "table_data_after_mb": round(bytes_to_mb(sizes_after["table_data_bytes"]), 3),
            "table_index_before_mb": round(bytes_to_mb(sizes_before["table_index_bytes"]), 3),
            "table_index_after_mb": round(bytes_to_mb(sizes_after["table_index_bytes"]), 3),
            "rows_in_table_after": rows_in_table_after,
        }

        append_run_to_csv(row)
        print(f"Run metrics appended to {RUN_CSV_PATH}")

    # Close DB connection
    cur.close()
    conn.close()

    # =========================
    # SUMMARY STATISTICS
    # =========================

    mean_duration = statistics.mean(run_durations)
    std_duration = statistics.stdev(run_durations) if len(run_durations) > 1 else 0.0

    mean_throughput = statistics.mean(run_throughputs)
    std_throughput = statistics.stdev(run_throughputs) if len(run_throughputs) > 1 else 0.0

    mean_db_after = statistics.mean(run_db_sizes_after)
    std_db_after = statistics.stdev(run_db_sizes_after) if len(run_db_sizes_after) > 1 else 0.0

    mean_table_after = statistics.mean(run_table_sizes_after)
    std_table_after = statistics.stdev(run_table_sizes_after) if len(run_table_sizes_after) > 1 else 0.0

    print("\n==============================")
    print("FINAL SUMMARY (MEAN ± STD DEV)")
    print("==============================")
    print(f"Engine              : {ENGINE_NAME}")
    print(f"Runs                : {N_RUNS}")
    print(f"Rows per run        : {TOTAL_ROWS}")
    print(f"Batch size          : {BATCH_SIZE}")
    print("--------------------------------")
    print(f"Duration (s)        : {mean_duration:.2f} ± {std_duration:.2f}")
    print(f"Throughput (rows/s) : {mean_throughput:.2f} ± {std_throughput:.2f}")
    print(f"DB size after (MB)  : {mean_db_after:.2f} ± {std_db_after:.2f}")
    print(f"Table size after(MB): {mean_table_after:.2f} ± {std_table_after:.2f}")
    print("==============================\n")

    # Prepare summary CSV row
    summary_row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine": ENGINE_NAME,
        "warmup_rows": WARMUP_ROWS,
        "total_rows_per_run": TOTAL_ROWS,
        "batch_size": BATCH_SIZE,
        "n_runs": N_RUNS,
        "mean_duration_sec": round(mean_duration, 4),
        "std_duration_sec": round(std_duration, 4),
        "mean_rows_per_sec": round(mean_throughput, 2),
        "std_rows_per_sec": round(std_throughput, 2),
        "mean_db_size_after_mb": round(mean_db_after, 3),
        "std_db_size_after_mb": round(std_db_after, 3),
        "mean_table_total_after_mb": round(mean_table_after, 3),
        "std_table_total_after_mb": round(std_table_after, 3),
    }

    append_summary_to_csv(summary_row)
    print(f"Summary appended to {SUMMARY_CSV_PATH}")


if __name__ == "__main__":
    main()
