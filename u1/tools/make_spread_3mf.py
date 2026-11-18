"""Build the finger-spread sweep plate (u1/docs/FINGER_SPREAD.md): six blank covers whose snap fingers are spread 0 to 2.5 mm per side, one Snapmaker Orca 3MF.

Each cover is the blank cover with the spread value engraved as its label (control +0.0 first), turned as printed (flat top on the bed, fingers on slicer supports) and laid out on the 270mm bed.
It is one filament (PETG) and carries no printer, process or filament settings: pick the U1 0.4mm presets after opening. Nothing the other builds write is touched.
Also prints, for each spread, the hooks' half-width against the assumed bore (the bore is 1waynger1's plug width, not measured on the printer).

Run: uv run python u1/tools/make_spread_3mf.py
"""
import math
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]  # the repository root
sys.path.insert(0, str(ROOT / "u1" / "tools"))
sys.path.insert(0, str(ROOT / "u1"))
sys.path.insert(0, str(ROOT / "chip"))
from make_3mf import ORCA_VERSION, mesh_xml  # noqa: E402
from print_orientation import UPSIDE_DOWN  # noqa: E402
from print_plates import BED, GAP  # noqa: E402
from socket_fingers import FINGER_HEIGHT, hook_half_width  # noqa: E402
from u1_parts import SOCKET_BORE_DIAMETER, cover_parts  # noqa: E402
from build123d import export_stl  # noqa: E402

SPREADS = (0.0, 0.5, 1.0, 1.5, 2.0, 2.5)  # mm per side; the control first
COLUMNS = 3  # covers per row on the bed
OUT_3MF = ROOT / "u1" / "out" / "u1_finger_spread.3mf"


def label_for(spread: float) -> str:
    """The text engraved on a cover: the spread with its sign, one decimal (+0.0, +1.5)."""
    return f"{spread:+.1f}"


def hook_extents(spread: float) -> tuple[float, float]:
    """Return (the hooks' half-width, the half-width the bore allows at the fingers' top and bottom edges, +-FINGER_HEIGHT/2), both in mm."""
    bore_radius = SOCKET_BORE_DIAMETER / 2
    return hook_half_width(spread), math.sqrt(bore_radius ** 2 - (FINGER_HEIGHT / 2) ** 2)


def cover_mesh(spread: float) -> trimesh.Trimesh:
    """Return the blank cover for this spread (label engraved, no slot digit) as a mesh, in the model's frame."""
    body = cover_parts(None, spread=spread, label=label_for(spread))["cover"]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cover.stl"
        export_stl(body, str(path))
        return trimesh.load(path, force="mesh")


def lay_out(meshes: list[trimesh.Trimesh]) -> list[trimesh.Trimesh]:
    """Return the meshes turned as printed (flat top on the bed) and placed in a grid, GAP apart, centred on the bed."""
    turned = []
    for m in meshes:
        m = m.copy()
        m.vertices = m.vertices @ UPSIDE_DOWN.T
        turned.append(m)
    cell_x = max(m.extents[0] for m in turned) + GAP
    cell_y = max(m.extents[1] for m in turned) + GAP
    rows = math.ceil(len(turned) / COLUMNS)
    assert COLUMNS * cell_x - GAP < BED and rows * cell_y - GAP < BED, "the sweep does not fit on the bed"
    for i, m in enumerate(turned):
        m.apply_translation(np.array([(i % COLUMNS) * cell_x, (i // COLUMNS) * cell_y, 0.0]) - m.bounds[0])
    lo = np.min([m.bounds[0] for m in turned], axis=0)
    hi = np.max([m.bounds[1] for m in turned], axis=0)
    centre = np.array([BED / 2 - (lo[0] + hi[0]) / 2, BED / 2 - (lo[1] + hi[1]) / 2, 0.0])
    for m in turned:
        m.apply_translation(centre)
    return turned


def write_3mf(path: Path, meshes: list[trimesh.Trimesh], names: list[str]) -> None:
    """Write the placed meshes as a Bambu-format 3MF, one object each, fingers on supports, all on filament 1 of one plate."""
    head = '<?xml version="1.0" encoding="UTF-8"?>\n'
    ns = 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" requiredextensions="p"'
    files: dict[str, str] = {}
    resources, items, settings, instances, rels = [], [], [], [], []
    for i, (mesh, name) in enumerate(zip(meshes, names)):
        object_id, sub_id = 2 * i + 1, 2 * i + 2
        model_path = f"/3D/Objects/object_{object_id}.model"
        centre = mesh.bounds.mean(axis=0) * [1, 1, 0]
        local = mesh.copy()
        local.apply_translation(-centre)  # the object's origin sits at its footprint centre; the build item places it
        files[model_path.lstrip("/")] = f'{head}<model unit="millimeter" {ns}><resources>{mesh_xml(sub_id, local)}</resources><build/></model>'
        rels.append(f'<Relationship Target="{model_path}" Id="rel-{object_id}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
        resources.append(f'<object id="{object_id}" type="model"><components><component p:path="{model_path}" objectid="{sub_id}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/></components></object>')
        items.append(f'<item objectid="{object_id}" transform="1 0 0 0 1 0 0 0 1 {centre[0]:.5f} {centre[1]:.5f} 0" printable="1"/>')
        part = (
            f'<part id="{sub_id}" subtype="normal_part"><metadata key="name" value={quoteattr(name)}/>'
            '<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/><metadata key="extruder" value="1"/></part>'
        )
        support = '<metadata key="enable_support" value="1"/><metadata key="support_on_build_plate_only" value="1"/>'
        settings.append(f'<object id="{object_id}"><metadata key="name" value={quoteattr(name)}/><metadata key="extruder" value="1"/>{support}{part}</object>')
        instances.append(f'<model_instance><metadata key="object_id" value="{object_id}"/><metadata key="instance_id" value="0"/></model_instance>')
    plate = f'<plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value="Finger spread sweep (PETG)"/><metadata key="locked" value="false"/>{"".join(instances)}</plate>'
    files.update({
        "[Content_Types].xml": f'{head}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="png" ContentType="image/png"/><Default Extension="gcode" ContentType="text/x.gcode"/></Types>',
        "_rels/.rels": f'{head}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
        "3D/_rels/3dmodel.model.rels": f'{head}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{"".join(rels)}</Relationships>',
        "3D/3dmodel.model": f'{head}<model unit="millimeter" xml:lang="en-US" {ns}><metadata name="Application">BambuStudio-{ORCA_VERSION}</metadata><metadata name="BambuStudio:3mfVersion">1</metadata><metadata name="Title">U1 finger spread sweep</metadata><resources>{"".join(resources)}</resources><build>{"".join(items)}</build></model>',
        "Metadata/model_settings.config": f'{head}<config>{"".join(settings)}{plate}</config>',
    })
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in files.items():
            z.writestr(name, text)


def main() -> int:
    """Build the six covers, write the 3MF, print the hook-against-bore table; return a shell exit code."""
    bore_radius = SOCKET_BORE_DIAMETER / 2
    print(f"bore radius {bore_radius:.2f} mm (assumed, not measured); chord at the fingers' +-{FINGER_HEIGHT / 2:g} mm edges {hook_extents(0)[1]:.2f} mm")
    print("spread  hook half-width  minus bore radius  minus chord at the finger edges")
    for spread in SPREADS:
        half, chord = hook_extents(spread)
        print(f"{spread:+.1f}     {half:6.3f}           {half - bore_radius:+6.2f}             {half - chord:+6.2f}")
    placed = lay_out([cover_mesh(s) for s in SPREADS])
    OUT_3MF.parent.mkdir(exist_ok=True)
    write_3mf(OUT_3MF, placed, [f"Cover, spread {label_for(s)}" for s in SPREADS])
    print(f"wrote {OUT_3MF}: {len(placed)} covers, spreads {', '.join(label_for(s) for s in SPREADS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
