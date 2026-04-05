from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image
from pymongo import MongoClient

from benchmark_config import load_settings
from database_setup import open_minio


def suffix_for_mime(mime_type: str) -> str:
    return {"image/jpeg": ".jpg", "video/mp4": ".mp4"}.get(mime_type, ".bin")


def main() -> None:
    settings = load_settings()
    minio_client = open_minio(settings)

    client = MongoClient(settings.mongo_uri)
    try:
        coll = client[settings.mongo_db_name][settings.mongo_collection_name]
        doc = coll.find_one(
            {"meta.device_id": settings.device_id},
            sort=[("ts", -1)],
        )
    finally:
        client.close()

    if not doc:
        print("No documents found in MongoDB benchmark collection.")
        return

    payload_size_bytes = doc["payload_size_bytes"]
    mime_type = doc["mime_type"]
    ts = doc["ts"]
    object_key = doc["minio_object_key"]

    resp = minio_client.get_object(settings.minio_bucket, object_key)
    payload_data = resp.read()
    resp.close()
    resp.release_conn()

    output_path = Path(f"restored_payload_mongo{suffix_for_mime(mime_type)}")
    output_path.write_bytes(payload_data)

    print(f"Retrieved sample from {ts} ({payload_size_bytes} bytes, {mime_type})")
    print(f"MinIO object key: {object_key}")
    print(f"Saved payload to {output_path}")

    if mime_type.startswith("image/"):
        img = Image.open(BytesIO(payload_data))
        print(f"Decoded image size: {img.size}")


if __name__ == "__main__":
    main()
