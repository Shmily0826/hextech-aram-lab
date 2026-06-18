"""Compress og-banner.png from 2.2MB to under 300KB."""
from PIL import Image
import os

SRC = "og-banner.png"
orig_size = os.path.getsize(SRC)
img = Image.open(SRC)
print(f"Original: {img.size}, {orig_size:,} bytes ({orig_size/1024:.0f} KB)")

# Resize to 1200x630 (OG recommended size) and save as JPEG
img = img.convert("RGB")
img = img.resize((1200, 630), Image.LANCZOS)
img.save(SRC, "PNG", optimize=True)
new_size = os.path.getsize(SRC)
print(f"Optimized PNG: {new_size:,} bytes ({new_size/1024:.0f} KB)")

# Try JPEG for even smaller size
img.save("og-banner-test.jpg", "JPEG", quality=85, optimize=True)
jpg_size = os.path.getsize("og-banner-test.jpg")
print(f"JPEG q85: {jpg_size:,} bytes ({jpg_size/1024:.0f} KB)")

# Use whichever is smaller, save back as og-banner.png for compatibility
if jpg_size < new_size:
    os.replace("og-banner-test.jpg", SRC)
    final = jpg_size
    print("Using JPEG version (smaller)")
else:
    os.remove("og-banner-test.jpg")
    final = new_size
    print("Keeping PNG version")

reduction = (1 - final / orig_size) * 100
print(f"\nResult: {orig_size/1024:.0f} KB → {final/1024:.0f} KB ({reduction:.1f}% reduction)")
