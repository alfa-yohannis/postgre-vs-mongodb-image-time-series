import os
from PIL import Image

output_dir = "assets"
os.makedirs(output_dir, exist_ok=True)
path = os.path.join(output_dir, "Schwarzsee.jpg")

width, height = 1920, 1080
# Generate random bytes for RGB (3 bytes per pixel)
random_data = os.urandom(width * height * 3)

img = Image.frombytes('RGB', (width, height), random_data)
img.save(path)
print(f"Random noise image generated at {path}")
