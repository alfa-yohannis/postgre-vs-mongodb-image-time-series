import csv
import statistics
from datetime import datetime, timezone


POSTGRES_INSERT_RUNS = "results_postgres_insert_runs.csv"
POSTGRES_MINIO_INSERT_RUNS = "results_postgres_minio_insert_runs.csv"

POSTGRES_RETRIEVAL_RUNS = "results_postgres_point_read_runs.csv"
POSTGRES_MINIO_RETRIEVAL_RUNS = "results_postgres_minio_point_read_runs.csv"

POSTGRES_DRIVER_SUMMARY = "results_postgres_driver_summary.csv"
MINIO_DRIVER_SUMMARY = "results_minio_driver_summary.csv"

POSTGRES_INSERT_SUMMARY = "results_postgres_insert_summary.csv"
POSTGRES_MINIO_INSERT_SUMMARY = "results_postgres_minio_insert_summary.csv"

FINAL_STATS_CSV = "final_stats_summary.csv"


def load_column_from_csv(path, column_name):
    values = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            values.append(float(row[column_name]))
    return values


def load_single_value_from_summary(path, column_name):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            raise RuntimeError(f"No data in {path}")
        return float(rows[-1][column_name])


def append_final_summary(row_dict):
    fieldnames = list(row_dict.keys())
    file_exists = False
    try:
        with open(FINAL_STATS_CSV):
            file_exists = True
    except FileNotFoundError:
        pass

    with open(FINAL_STATS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_dict)


def main():
    timestamp = datetime.now(timezone.utc).isoformat()

    # INSERT THROUGHPUT
    pg_insert = load_column_from_csv(POSTGRES_INSERT_RUNS, "rows_per_sec")
    pg_minio_insert = load_column_from_csv(POSTGRES_MINIO_INSERT_RUNS, "rows_per_sec")

    pg_insert_mean = statistics.mean(pg_insert)
    pg_insert_std = statistics.stdev(pg_insert)
    pg_minio_insert_mean = statistics.mean(pg_minio_insert)
    pg_minio_insert_std = statistics.stdev(pg_minio_insert)

    # RETRIEVAL LATENCY
    pg_retrieval = load_column_from_csv(POSTGRES_RETRIEVAL_RUNS, "latency_ms")
    pg_minio_retrieval = load_column_from_csv(POSTGRES_MINIO_RETRIEVAL_RUNS, "latency_ms")

    pg_retrieval_mean = statistics.mean(pg_retrieval)
    pg_retrieval_std = statistics.stdev(pg_retrieval)
    pg_minio_retrieval_mean = statistics.mean(pg_minio_retrieval)
    pg_minio_retrieval_std = statistics.stdev(pg_minio_retrieval)

    # DRIVER OVERHEAD
    pg_driver_mean = load_single_value_from_summary(POSTGRES_DRIVER_SUMMARY, "mean_latency_ms")
    pg_driver_std = load_single_value_from_summary(POSTGRES_DRIVER_SUMMARY, "std_latency_ms")
    minio_driver_mean = load_single_value_from_summary(MINIO_DRIVER_SUMMARY, "mean_latency_ms")
    minio_driver_std = load_single_value_from_summary(MINIO_DRIVER_SUMMARY, "std_latency_ms")

    # STORAGE SIZE
    pg_table_mb = load_single_value_from_summary(POSTGRES_INSERT_SUMMARY, "mean_table_total_after_mb")
    pg_db_mb = load_single_value_from_summary(POSTGRES_INSERT_SUMMARY, "mean_db_size_after_mb")
    pg_minio_table_mb = load_single_value_from_summary(POSTGRES_MINIO_INSERT_SUMMARY, "mean_table_total_after_mb")
    pg_minio_db_mb = load_single_value_from_summary(POSTGRES_MINIO_INSERT_SUMMARY, "mean_db_size_after_mb")

    print("\n==============================")
    print("FINAL STATISTICAL SUMMARY")
    print("==============================")

    print("\n[INSERT THROUGHPUT] rows/sec")
    print(f"PG (PostgreSQL BYTEA) : {pg_insert_mean:.2f} +/- {pg_insert_std:.2f}")
    print(f"PM (PostgreSQL+MinIO) : {pg_minio_insert_mean:.2f} +/- {pg_minio_insert_std:.2f}")

    print("\n[RETRIEVAL LATENCY] ms")
    print(f"PG (PostgreSQL BYTEA) : {pg_retrieval_mean:.2f} +/- {pg_retrieval_std:.2f}")
    print(f"PM (PostgreSQL+MinIO) : {pg_minio_retrieval_mean:.2f} +/- {pg_minio_retrieval_std:.2f}")

    print("\n[DRIVER ROUNDTRIP] ms")
    print(f"PostgreSQL            : {pg_driver_mean:.4f} +/- {pg_driver_std:.4f}")
    print(f"MinIO                 : {minio_driver_mean:.4f} +/- {minio_driver_std:.4f}")

    print("\n[STORAGE SIZE] MB")
    print(f"PG Table              : {pg_table_mb:.2f}")
    print(f"PG DB                 : {pg_db_mb:.2f}")
    print(f"PM Table              : {pg_minio_table_mb:.2f}")
    print(f"PM DB                 : {pg_minio_db_mb:.2f}")

    print("==============================\n")

    final_row = {
        "timestamp": timestamp,
        "pg_insert_mean": round(pg_insert_mean, 2),
        "pg_insert_std": round(pg_insert_std, 2),
        "pg_minio_insert_mean": round(pg_minio_insert_mean, 2),
        "pg_minio_insert_std": round(pg_minio_insert_std, 2),
        "pg_retrieval_mean": round(pg_retrieval_mean, 2),
        "pg_retrieval_std": round(pg_retrieval_std, 2),
        "pg_minio_retrieval_mean": round(pg_minio_retrieval_mean, 2),
        "pg_minio_retrieval_std": round(pg_minio_retrieval_std, 2),
        "pg_driver_mean": round(pg_driver_mean, 4),
        "pg_driver_std": round(pg_driver_std, 4),
        "minio_driver_mean": round(minio_driver_mean, 4),
        "minio_driver_std": round(minio_driver_std, 4),
        "pg_table_mb": round(pg_table_mb, 2),
        "pg_db_mb": round(pg_db_mb, 2),
        "pg_minio_table_mb": round(pg_minio_table_mb, 2),
        "pg_minio_db_mb": round(pg_minio_db_mb, 2),
    }

    append_final_summary(final_row)
    print(f"Final statistics saved to: {FINAL_STATS_CSV}\n")


if __name__ == "__main__":
    main()
