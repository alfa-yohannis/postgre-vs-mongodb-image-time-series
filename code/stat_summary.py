import csv
import statistics
from datetime import datetime, timezone

# =========================
# FILE PATHS
# =========================

POSTGRES_INSERT_RUNS = "results_postgres_insert_runs.csv"
MONGO_INSERT_RUNS = "results_mongo_insert_runs.csv"

POSTGRES_AGG_RUNS = "results_postgres_aggregate_runs.csv"
MONGO_AGG_RUNS = "results_mongo_aggregate_runs.csv"

POSTGRES_DRIVER_SUMMARY = "results_postgres_driver_summary.csv"
MONGO_DRIVER_SUMMARY = "results_mongo_driver_summary.csv"

POSTGRES_INSERT_SUMMARY = "results_postgres_insert_summary.csv"
MONGO_INSERT_SUMMARY = "results_mongo_insert_summary.csv"

FINAL_STATS_CSV = "final_stats_summary.csv"


# =========================
# CSV LOADERS
# =========================

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


# =========================
# SUMMARY WRITER
# =========================

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


# =========================
# MAIN
# =========================

def main():
    timestamp = datetime.now(timezone.utc).isoformat()

    # -------------------------------------------------
    # 1) INSERT THROUGHPUT STATS
    # -------------------------------------------------

    pg_insert = load_column_from_csv(POSTGRES_INSERT_RUNS, "rows_per_sec")
    mongo_insert = load_column_from_csv(MONGO_INSERT_RUNS, "rows_per_sec")

    pg_insert_mean = statistics.mean(pg_insert)
    pg_insert_std = statistics.stdev(pg_insert)

    mongo_insert_mean = statistics.mean(mongo_insert)
    mongo_insert_std = statistics.stdev(mongo_insert)

    # -------------------------------------------------
    # 2) AGGREGATION LATENCY STATS
    # -------------------------------------------------

    pg_agg = load_column_from_csv(POSTGRES_AGG_RUNS, "latency_ms")
    mongo_agg = load_column_from_csv(MONGO_AGG_RUNS, "latency_ms")

    pg_agg_mean = statistics.mean(pg_agg)
    pg_agg_std = statistics.stdev(pg_agg)

    mongo_agg_mean = statistics.mean(mongo_agg)
    mongo_agg_std = statistics.stdev(mongo_agg)

    # -------------------------------------------------
    # 3) DRIVER OVERHEAD (ALREADY MEAN±STD)
    # -------------------------------------------------

    pg_driver_mean = load_single_value_from_summary(
        POSTGRES_DRIVER_SUMMARY, "mean_latency_ms"
    )
    pg_driver_std = load_single_value_from_summary(
        POSTGRES_DRIVER_SUMMARY, "std_latency_ms"
    )

    mongo_driver_mean = load_single_value_from_summary(
        MONGO_DRIVER_SUMMARY, "mean_latency_ms"
    )
    mongo_driver_std = load_single_value_from_summary(
        MONGO_DRIVER_SUMMARY, "std_latency_ms"
    )

    # -------------------------------------------------
    # 4) STORAGE SIZE (MEAN ONLY)
    # -------------------------------------------------

    pg_table_mb = load_single_value_from_summary(
        POSTGRES_INSERT_SUMMARY, "mean_table_total_after_mb"
    )
    pg_db_mb = load_single_value_from_summary(
        POSTGRES_INSERT_SUMMARY, "mean_db_size_after_mb"
    )

    mongo_table_mb = load_single_value_from_summary(
        MONGO_INSERT_SUMMARY, "mean_table_total_after_mb"
    )
    mongo_db_mb = load_single_value_from_summary(
        MONGO_INSERT_SUMMARY, "mean_db_size_after_mb"
    )

    # -------------------------------------------------
    # PRINT FINAL CONSOLE SUMMARY
    # -------------------------------------------------

    print("\n==============================")
    print("FINAL STATISTICAL SUMMARY")
    print("==============================")

    print("\n[INSERT THROUGHPUT] rows/sec")
    print(f"PostgreSQL : {pg_insert_mean:.2f} ± {pg_insert_std:.2f}")
    print(f"MongoDB    : {mongo_insert_mean:.2f} ± {mongo_insert_std:.2f}")

    print("\n[AGGREGATION LATENCY] ms")
    print(f"PostgreSQL : {pg_agg_mean:.2f} ± {pg_agg_std:.2f}")
    print(f"MongoDB    : {mongo_agg_mean:.2f} ± {mongo_agg_std:.2f}")

    print("\n[DRIVER ROUNDTRIP] ms")
    print(f"PostgreSQL : {pg_driver_mean:.4f} ± {pg_driver_std:.4f}")
    print(f"MongoDB    : {mongo_driver_mean:.4f} ± {mongo_driver_std:.4f}")

    print("\n[STORAGE SIZE] MB")
    print(f"PostgreSQL Table : {pg_table_mb:.2f}")
    print(f"PostgreSQL DB    : {pg_db_mb:.2f}")
    print(f"MongoDB Table    : {mongo_table_mb:.2f}")
    print(f"MongoDB DB       : {mongo_db_mb:.2f}")

    print("==============================\n")

    # -------------------------------------------------
    # SAVE TO FINAL CSV
    # -------------------------------------------------

    final_row = {
        "timestamp": timestamp,

        # Insert
        "pg_insert_mean": round(pg_insert_mean, 2),
        "pg_insert_std": round(pg_insert_std, 2),
        "mongo_insert_mean": round(mongo_insert_mean, 2),
        "mongo_insert_std": round(mongo_insert_std, 2),

        # Aggregation
        "pg_agg_mean": round(pg_agg_mean, 2),
        "pg_agg_std": round(pg_agg_std, 2),
        "mongo_agg_mean": round(mongo_agg_mean, 2),
        "mongo_agg_std": round(mongo_agg_std, 2),

        # Driver
        "pg_driver_mean": round(pg_driver_mean, 4),
        "pg_driver_std": round(pg_driver_std, 4),
        "mongo_driver_mean": round(mongo_driver_mean, 4),
        "mongo_driver_std": round(mongo_driver_std, 4),

        # Storage
        "pg_table_mb": round(pg_table_mb, 2),
        "pg_db_mb": round(pg_db_mb, 2),
        "mongo_table_mb": round(mongo_table_mb, 2),
        "mongo_db_mb": round(mongo_db_mb, 2),
    }

    append_final_summary(final_row)

    print(f"✅ Final statistics saved to: {FINAL_STATS_CSV}\n")


if __name__ == "__main__":
    main()
