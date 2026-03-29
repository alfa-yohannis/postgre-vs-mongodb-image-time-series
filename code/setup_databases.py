from benchmark_config import describe_settings, load_settings
from database_setup import (
    ensure_mongo_collection,
    ensure_postgres_schema,
    wait_for_mongodb,
    wait_for_postgres,
)


def main() -> None:
    settings = load_settings()
    print("Preparing benchmark databases...")
    print(describe_settings(settings))

    wait_for_postgres(settings)
    wait_for_mongodb(settings)

    ensure_postgres_schema(settings)
    ensure_mongo_collection(settings)

    print("PostgreSQL and MongoDB are ready for the benchmark.")


if __name__ == "__main__":
    main()
