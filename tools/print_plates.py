"""Lay out the test-print set (docs/TEST_PRINT.md) on U1 build plates, each part turned as printed, and stage it for the test-print page.

Each part is written as base64 STL text (artifacts do not serve .stl), split into the faces that need support and the rest, plus a layout.json the page reads.
Run after the builds: uv run --with build123d --with trimesh --with numpy --with matplotlib python tools/print_plates.py
"""
import base64
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "coin"))
from print_orientation import OVERHANG_LIMIT, UPSIDE_DOWN  # noqa: E402
from u1_chip_clip import BACK_SKIN, PAUSE_HEIGHT, POCKET_DEPTH, POCKET_DIAMETER, STICKER_DIAMETER  # noqa: E402

OUT = ROOT / "coin" / "out"
FIXTURES = ROOT / "fixtures"
STAGE = OUT / "test_print"
BED = 270.0  # Snapmaker U1 bed, mm square
GAP = 12.0  # between parts on the plate
BED_CONTACT = 0.15  # faces below this height rest on the bed, so they never need support
POCKET_RADIUS = POCKET_DIAMETER / 2 + 0.01  # the chip's sealed sticker pocket, plus mesh tolerance
STICKER_THICKNESS = 0.4  # assumed, not yet measured (see README)

FLAT = np.eye(3)
ON_BOTTOM_STOP = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)  # dock: its flat end (low y) on the bed

# (round, name, how it prints, rotation, [(file, colour role)]); the first file is the body, the rest are inlays in the same frame.
PARTS = (
    (1, "Standoff strip", "Flat. The sticker goes into each pocket after printing; no pause.", FLAT, [(FIXTURES / "u1_standoff_strip.stl", "fixture")]),
    (1, "Coin-finder puck", "Flat. The sticker goes into the pocket after printing; no pause.", FLAT, [(FIXTURES / "u1_coil_finder_puck.stl", "fixture")]),
    (2, "Chip (PLA)", f"Back face down. Pause at the layer starting at {PAUSE_HEIGHT:.2f}mm, drop the sticker in, resume.", FLAT, [(OUT / "chip_PLA.stl", "chip"), (OUT / "chip_PLA_label.stl", "label")]),
    (2, "Dock, slot 1", "Standing on its bottom stop.", ON_BOTTOM_STOP, [(OUT / "dock_slot1.stl", "dock"), (OUT / "dock_slot1_accent.stl", "label")]),
    (2, "Dock mount", "Upside down on its arm ends. The crossbar bridges about 39mm.", UPSIDE_DOWN, [(OUT / "dock_mount.stl", "mount")]),
    (2, "Socket adapter", "Standing on its flat top.", UPSIDE_DOWN, [(OUT / "socket_adapter.stl", "adapter")]),
    (2, "Blank cover, slot 2", "Standing on its flat top, with slicer supports under the fingers.", UPSIDE_DOWN, [(OUT / "cover_slot2.stl", "mount"), (OUT / "cover_slot2_accent.stl", "label")]),
)


def split_overhang(mesh: trimesh.Trimesh, sealed_pocket_centre: np.ndarray | None = None) -> tuple[trimesh.Trimesh, trimesh.Trimesh | None]:
    """Return (faces that print unsupported, faces facing down more steeply than 45 degrees above the bed).

    A chip's pocket ceiling is not counted: it is laid over the sticker after the pause, so the sticker carries it.
    """
    centres = mesh.triangles_center
    over = (mesh.face_normals[:, 2] < -OVERHANG_LIMIT) & (centres[:, 2] > BED_CONTACT)
    if sealed_pocket_centre is not None:
        ceiling = np.isclose(centres[:, 2], PAUSE_HEIGHT, atol=0.01) & (np.linalg.norm(centres[:, :2] - sealed_pocket_centre[:2], axis=1) <= POCKET_RADIUS)
        over &= ~ceiling
    if not over.any():
        return mesh, None
    return mesh.submesh([np.flatnonzero(~over)], append=True), mesh.submesh([np.flatnonzero(over)], append=True)


def write(mesh_dir: Path, stem: str, mesh: trimesh.Trimesh, role: str) -> dict:
    """Write the mesh as base64 STL text; return its layout entry."""
    name = f"{stem}.txt"
    (mesh_dir / name).write_text(base64.b64encode(mesh.export(file_type="stl")).decode())
    return {"file": name, "role": role}


def main() -> int:
    """Stage the page, meshes and layout; return a shell exit code."""
    missing = [str(f) for *_, files in PARTS for f, _ in files if not f.exists()]
    if missing:
        print(f"missing build outputs (run the builds first): {', '.join(missing)}", file=sys.stderr)
        return 1
    mesh_dir = STAGE / "mesh"
    shutil.rmtree(mesh_dir, ignore_errors=True)
    mesh_dir.mkdir(parents=True)
    plates = {}
    for rnd in sorted({p[0] for p in PARTS}):
        x = y = row_depth = 0.0
        lo, hi = np.full(2, np.inf), np.full(2, -np.inf)
        items = []
        for _, name, note, rotation, files in (p for p in PARTS if p[0] == rnd):
            meshes = [trimesh.load(f, force="mesh") for f, _ in files]
            for m in meshes:
                assert np.isclose(np.linalg.det(rotation), 1.0)
                m.vertices = m.vertices @ rotation.T
            body = meshes[0]
            size = body.extents
            if x > 0 and x + size[0] > BED:
                x, y, row_depth = 0.0, y + row_depth + GAP, 0.0
            shift = np.array([x, y, 0.0]) - body.bounds[0]  # body on the bed at the cursor; inlays move with it
            for m in meshes:
                m.apply_translation(shift)
            lo, hi = np.minimum(lo, body.bounds[0][:2]), np.maximum(hi, body.bounds[1][:2])
            x, row_depth = x + size[0] + GAP, max(row_depth, size[1])
            entry = {"name": name, "note": note, "size": [round(float(v), 1) for v in size], "meshes": []}
            for (f, role), m in zip(files, meshes):
                good, over = split_overhang(m, shift if role == "chip" else None)
                entry["meshes"].append(write(mesh_dir, f.stem, good, role))
                if over is not None:
                    entry["meshes"].append(write(mesh_dir, f.stem + "_overhang", over, "overhang"))
                    entry["overhang_mm2"] = entry.get("overhang_mm2", 0) + round(float(over.area))
            if files[0][1] == "chip":
                # The sticker where it lies when the print resumes: on the back skin, centred on the chip (its frame origin).
                disc = trimesh.creation.cylinder(radius=STICKER_DIAMETER / 2, height=STICKER_THICKNESS, sections=96)
                disc.apply_translation(np.array([0, 0, BACK_SKIN + STICKER_THICKNESS / 2]) + shift)
                entry["meshes"].append(write(mesh_dir, "sticker", disc, "sticker"))
                entry["pause"] = PAUSE_HEIGHT
            items.append(entry)
        plates[str(rnd)] = {"parts": items, "centre": ((lo + hi) / 2).round(1).tolist()}
    layout = {"bed": BED, "pause": PAUSE_HEIGHT, "pocket": [BACK_SKIN, BACK_SKIN + POCKET_DEPTH], "sticker": [STICKER_DIAMETER, STICKER_THICKNESS], "plates": plates}
    (STAGE / "layout.json").write_text(json.dumps(layout, indent=1))
    shutil.copy(ROOT / "tools" / "preview" / "u1-test-print.html", STAGE / "u1-test-print.html")
    print(f"staged {len(list(mesh_dir.glob('*.txt')))} meshes and the page in {STAGE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
