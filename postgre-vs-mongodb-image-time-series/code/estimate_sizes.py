import sys
sys.path.append('.')
from pathlib import Path
from benchmark_config import WORKLOAD_PROFILES
from media_payloads import _build_image_payload, _build_video_payload, MediaPayload

from PIL import Image

# Create dummy image
canvas = Image.new("RGB", (1920, 1080), color="blue")
canvas.save("dummy.jpg", "JPEG")
dummy_path = Path("dummy.jpg")

for p in WORKLOAD_PROFILES:
    if p.payload_kind == 'image':
        payload = _build_image_payload(dummy_path, p)
        print(f"Profile: {p.name}, size: {payload.payload_size_mb:.2f} MB")

