"""Stage the review page and its meshes in coin/out/preview for publishing as an artifact.

Artifacts do not serve .stl, so each mesh is written as base64 text that the page decodes. Run the build first.
"""
import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "coin" / "out"
STAGE = OUT / "preview"
DOCK_PARTS = ("back_plate", "channels", "lower_pocket", "accent")


def main() -> int:
    """Copy the page and encode every chip and dock part it loads; return a shell exit code."""
    mesh_dir = STAGE / "mesh"
    mesh_dir.mkdir(parents=True, exist_ok=True)
    # Every chip the build made, found by its label file, so this never needs its own copy of the filament list.
    stems = sorted(p.name[len("chip_"):-len("_label.stl")] for p in OUT.glob("chip_*_label.stl"))
    if not stems:
        print("no chips in coin/out: run coin/u1_chip_clip.py first", file=sys.stderr)
        return 1
    names = [f"chip_{m}" for m in stems] + [f"chip_{m}_label" for m in stems]
    names += [f"dock_slot{s}_{p}" for s in (1, 2, 3, 4) for p in DOCK_PARTS]
    names += ["dock_mount", "socket_adapter", "hub_adapter_standin"] + [f"cover_slot{s}{p}" for s in (1, 2, 3, 4) for p in ("", "_accent")]
    missing = [n for n in names if not (OUT / f"{n}.stl").exists()]
    if missing:
        print(f"missing build outputs (run coin/u1_chip_clip.py first): {', '.join(missing)}", file=sys.stderr)
        return 1
    # Meshes from parts that no longer exist would otherwise linger and be published with the page.
    for stale in mesh_dir.glob("*.txt"):
        if stale.stem not in names:
            stale.unlink()
    for name in names:
        (mesh_dir / f"{name}.txt").write_text(base64.b64encode((OUT / f"{name}.stl").read_bytes()).decode())
    (mesh_dir / "manifest.json").write_text(json.dumps({"chips": stems}))
    orientation = STAGE / "print_orientation.png"
    subprocess.run([sys.executable, str(ROOT / "tools" / "print_orientation.py"), str(orientation)], check=True)
    shutil.copy(ROOT / "tools" / "preview" / "u1-chip-dock-review.html", STAGE / "u1-chip-dock-review.html")
    print(f"staged {len(names)} meshes and the page in {STAGE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
