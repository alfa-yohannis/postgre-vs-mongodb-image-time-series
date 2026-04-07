from pymongo import MongoClient
import os
from bson import BSON

print("Testing BSON encoding...")
raw_bytes = os.urandom(7500000)
doc = {"data": raw_bytes}
bson_data = BSON.encode(doc)
print(f"Python byte length: {len(raw_bytes)}")
print(f"BSON binary length: {len(bson_data)}")

client = MongoClient("mongodb://mongo:mongo@127.0.0.1:57017/?authSource=admin")
db = client["iot_ts"]
coll = db["debug_coll"]
coll.drop()
coll.insert_one(doc)
print("Insertion of 7.5MB doc successful.")

batch = [doc, doc]
try:
    coll.insert_many(batch, ordered=False)
    print("Insertion of 2x 7.5MB docs successful via insert_many.")
except Exception as e:
    print(f"Failed with insert_many 2 docs: {e}")
