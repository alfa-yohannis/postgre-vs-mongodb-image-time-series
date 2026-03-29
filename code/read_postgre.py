from __future__ import annotations

from pathlib import Path

import psycopg2
from PIL import Image
from io import BytesIO

from benchmark_config import load_settings


def suffix_for_mime(mime_type: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "video/mp4": ".mp4",
    }.get(mime_type, ".bin")


def main() -> None:
    settings = load_settings()

    conn = psycopg2.connect(**settings.postgres_config)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT ts, payload_data, payload_size_bytes, mime_type
                FROM {settings.postgres_table_name}
                WHERE device_id = %s
                ORDER BY ts DESC
                LIMIT 1
                """,
                (settings.device_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        print("No rows found in PostgreSQL benchmark table.")
        return

    ts, payload_data, payload_size_bytes, mime_type = row
    output_path = Path(f"restored_payload_postgre{suffix_for_mime(mime_type)}")
    output_path.write_bytes(payload_data)

    print(f"Retrieved sample from {ts} ({payload_size_bytes} bytes, {mime_type})")
    print(f"Saved payload to {output_path}")

    if mime_type.startswith("image/"):
        img = Image.open(BytesIO(payload_data))
        print(f"Decoded image size: {img.size}")


if __name__ == "__main__":
    main()
