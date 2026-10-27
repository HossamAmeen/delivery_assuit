"""Generate PLACEHOLDER PWA icons (no brand assets exist yet). Run: python3 scripts/generate_icons.py"""

from pathlib import Path

from PIL import Image, ImageDraw

BG = (11, 95, 255)
FG = (255, 255, 255)
OUT = Path(__file__).resolve().parent.parent / "public" / "icons"


def draw(size, safe):
    """Square icon; `safe` is the fraction of the canvas the mark may use."""
    img = Image.new("RGB", (size, size), BG)
    d = ImageDraw.Draw(img)
    box = size * safe
    left = (size - box) / 2
    # A simple parcel: rounded square with a cross band.
    d.rounded_rectangle([left, left, left + box, left + box], radius=box * 0.12, outline=FG, width=max(2, int(size * 0.04)))
    band = box * 0.16
    mid = size / 2
    d.rectangle([mid - band / 2, left, mid + band / 2, left + box], fill=FG)
    d.rectangle([left, mid - band / 2, left + box, mid + band / 2], fill=FG)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    draw(192, 0.7).save(OUT / "icon-192.png")
    draw(512, 0.7).save(OUT / "icon-512.png")
    draw(512, 0.5).save(OUT / "icon-maskable-512.png")  # inside the 80% maskable safe zone
    draw(180, 0.7).save(OUT / "apple-touch-icon.png")


if __name__ == "__main__":
    main()
