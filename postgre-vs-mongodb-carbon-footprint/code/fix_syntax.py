with open("benchmark_config.py", "r") as f:
    text = f.read()
import re
text = re.sub(r'    "360p_sd_image": WorkloadProfile\(\n        name="360p_sd_image",[\s\S]*?video_duration_sec=None,\n    \),\n', "", text)
with open("benchmark_config.py", "w") as f: f.write(text)
