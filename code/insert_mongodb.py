import os
from io import BytesIO
from datetime import datetime, timezone
import time
import csv
import statistics

from PIL import Image
from pymongo import MongoClient


# =========================
# CONFIGURATION
# =========================

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "iot_ts"          # or "iot_ts_mongo" if you prefer separation
COLL_NAME = "sensor_frames"

IMAGE_PATH = "assets/Schwarzsee.jpg"  # single source image
DEVICE_ID = 1

# Benchmark parameters
WARMUP_ROWS = 10000        # rows for warm-up (not logged)
TOTAL_ROWS = 200000        # rows per measured run
BATCH_SIZE = 1000          # batch size for both warm-up and measured runs
N_RUNS = 10                 # how many measured runs

TARGET_SIZE = (320, 240)
MIME_TYPE = "image/jpeg"

RUN_CSV_PATH = "results_mongo_insert_runs.csv"
SUMMARY_CSV_PATH = "results_mongo_insert_summary.csv"
ENGINE_NAME = "mongodb_timeseries"  # label for comparison with PostgreSQL later


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

def get_collection_and_db_sizes(db, coll_name: str):
    """
    Return collection and DB sizes in bytes, mapped to the same keys
    as the PostgreSQL helper for easy comparison.

    We use storageSize (allocated data on disk) + totalIndexSize for both
    collection and database. This is analogous to PostgreSQL's
    pg_total_relation_size (data + index + toast), and excludes
    MongoDB journal/WiredTiger log files.
    """
    dbstats = db.command("dbStats")
    collstats = db.command("collStats", coll_name)

    # Collection-level sizes (allocated on disk)
    # 'storageSize' = allocated bytes for this collection (data, without indexes)
    # 'size'        = logical data size, may be smaller than storageSize
    coll_storage_bytes = collstats.get("storageSize", collstats.get("size", 0))
    coll_index_bytes = collstats.get("totalIndexSize", 0)

    coll_total_bytes = coll_storage_bytes + coll_index_bytes

    # Database-level sizes (allocated on disk)
    # 'storageSize' = sum of collection storage sizes
    # 'indexSize'   = sum of index sizes
    db_storage_bytes = dbstats.get("storageSize", dbstats.get("dataSize", 0))
    db_index_bytes = dbstats.get("indexSize", 0)
    db_total_bytes = db_storage_bytes + db_index_bytes

    return {
        # Keep key names identical to PostgreSQL version
        "table_total_bytes": coll_total_bytes,      # collection data + indexes
        "table_data_bytes": coll_storage_bytes,     # allocated collection data
        "table_index_bytes": coll_index_bytes,      # collection indexes
        "db_bytes": db_total_bytes,                 # db data + indexes (no journal)
    }


def get_row_count(coll):
    # Exact count; for very huge collections you might switch to estimated_document_count()
    return coll.count_documents({})


def bytes_to_mb(b):
    return b / (1024 * 1024)


# =========================
# CSV LOGGING
# (same fields as PostgreSQL version for easy side-by-side plots)
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

def insert_docs(coll, frame_bytes, total_rows, batch_size):
    """
    Insert total_rows documents into MongoDB collection.
    Returns (rows_inserted, duration_sec).
    """
    t0 = time.perf_counter()
    batch = []
    inserted = 0

    while inserted < total_rows:
        ts = datetime.now(timezone.utc)

        doc = {
            "device_id": DEVICE_ID,
            "ts": ts,
            "frame_data": frame_bytes,  # stored as BinData
            "width": TARGET_SIZE[0],
            "height": TARGET_SIZE[1],
            "mime_type": MIME_TYPE,
        }

        batch.append(doc)

        if len(batch) >= batch_size:
            coll.insert_many(batch)
            inserted += len(batch)
            batch.clear()

    # final partial batch
    if batch:
        coll.insert_many(batch)
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

    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    coll = db[COLL_NAME]

    # 1) Ensure empty collection before everything
    print("Clearing collection before benchmark...")
    coll.delete_many({})

    # 2) Warm-up (not logged to CSV)
    if WARMUP_ROWS > 0:
        print(f"Warm-up: inserting {WARMUP_ROWS} docs (not logged)...")
        rows_warm, dur_warm = insert_docs(coll, frame_bytes, WARMUP_ROWS, BATCH_SIZE)
        print(f"Warm-up done: {rows_warm} docs in {dur_warm:.2f} sec\n")

        # Optional: empty collection again after warm-up
        print("Clearing collection after warm-up...")
        coll.delete_many({})

    # Storage for per-run stats (for mean/std)
    run_durations = []
    run_throughputs = []
    run_db_sizes_after = []
    run_table_sizes_after = []

    # 3) Measured runs
    for run_id in range(1, N_RUNS + 1):
        print(f"\n===== RUN {run_id}/{N_RUNS} =====")

        # Empty collection before each run
        print("Clearing collection before run...")
        coll.delete_many({})

        # Measure sizes BEFORE
        sizes_before = get_collection_and_db_sizes(db, COLL_NAME)

        # Do the inserts
        rows_inserted, duration = insert_docs(coll, frame_bytes, TOTAL_ROWS, BATCH_SIZE)
        rows_per_sec = rows_inserted / duration if duration > 0 else 0.0

        # Measure sizes AFTER
        sizes_after = get_collection_and_db_sizes(db, COLL_NAME)
        rows_in_coll_after = get_row_count(coll)

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
        print(f"Total Docs  : {rows_inserted}")
        print(f"Batch Size  : {BATCH_SIZE}")
        print(f"Total Time  : {duration:.2f} seconds")
        print(f"Throughput  : {rows_per_sec:.2f} docs/sec")
        print(f"DB Size     : {bytes_to_mb(sizes_before['db_bytes']):.2f} MB -> "
              f"{bytes_to_mb(sizes_after['db_bytes']):.2f} MB")
        print(f"Coll Total  : {bytes_to_mb(sizes_before['table_total_bytes']):.2f} MB -> "
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
            "rows_in_table_after": rows_in_coll_after,
        }

        append_run_to_csv(row)
        print(f"Run metrics appended to {RUN_CSV_PATH}")

    # Close DB connection
    client.close()

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
    print(f"Docs per run        : {TOTAL_ROWS}")
    print(f"Batch size          : {BATCH_SIZE}")
    print("--------------------------------")
    print(f"Duration (s)        : {mean_duration:.2f} ± {std_duration:.2f}")
    print(f"Throughput (docs/s) : {mean_throughput:.2f} ± {std_throughput:.2f}")
    print(f"DB size after (MB)  : {mean_db_after:.2f} ± {std_db_after:.2f}")
    print(f"Coll size after(MB) : {mean_table_after:.2f} ± {std_table_after:.2f}")
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
