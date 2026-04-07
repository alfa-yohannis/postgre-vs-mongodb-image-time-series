import os
import pandas as pd
from pathlib import Path

results_dir = Path("./results")

def get_disk(db_name):
    print(f"\n--- {db_name.upper()} DISK ---")
    pattern = f"results_{db_name}_insert_runs_*.csv"
    dfs = []
    for fpath in results_dir.glob(pattern):
        profile = fpath.stem.replace(f"results_{db_name}_insert_runs_", "")
        df = pd.read_csv(fpath)
        if 'table_total_after_mb' in df.columns:
            print(f"{profile}: {df['table_total_after_mb'].mean():.2f} MB")
        elif 'db_size_after_mb' in df.columns:
            print(f"{profile}: {df['db_size_after_mb'].mean():.2f} MB")

get_disk('postgres')
get_disk('mongo')
