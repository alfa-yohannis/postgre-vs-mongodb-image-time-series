from __future__ import annotations

import time

import psycopg2
from pymongo import MongoClient

from benchmark_config import BenchmarkSettings


POSTGRES_DDL_TEMPLATE = """
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS {table_name} (
    sample_id BIGSERIAL NOT NULL,
    device_id BIGINT NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    profile_name TEXT NOT NULL,
    payload_kind TEXT NOT NULL,
    payload_data BYTEA NOT NULL,
    payload_size_bytes INTEGER NOT NULL,
    width INTEGER,
    height INTEGER,
    mime_type TEXT NOT NULL,
    codec TEXT,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (ts, sample_id)
);

SELECT create_hypertable(
    '{table_name}',
    by_range('ts'),
    if_not_exists => TRUE,
    create_default_indexes => FALSE
);

CREATE INDEX IF NOT EXISTS idx_{table_name}_device_ts_desc
ON {table_name} (device_id, ts DESC);
"""


def wait_for_postgres(settings: BenchmarkSettings, timeout_sec: int = 90) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            conn = psycopg2.connect(**settings.postgres_config)
            conn.close()
            return
        except psycopg2.Error:
            time.sleep(1)
    raise TimeoutError("Timed out while waiting for PostgreSQL to accept connections.")


def wait_for_mongodb(settings: BenchmarkSettings, timeout_sec: int = 90) -> None:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=1500)
            client.admin.command({"ping": 1})
            client.close()
            return
        except Exception:
            time.sleep(1)
    raise TimeoutError("Timed out while waiting for MongoDB to accept connections.")


def open_postgres(settings: BenchmarkSettings):
    conn = psycopg2.connect(**settings.postgres_config)
    conn.autocommit = True
    return conn


def open_mongodb(settings: BenchmarkSettings) -> MongoClient:
    return MongoClient(settings.mongo_uri)


def ensure_postgres_schema(settings: BenchmarkSettings) -> None:
    conn = open_postgres(settings)
    try:
        with conn.cursor() as cur:
            cur.execute(
                POSTGRES_DDL_TEMPLATE.format(table_name=settings.postgres_table_name)
            )
    finally:
        conn.close()


def recreate_postgres_table(settings: BenchmarkSettings) -> None:
    conn = open_postgres(settings)
    try:
        with conn.cursor() as cur:
            cur.execute(f"DROP TABLE IF EXISTS {settings.postgres_table_name} CASCADE;")
            cur.execute(
                POSTGRES_DDL_TEMPLATE.format(table_name=settings.postgres_table_name)
            )
    finally:
        conn.close()


def ensure_mongo_collection(settings: BenchmarkSettings) -> None:
    client = open_mongodb(settings)
    try:
        db = client[settings.mongo_db_name]
        existing = db.list_collection_names()
        if settings.mongo_collection_name not in existing:
            db.create_collection(
                settings.mongo_collection_name,
                timeseries={
                    "timeField": "ts",
                    "metaField": "meta",
                    "granularity": "seconds",
                },
            )

        coll = db[settings.mongo_collection_name]
        coll.create_index(
            [("meta.device_id", 1), ("ts", -1)],
            name="idx_device_ts_desc",
        )
    finally:
        client.close()


def recreate_mongo_collection(settings: BenchmarkSettings) -> None:
    client = open_mongodb(settings)
    try:
        db = client[settings.mongo_db_name]
        if settings.mongo_collection_name in db.list_collection_names():
            db.drop_collection(settings.mongo_collection_name)
        db.create_collection(
            settings.mongo_collection_name,
            timeseries={
                "timeField": "ts",
                "metaField": "meta",
                "granularity": "seconds",
            },
        )
        db[settings.mongo_collection_name].create_index(
            [("meta.device_id", 1), ("ts", -1)],
            name="idx_device_ts_desc",
        )
    finally:
        client.close()
