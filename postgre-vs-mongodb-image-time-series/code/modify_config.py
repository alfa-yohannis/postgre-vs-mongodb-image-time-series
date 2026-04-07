import os
from pathlib import Path

file_path = Path("/home/alfa/projects/image-based-time-series-data/postgre-vs-mongodb-image-time-series/code/benchmark_config.py")
content = file_path.read_text()

lines = content.split('\n')

for i in range(len(lines)):
    if 'warmup_rows=' in lines[i]:
        lines[i] = '        warmup_rows=100,'
    elif 'total_rows=' in lines[i] and 'total_rows: int' not in lines[i] and '_env_int' not in lines[i] and 'rows/run=' not in lines[i]:
        lines[i] = '        total_rows=1000,'
    elif 'batch_size=' in lines[i] and 'batch_size: int' not in lines[i] and 'batch=' not in lines[i]:
        lines[i] = '        batch_size=1,'

file_path.write_text('\n'.join(lines))
