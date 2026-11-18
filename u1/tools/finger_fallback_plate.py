"""The fallback test plate (u1/docs/FINGER_FALLBACK.md): the harness plate and the separate snap-finger piece, each turned to the face-down orientation with the least overhang, on one PETG plate.

For each piece every face-down orientation (one per face of its bounding box) is scored with the same overhang rule as u1/tools/print_plates.py (faces turned down more steeply
than 45 degrees and not on the bed), and the least is picked; the table is printed. Only these six are tried, not tilted ones.
Writes u1/out/u1_finger_fallback.3mf (no printer, process or filament settings: pick the U1 0.4mm and PETG presets in Snapmaker Orca after opening, as for u1_test_print.3mf).

Run after the builds: uv run python u1/tools/finger_fallback_plate.py
"""
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]  # the repository root
sys.path.insert(0, str(ROOT / "u1" / "tools"))
sys.path.insert(0, str(ROOT / "u1"))
sys.path.insert(0, str(ROOT / "chip"))
from make_3mf import ORCA_VERSION, mesh_xml, model_metadata_xml  # noqa: E402
from print_orientation import orient  # noqa: E402
from print_plates import BED, GAP, split_overhang  # noqa: E402

OUT = ROOT / "u1" / "out"
OUT_3MF = OUT / "u1_finger_fallback.3mf"
PIECES = (("Harness plate", OUT / "u1_finger_fallback_plate.stl"), ("Finger piece", OUT / "u1_finger_fallback_fingers.stl"))
# Which face of the piece is on the bed -> the direction (chip frame: X width, Y up the dock, Z out from the panel) that must point down.
FACES = {"top edge (+Y)": (0, 1, 0), "bottom edge (-Y)": (0, -1, 0), "back face (-Z, on the panel)": (0, 0, -1), "front (+Z)": (0, 0, 1), "side (+X)": (1, 0, 0), "side (-X)": (-1, 0, 0)}


def candidates(mesh: trimesh.Trimesh) -> list[dict]:
    """Score each face-down orientation: its rotation, height on the bed and the face area (mm2) that would need support."""
    rows = []
    for label, down in FACES.items():
        rotation = trimesh.geometry.align_vectors(np.array(down, float), [0, 0, -1])[:3, :3]
        placed = orient(mesh, rotation)
        _, over = split_overhang(placed)
        rows.append({"face": label, "rotation": rotation, "height": float(placed.extents[2]), "overhang_mm2": 0.0 if over is None else float(over.area)})
    return rows


def best(rows: list[dict]) -> dict:
    """The orientation with the least overhang; ties (within 0.01 mm2) go to the lowest print."""
    return min(rows, key=lambda r: (round(r["overhang_mm2"], 2), r["height"]))


def lay_out() -> list[dict]:
    """Return both pieces turned as printed and placed side by side on one bed: name, chosen orientation, all candidates, placed mesh."""
    placed, x = [], 0.0
    for name, path in PIECES:
        mesh = trimesh.load(path, force="mesh")
        rows = candidates(mesh)
        choice = best(rows)
        m = orient(mesh, choice["rotation"])
        m.apply_translation([x - m.bounds[0][0], -m.bounds[0][1], 0.0])
        x += m.extents[0] + GAP
        placed.append({"name": name, "choice": choice, "rows": rows, "mesh": m})
    return placed


def write_3mf(path: Path, placed: list[dict]) -> None:
    """Write one plate holding both pieces, filament 1, centred on the bed (the same file structure as u1/tools/make_3mf.py)."""
    head = '<?xml version="1.0" encoding="UTF-8"?>\n'
    ns = 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" requiredextensions="p"'
    lo = np.min([p["mesh"].bounds[0] for p in placed], axis=0)
    hi = np.max([p["mesh"].bounds[1] for p in placed], axis=0)
    offset = np.array([BED / 2 - (lo[0] + hi[0]) / 2, BED / 2 - (lo[1] + hi[1]) / 2, 0.0])
    files: dict[str, str] = {}
    resources, items, settings, instances, rels = [], [], [], [], []
    for object_id, piece in enumerate(placed, start=1):
        sub_id = 100 + object_id
        model_path = f"/3D/Objects/object_{object_id}.model"
        centre = piece["mesh"].bounds.mean(axis=0) * [1, 1, 0]
        local = piece["mesh"].copy()
        local.apply_translation(-centre)
        files[model_path.lstrip("/")] = f'{head}<model unit="millimeter" {ns}><resources>{mesh_xml(sub_id, local)}</resources><build/></model>'
        rels.append(f'<Relationship Target="{model_path}" Id="rel-{object_id}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
        resources.append(f'<object id="{object_id}" type="model"><components><component p:path="{model_path}" objectid="{sub_id}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/></components></object>')
        tx, ty, _ = centre + offset
        items.append(f'<item objectid="{object_id}" transform="1 0 0 0 1 0 0 0 1 {tx:.5f} {ty:.5f} 0" printable="1"/>')
        part = (f'<part id="{sub_id}" subtype="normal_part"><metadata key="name" value={quoteattr(piece["name"])}/>'
                f'<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/><metadata key="extruder" value="1"/></part>')
        settings.append(f'<object id="{object_id}"><metadata key="name" value={quoteattr(piece["name"])}/><metadata key="extruder" value="1"/>{part}</object>')
        instances.append(f'<model_instance><metadata key="object_id" value="{object_id}"/><metadata key="instance_id" value="0"/></model_instance>')
    plate = f'<plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value="Finger fallback, PETG"/><metadata key="locked" value="false"/>{"".join(instances)}</plate>'
    files.update({
        "[Content_Types].xml": f'{head}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="png" ContentType="image/png"/><Default Extension="gcode" ContentType="text/x.gcode"/></Types>',
        "_rels/.rels": f'{head}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
        "3D/_rels/3dmodel.model.rels": f'{head}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{"".join(rels)}</Relationships>',
        "3D/3dmodel.model": f'{head}<model unit="millimeter" xml:lang="en-US" {ns}><metadata name="Application">BambuStudio-{ORCA_VERSION}</metadata><metadata name="BambuStudio:3mfVersion">1</metadata>{model_metadata_xml("U1 chip clip finger fallback")}<resources>{"".join(resources)}</resources><build>{"".join(items)}</build></model>',
        "Metadata/model_settings.config": f'{head}<config>{"".join(settings)}{plate}</config>',
    })
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in files.items():
            z.writestr(name, text)


def main() -> int:
    """Print the orientation table, write the 3MF; return a shell exit code."""
    missing = [str(p) for _, p in PIECES if not p.exists()]
    if missing:
        print(f"missing build outputs (run python u1/finger_fallback.py first): {', '.join(missing)}", file=sys.stderr)
        return 1
    placed = lay_out()
    for piece in placed:
        print(f"{piece['name']}: overhang area by face down (mm2 over the 45 degree limit)")
        for r in piece["rows"]:
            print(f"  {r['face']:<32} {r['overhang_mm2']:8.1f}   height {r['height']:5.1f}{'   <- chosen' if r is piece['choice'] else ''}")
    write_3mf(OUT_3MF, placed)
    print(f"wrote {OUT_3MF}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
