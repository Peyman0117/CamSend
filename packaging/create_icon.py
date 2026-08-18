"""Create the Windows application icon from the public CamSend logo."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops


def create_icon(source_path: Path, destination_path: Path) -> None:
    source = Image.open(source_path).convert("RGBA")
    rgb = source.convert("RGB")
    difference = ImageChops.difference(rgb, Image.new("RGB", rgb.size, "white")).convert("L")
    bounds = difference.point(lambda value: 255 if value > 14 else 0).getbbox()
    brand = source.crop(bounds) if bounds else source

    icon_width = min(brand.width, int(brand.height * 1.18))
    mark = brand.crop((0, 0, icon_width, brand.height)).convert("RGBA")
    mark_rgb = mark.convert("RGB")
    alpha_source = ImageChops.difference(mark_rgb, Image.new("RGB", mark_rgb.size, "white")).convert("L")
    alpha = alpha_source.point(lambda value: 0 if value <= 8 else min(255, (value - 8) * 8))
    mark.putalpha(alpha)

    size = max(mark.size)
    padding = max(12, size // 12)
    canvas = Image.new("RGBA", (size + padding * 2, size + padding * 2), (0, 0, 0, 0))
    canvas.alpha_composite(mark, ((canvas.width - mark.width) // 2, (canvas.height - mark.height) // 2))
    canvas = canvas.resize((256, 256), Image.Resampling.LANCZOS)

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(
        destination_path,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    create_icon(args.source.resolve(), args.destination.resolve())


if __name__ == "__main__":
    main()
