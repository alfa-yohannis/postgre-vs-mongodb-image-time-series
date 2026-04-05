from benchmark_config import describe_settings, load_settings
from database_setup import (
    ensure_minio_bucket,
    ensure_postgres_minio_schema,
    ensure_postgres_schema,
    wait_for_minio,
    wait_for_postgres,
)


def main() -> None:
    settings = load_settings()
    print("Preparing benchmark databases...")
    print(describe_settings(settings))

    wait_for_postgres(settings)
    wait_for_minio(settings)

    ensure_postgres_schema(settings)
    ensure_postgres_minio_schema(settings)
    ensure_minio_bucket(settings)

    print("PostgreSQL and MinIO are ready for the benchmark.")


if __name__ == "__main__":
    main()
