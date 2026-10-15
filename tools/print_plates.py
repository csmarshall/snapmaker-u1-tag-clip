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
from u1_chip_clip import POCKET_DEPTH, POCKET_DIAMETER  # noqa: E402

OUT = ROOT / "coin" / "out"
FIXTURES = ROOT / "fixtures"
STAGE = OUT / "test_print"
BED = 270.0  # Snapmaker U1 bed, mm square
GAP = 12.0  # between parts on the plate
BED_CONTACT = 0.15  # faces below this height rest on the bed, so they never need support
POCKET_RADIUS = POCKET_DIAMETER / 2 + 0.01  # the chip's sticker recess, plus mesh tolerance

FLAT = np.eye(3)
ON_BOTTOM_STOP = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)  # dock: its flat end (low y) on the bed

# (plate, name, how it prints, rotation, [(file, colour role)]); the first file is the body, the rest are inlays in the same frame.
PARTS = (
    (1, "Dock, slot 1", "Standing on its bottom stop.", ON_BOTTOM_STOP, [(OUT / "dock_slot1.stl", "dock"), (OUT / "dock_slot1_accent.stl", "label")]),
    (1, "Dock mount", "Upside down on its arm ends. The crossbar bridges about 39mm.", UPSIDE_DOWN, [(OUT / "dock_mount.stl", "mount")]),
    (1, "Socket adapter", "Standing on its flat top.", UPSIDE_DOWN, [(OUT / "socket_adapter.stl", "adapter")]),
    (1, "Blank cover, slot 2", "Standing on its flat top, with slicer supports under the fingers.", UPSIDE_DOWN, [(OUT / "cover_slot2.stl", "mount"), (OUT / "cover_slot2_accent.stl", "label")]),
    (1, "Chip, PETG label", "Back face down, no pause. The recess ceiling bridges about 26mm. Press the sticker into the recess afterwards.", FLAT, [(OUT / "chip_PETG.stl", "chip"), (OUT / "chip_PETG_label.stl", "label")]),
)
# Plate number -> (title, filament).
PLATES = {1: ("Fit set", "PLA")}

# The integrated dock (docs/INTEGRATED_DOCK.md) is its own one-plate project, so the test print above stays as it was.
# Chip X to printer -Z (its +X side face on the bed), chip Y along the bed, chip Z to printer X: a proper rotation (determinant +1). The tongue then lies flat along the bed.
ON_SIDE = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float)
INTEGRATED_PARTS = (
    (1, "Integrated dock, slot 1", "Lying on its side face; the dovetail's section stands upright.", ON_SIDE, [(OUT / "dock_integrated_slot1.stl", "dock"), (OUT / "dock_integrated_slot1_accent.stl", "label")]),
)
INTEGRATED_PLATES = {1: ("Integrated dock", "PETG")}


def split_overhang(mesh: trimesh.Trimesh, sealed_pocket_centre: np.ndarray | None = None) -> tuple[trimesh.Trimesh, trimesh.Trimesh | None]:
    """Return (faces that print unsupported, faces facing down more steeply than 45 degrees above the bed).

    A chip's recess ceiling is not counted: it is a straight bridge across the recess, which prints without support.
    """
    centres = mesh.triangles_center
    over = (mesh.face_normals[:, 2] < -OVERHANG_LIMIT) & (centres[:, 2] > BED_CONTACT)
    if sealed_pocket_centre is not None:
        ceiling = np.isclose(centres[:, 2], POCKET_DEPTH, atol=0.01) & (np.linalg.norm(centres[:, :2] - sealed_pocket_centre[:2], axis=1) <= POCKET_RADIUS)
        over &= ~ceiling
    if not over.any():
        return mesh, None
    return mesh.submesh([np.flatnonzero(~over)], append=True), mesh.submesh([np.flatnonzero(over)], append=True)


def write(mesh_dir: Path, stem: str, mesh: trimesh.Trimesh, role: str) -> dict:
    """Write the mesh as base64 STL text; return its layout entry."""
    name = f"{stem}.txt"
    (mesh_dir / name).write_text(base64.b64encode(mesh.export(file_type="stl")).decode())
    return {"file": name, "role": role}


def lay_out(parts_table: tuple = PARTS) -> dict[int, list[dict]]:
    """Return each round's parts placed on the bed as printed: name, note, size, and [(source file, colour role, placed mesh)]."""
    missing = [str(f) for *_, files in parts_table for f, _ in files if not f.exists()]
    if missing:
        raise FileNotFoundError(f"missing build outputs (run the builds first): {', '.join(missing)}")
    plates: dict[int, list[dict]] = {}
    for rnd in sorted({p[0] for p in parts_table}):
        x = y = row_depth = 0.0
        items = []
        for _, name, note, rotation, files in (p for p in parts_table if p[0] == rnd):
            assert np.isclose(np.linalg.det(rotation), 1.0)
            meshes = [trimesh.load(f, force="mesh") for f, _ in files]
            for m in meshes:
                m.vertices = m.vertices @ rotation.T
            body = meshes[0]
            size = body.extents
            if x > 0 and x + size[0] > BED:
                x, y, row_depth = 0.0, y + row_depth + GAP, 0.0
            shift = np.array([x, y, 0.0]) - body.bounds[0]  # body on the bed at the cursor; inlays move with it
            for m in meshes:
                m.apply_translation(shift)
            x, row_depth = x + size[0] + GAP, max(row_depth, size[1])
            items.append({"name": name, "note": note, "size": size, "shift": shift, "files": [(f, role, m) for (f, role), m in zip(files, meshes)]})
        plates[rnd] = items
    return plates


def main() -> int:
    """Stage the page, meshes and layout; return a shell exit code."""
    try:
        placed = lay_out()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1
    mesh_dir = STAGE / "mesh"
    shutil.rmtree(mesh_dir, ignore_errors=True)
    mesh_dir.mkdir(parents=True)
    plates = {}
    for rnd, parts in placed.items():
        items = []
        for part in parts:
            entry = {"name": part["name"], "note": part["note"], "size": [round(float(v), 1) for v in part["size"]], "meshes": []}
            for f, role, m in part["files"]:
                # An inlay's underside rests on its own body's engraving floor, so only bodies can need support.
                good, over = (m, None) if role == "label" else split_overhang(m, part["shift"] if role == "chip" else None)
                entry["meshes"].append(write(mesh_dir, f.stem, good, role))
                if over is not None:
                    entry["meshes"].append(write(mesh_dir, f.stem + "_overhang", over, "overhang"))
                    entry["overhang_mm2"] = entry.get("overhang_mm2", 0) + round(float(over.area))
            items.append(entry)
        plates[str(rnd)] = {"title": PLATES[rnd][0], "filament": PLATES[rnd][1], "parts": items}
    layout = {"bed": BED, "plates": plates}
    (STAGE / "layout.json").write_text(json.dumps(layout, indent=1))
    shutil.copy(ROOT / "tools" / "preview" / "u1-test-print.html", STAGE / "u1-test-print.html")
    print(f"staged {len(list(mesh_dir.glob('*.txt')))} meshes and the page in {STAGE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
