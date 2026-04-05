from database_setup import wait_for_mongodb, wait_for_postgres, load_settings
settings = load_settings()
print("Checking engines...")
# wait_for_mongodb(settings, 10)
# wait_for_postgres(settings, 10)
print("Done")
