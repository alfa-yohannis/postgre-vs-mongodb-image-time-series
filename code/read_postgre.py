# read_back_one.py
from io import BytesIO

import psycopg2
from PIL import Image

DB_CONFIG = {
    "dbname": "iot_ts",
    "user": "postgres",
    "password": "1234",  # fill if needed
    "host": "localhost",
    "port": 5432,
}


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, device_id, ts, frame_data, mime_type
        FROM sensor_frames
        ORDER BY ts DESC
        LIMIT 1
        """
    )

    row = cur.fetchone()
    if not row:
        print("No rows in sensor_frames")
        return

    row_id, device_id, ts, frame_bytes, mime_type = row
    print("Read row:", row_id, device_id, ts, mime_type)

    img = Image.open(BytesIO(frame_bytes))
    print("Image size:", img.size)

    out_path = "restored_frame_postgre.jpg"
    img.save(out_path)
    print("Saved to", out_path)

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
