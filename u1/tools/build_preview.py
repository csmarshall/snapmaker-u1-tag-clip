"""Stage the review page and its meshes in u1/out/preview for publishing as an artifact.

Artifacts do not serve .stl, so each mesh is written as base64 text that the page decodes. Run the build first.
"""
import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # the repository root
OUT = ROOT / "u1" / "out"
CHIP_OUT = ROOT / "chip" / "out"  # the chips and generic docks
STAGE = OUT / "preview"
DOCK_PARTS = ("back_plate", "channels", "lower_pocket", "accent")


def source(name: str) -> Path:
    """The built STL for a mesh name: chips and the generic docks come from chip/out, everything else from u1/out."""
    return (CHIP_OUT if name.startswith(("chip_", "dock_slot")) else OUT) / f"{name}.stl"


def main() -> int:
    """Copy the page and encode every chip and dock part it loads; return a shell exit code."""
    mesh_dir = STAGE / "mesh"
    mesh_dir.mkdir(parents=True, exist_ok=True)
    # Every chip the build made, found by its label file, so this never needs its own copy of the filament list.
    stems = sorted(p.name[len("chip_"):-len("_label.stl")] for p in CHIP_OUT.glob("chip_*_label.stl"))
    if not stems:
        print("no chips in chip/out: run chip/chip_clip.py first", file=sys.stderr)
        return 1
    names = [f"chip_{m}" for m in stems] + [f"chip_{m}_label" for m in stems]
    names += [f"dock_slot{s}_{p}" for s in (1, 2, 3, 4) for p in DOCK_PARTS]
    names += ["dock_mount", "socket_adapter", "hub_adapter_standin"] + [f"cover_slot{s}{p}" for s in (1, 2, 3, 4) for p in ("", "_accent")]
    missing = [n for n in names if not source(n).exists()]
    if missing:
        print(f"missing build outputs (run chip/chip_clip.py and u1/u1_build.py first): {', '.join(missing)}", file=sys.stderr)
        return 1
    # Meshes from parts that no longer exist would otherwise linger and be published with the page.
    for stale in mesh_dir.glob("*.txt"):
        if stale.stem not in names:
            stale.unlink()
    for name in names:
        (mesh_dir / f"{name}.txt").write_text(base64.b64encode(source(name).read_bytes()).decode())
    (mesh_dir / "manifest.json").write_text(json.dumps({"chips": stems}))
    orientation = STAGE / "print_orientation.png"
    subprocess.run([sys.executable, str(ROOT / "u1" / "tools" / "print_orientation.py"), str(orientation)], check=True)
    shutil.copy(ROOT / "u1" / "tools" / "preview" / "u1-chip-dock-review.html", STAGE / "u1-chip-dock-review.html")
    print(f"staged {len(names)} meshes and the page in {STAGE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
