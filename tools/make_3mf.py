"""Build the test-print project (docs/TEST_PRINT.md) as one Snapmaker Orca 3MF: plate 1 is round 1, plate 2 round 2.

Uses the layout from print_plates.py. Bodies print with filament 1 and inlays (labels, digits, hint) with filament 2. The blank cover gets supports on the plate,
and the chip's sticker pause is set at PAUSE_HEIGHT. There are no printer, process or filament settings in it: pick the U1 0.4mm presets in Snapmaker Orca
after opening. (Snapmaker Orca 1.10.1's CLI segfaults on loading any process preset, so it cannot fill them in or slice-check the file.)

Run after the builds: uv run --with build123d --with trimesh --with numpy --with matplotlib python tools/make_3mf.py
"""
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from print_plates import BED, PLATES, lay_out  # noqa: E402
from u1_chip_clip import PAUSE_HEIGHT  # noqa: E402  (print_plates puts coin/ on the path)

LAYER_HEIGHT = 0.2  # set it as the first layer height too, so a layer starts exactly at PAUSE_HEIGHT (0.6 back skin + 0.6 pocket = six layers)
INLAY_ROLES = {"label"}
SUPPORTED = {"Blank cover, slot 2"}  # parts whose fingers need slicer support (see README, Printing)
ORCA_VERSION = "01.10.01.50"  # claimed in the file; Orca refuses a 3MF from a newer version than itself
PLATE_GAP = 0.2  # Orca's LOGICAL_PART_PLATE_GAP: plates sit one bed width plus this fraction apart
OUT_3MF = ROOT / "coin" / "out" / "u1_test_print.3mf"

assert abs(PAUSE_HEIGHT / LAYER_HEIGHT - round(PAUSE_HEIGHT / LAYER_HEIGHT)) < 1e-6, "PAUSE_HEIGHT must fall on a layer boundary"


def mesh_xml(object_id: int, mesh) -> str:
    """Return one 3MF <object> holding the mesh."""
    verts = "".join(f'<vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in mesh.vertices)
    tris = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh.faces)
    return f'<object id="{object_id}" type="model"><mesh><vertices>{verts}</vertices><triangles>{tris}</triangles></mesh></object>'


def write_skeleton(path: Path) -> list[str]:
    """Write the geometry, parts, plates and the pause as a Bambu-format 3MF; return the part names in object order."""
    placed = lay_out()
    head = '<?xml version="1.0" encoding="UTF-8"?>\n'
    ns = 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" requiredextensions="p"'
    files: dict[str, str] = {}
    resources, items, settings_objects, plates_xml, rels, names = [], [], [], [], [], []
    next_id = 1
    for plate_no, parts in placed.items():
        # Centre the round on its bed; Orca lays plates out in a row, each a bed width plus a gap from the last.
        lo = np.min([m.bounds[0] for p in parts for _, _, m in p["files"]], axis=0)
        hi = np.max([m.bounds[1] for p in parts for _, _, m in p["files"]], axis=0)
        bed_centre = np.array([BED / 2 + (plate_no - 1) * BED * (1 + PLATE_GAP), BED / 2, 0.0])
        offset = bed_centre - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, 0.0])
        instances = []
        for part in parts:
            object_id = next_id
            sub_ids = list(range(object_id + 1, object_id + 1 + len(part["files"])))
            next_id = sub_ids[-1] + 1
            model_path = f"/3D/Objects/object_{object_id}.model"
            centre = np.array(part["files"][0][2].bounds).mean(axis=0) * [1, 1, 0]
            sub_objects, components, parts_cfg = [], [], []
            for sub_id, (src, role, mesh) in zip(sub_ids, part["files"]):
                local = mesh.copy()
                local.apply_translation(-centre)  # the object's origin sits at its body's footprint centre; the build item places it
                sub_objects.append(mesh_xml(sub_id, local))
                components.append(f'<component p:path="{model_path}" objectid="{sub_id}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>')
                extruder = 2 if role in INLAY_ROLES else 1
                parts_cfg.append(
                    f'<part id="{sub_id}" subtype="normal_part"><metadata key="name" value={quoteattr(src.stem)}/>'
                    f'<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/><metadata key="extruder" value="{extruder}"/></part>'
                )
            files[model_path.lstrip("/")] = f"{head}<model unit=\"millimeter\" {ns}><resources>{''.join(sub_objects)}</resources><build/></model>"
            rels.append(f'<Relationship Target="{model_path}" Id="rel-{object_id}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
            resources.append(f'<object id="{object_id}" type="model"><components>{"".join(components)}</components></object>')
            tx, ty, _ = centre + offset
            items.append(f'<item objectid="{object_id}" transform="1 0 0 0 1 0 0 0 1 {tx:.5f} {ty:.5f} 0" printable="1"/>')
            support = '<metadata key="enable_support" value="1"/><metadata key="support_on_build_plate_only" value="1"/>' if part["name"] in SUPPORTED else ""
            settings_objects.append(f'<object id="{object_id}"><metadata key="name" value={quoteattr(part["name"])}/><metadata key="extruder" value="1"/>{support}{"".join(parts_cfg)}</object>')
            instances.append(f'<model_instance><metadata key="object_id" value="{object_id}"/><metadata key="instance_id" value="0"/></model_instance>')
            names.append(part["name"])
        plates_xml.append(f'<plate><metadata key="plater_id" value="{plate_no}"/><metadata key="plater_name" value={quoteattr(PLATES[plate_no][0])}/><metadata key="locked" value="false"/>{"".join(instances)}</plate>')
    pause_plates = [n for n, parts in placed.items() if any(role == "chip" for p in parts for _, role, _ in p["files"])]
    # The pause runs before the layer that starts at PAUSE_HEIGHT, i.e. the layer whose top is one layer higher.
    pause_z = PAUSE_HEIGHT + LAYER_HEIGHT
    gcodes = "".join(
        f'<plate><plate_info id="{n}"/><layer top_z="{pause_z:.2f}" type="1" extruder="1" color="" extra="" gcode="M601"/><mode value="MultiAsSingle"/></plate>' for n in pause_plates
    )
    files.update({
        "[Content_Types].xml": f'{head}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="png" ContentType="image/png"/><Default Extension="gcode" ContentType="text/x.gcode"/></Types>',
        "_rels/.rels": f'{head}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
        "3D/_rels/3dmodel.model.rels": f'{head}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{"".join(rels)}</Relationships>',
        "3D/3dmodel.model": f'{head}<model unit="millimeter" xml:lang="en-US" {ns}><metadata name="Application">BambuStudio-{ORCA_VERSION}</metadata><metadata name="BambuStudio:3mfVersion">1</metadata><metadata name="Title">U1 chip clip test print</metadata><resources>{"".join(resources)}</resources><build>{"".join(items)}</build></model>',
        "Metadata/model_settings.config": f'{head}<config>{"".join(settings_objects)}{"".join(plates_xml)}</config>',
        "Metadata/custom_gcode_per_layer.xml": f"{head}<custom_gcodes_per_layer>{gcodes}</custom_gcodes_per_layer>",
    })
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in files.items():
            z.writestr(name, text)
    return names



def main() -> int:
    """Write the project 3MF (geometry, parts, plates, filament per part, cover supports, sticker pause); return a shell exit code."""
    names = write_skeleton(OUT_3MF)
    print(f"wrote {OUT_3MF}: {len(names)} objects: {', '.join(names)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
