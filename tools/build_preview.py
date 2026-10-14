"""Stage the review page and its meshes in coin/out/preview for publishing as an artifact.

Artifacts do not serve .stl, so each mesh is written as base64 text that the page decodes. Run the build first.
"""
import base64
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "coin" / "out"
STAGE = OUT / "preview"
MATERIALS = ("PLA", "PLAplus", "PETG", "ASA", "ABS", "TPU", "Nylon")
DOCK_PARTS = ("back_plate", "channels", "lower_pocket", "digit")


def main() -> int:
    """Copy the page and encode every chip and dock part it loads; return a shell exit code."""
    mesh_dir = STAGE / "mesh"
    mesh_dir.mkdir(parents=True, exist_ok=True)
    names = [f"chip_{m}" for m in MATERIALS] + [f"chip_{m}_label" for m in MATERIALS]
    names += [f"dock_slot{s}_{p}" for s in (1, 2, 3, 4) for p in DOCK_PARTS]
    missing = [n for n in names if not (OUT / f"{n}.stl").exists()]
    if missing:
        print(f"missing build outputs (run coin/u1_chip_clip.py first): {', '.join(missing)}", file=sys.stderr)
        return 1
    for name in names:
        (mesh_dir / f"{name}.txt").write_text(base64.b64encode((OUT / f"{name}.stl").read_bytes()).decode())
    shutil.copy(ROOT / "tools" / "preview" / "u1-chip-dock-review.html", STAGE / "u1-chip-dock-review.html")
    print(f"staged {len(names)} meshes and the page in {STAGE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
