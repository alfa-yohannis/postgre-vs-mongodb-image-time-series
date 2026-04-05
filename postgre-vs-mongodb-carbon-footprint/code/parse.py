import glob
import csv

def extract(pattern, key):
    results = {}
    for f in sorted(glob.glob(pattern)):
        try:
            profile = f.split("_summary_")[1].replace(".csv", "")
            with open(f) as csvf:
                reader = csv.DictReader(csvf)
                rows = list(reader)
                if rows:
                    if key in rows[0]:
                        results[profile] = float(rows[0][key])
                    else:
                        print(f"Key {key} not found in {f}")
        except Exception as e:
            print(f"Error reading {f}: {e}")
    return results

pg_ins = extract("results_postgres_insert_summary_*.csv", "mean_rows_per_sec")
mg_ins = extract("results_mongo_insert_summary_*.csv", "mean_rows_per_sec")
pg_ret = extract("results_postgres_retrieve_summary_*.csv", "mean_latency_ms")
mg_ret = extract("results_mongo_retrieve_summary_*.csv", "mean_latency_ms")

pg_disk = extract("results_postgres_insert_summary_*.csv", "mean_table_total_after_mb")
mg_disk = extract("results_mongo_insert_summary_*.csv", "mean_table_total_after_mb")

profiles = ["1080p_fhd_image", "1440p_qhd_image", "4k_uhd_image", "5k_image", "6k_image"]

print("Res | PG Ins | MG Ins | PG Ret | MG Ret | PG_Disk | MG_Disk")
for p in profiles:
    print(f"{p} | {pg_ins.get(p, 0):.2f} | {mg_ins.get(p, 0):.2f} | {pg_ret.get(p, 0):.2f} | {mg_ret.get(p, 0):.2f} | {pg_disk.get(p, 0):.2f} | {mg_disk.get(p, 0):.2f}")

