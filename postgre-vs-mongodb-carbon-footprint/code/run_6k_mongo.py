import os
import sys

# Force the 6K image profile
os.environ["MEDIA_PROFILE"] = "6k_image"
# We can also explicitly force some config if desired, e.g. reducing run loops for a quick test
# os.environ["BENCHMARK_INSERT_RUNS"] = "1"
# os.environ["BENCHMARK_TOTAL_ROWS"] = "10"

print("=" * 60)
print("Starting 6K MongoDB Test (Insert & Retrieve)")
print("=" * 60)

print("\n>>> Phase 1: Inserting 6K Images into MongoDB...")
try:
    import insert_mongodb
    insert_mongodb.main()
    print(">>> Phase 1 Complete!\n")
except Exception as e:
    print(f"\n[ERROR] Insertion failed: {e}")
    sys.exit(1)

print(">>> Phase 2: Retrieving 6K Images from MongoDB...")
try:
    import retrieve_mongodb
    retrieve_mongodb.main()
    print(">>> Phase 2 Complete!\n")
except Exception as e:
    print(f"\n[ERROR] Retrieval failed: {e}")
    sys.exit(1)

print("=" * 60)
print("6K MongoDB Test Completed Successfully!")
print("=" * 60)
