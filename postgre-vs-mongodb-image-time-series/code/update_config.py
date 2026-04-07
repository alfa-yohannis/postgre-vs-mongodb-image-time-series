import re
from pathlib import Path

file_path = Path("/home/alfa/projects/image-based-time-series-data/postgre-vs-mongodb-image-time-series/code/benchmark_config.py")
content = file_path.read_text()

# Replace total_rows=\d+, with total_rows=2000,
# Only inside the WorkloadProfile definitions (indented by 8 spaces to avoid hitting variables)
content = re.sub(r'( {8})total_rows=\d+,', r'\1total_rows=2000,', content)

# Replace batch_size=\d+, with batch_size=50,
content = re.sub(r'( {8})batch_size=\d+,', r'\1batch_size=50,', content)

file_path.write_text(content)
print("Updated all profiles to total_rows=2000 and batch_size=50")
