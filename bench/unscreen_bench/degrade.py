"""Make the 1080p-degraded variant: the meeting-window capture as a viewer receives it.

Meeting apps send screen shares at reduced resolution with lossy compression. We render at
1920x1080 inside a meeting window, downscale to 1280x720 and re-encode as JPEG at a seeded
quality between 50 and 70."""

import json
import random
from pathlib import Path

from PIL import Image

FRAMES = Path(__file__).resolve().parents[1] / "fixtures" / "frames"


def degrade(src: Path, dst: Path, seed: int) -> int:
    quality = random.Random(seed).randint(50, 70)  # noqa: S311
    with Image.open(src) as img:
        small = img.convert("RGB").resize((1280, 720), Image.Resampling.BILINEAR)
        small.save(dst, format="JPEG", quality=quality, subsampling=2)
    return quality


def main() -> None:
    manifest = json.loads((FRAMES / "manifest.json").read_text())
    added = []
    for item in manifest:
        if item["variant"] != "meet1080p":
            continue
        fid = item["id"].replace("meet1080p", "1080p-degraded")
        q = degrade(FRAMES / f"{item['id']}.png", FRAMES / f"{fid}.jpg", item["seed"])
        truth = FRAMES / f"{item['id']}.truth.json"
        (FRAMES / f"{fid}.truth.json").write_text(truth.read_text())
        added.append({**item, "id": fid, "variant": "1080p-degraded", "width": 1280, "height": 720, "jpeg_quality": q})
    manifest = [m for m in manifest if m["variant"] != "1080p-degraded"] + added
    (FRAMES / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"degraded {len(added)} frames")


if __name__ == "__main__":
    main()
