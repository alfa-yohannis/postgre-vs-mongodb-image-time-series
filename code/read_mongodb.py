# read_back_one_mongo.py
from io import BytesIO

from pymongo import MongoClient
from PIL import Image


# =========================
# CONFIGURATION
# =========================

MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "iot_ts"
COLL_NAME = "sensor_frames"


# =========================
# MAIN
# =========================

def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    coll = db[COLL_NAME]

    # Find the latest document by timestamp
    doc = coll.find_one(sort=[("ts", -1)])

    if not doc:
        print("No documents in sensor_frames")
        return

    doc_id = doc.get("_id")
    device_id = doc.get("device_id")
    ts = doc.get("ts")
    frame_bytes = doc.get("frame_data")
    mime_type = doc.get("mime_type")

    print("Read document:", doc_id, device_id, ts, mime_type)

    # frame_bytes is already bytes when using pymongo
    img = Image.open(BytesIO(frame_bytes))
    print("Image size:", img.size)

    out_path = "restored_frame_mongo.jpg"
    img.save(out_path)
    print("Saved to", out_path)

    client.close()


if __name__ == "__main__":
    main()
