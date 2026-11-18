"""Write one chip as a single Snapmaker Orca / Bambu-format 3MF: one object with two parts, the body on filament 1 and the name inlay on filament 2.

The file structure is the one u1/tools/make_3mf.py writes for its plates (which imports mesh_xml and ORCA_VERSION from here). There are no printer, process or filament settings in it:
pick the printer's presets in the slicer after opening. Needs trimesh and numpy, so chip_clip.py imports this only when it writes a 3MF.
"""
import tempfile
import zipfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

import numpy as np
import trimesh
from build123d import export_stl
from licence_notice import model_metadata_xml

ORCA_VERSION = "01.10.01.50"  # claimed in the file; Orca refuses a 3MF from a newer version than itself
BED = 270.0  # Snapmaker U1 bed, mm square; the chip is centred on it
ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)  # the earliest date a zip can hold; every 3MF entry carries it so rebuilds are byte-identical
INLAY_EXTRUDER = 2  # the name inlay prints in the second filament; everything else in the first


def write_3mf_zip(path: Path, files: dict[str, str]) -> None:
    """Write the entries to `path` in insertion order with a fixed timestamp and deflate, so the same content always gives the same bytes."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for entry, text in files.items():
            info = zipfile.ZipInfo(entry, date_time=ZIP_DATE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16  # fixed permissions, whatever the host's umask
            z.writestr(info, text)


VERTEX_DECIMALS = 5  # vertex coordinates are written to this many decimals, and rounded to them before sorting so the order cannot depend on float noise


def canonical_triangles(mesh) -> tuple[np.ndarray, np.ndarray]:
    """Return (vertices, faces) of the mesh in an order that depends only on its triangles: OCC's parallel meshing yields the same triangles in a different order from run to run, which would make the file differ.

    Vertices are rounded, each triangle starts at its smallest vertex (winding kept), triangles are sorted, and the vertices are numbered in sorted order.
    """
    tris = np.round(np.asarray(mesh.triangles, dtype=float), VERTEX_DECIMALS) + 0.0  # + 0.0 turns -0.0 into 0.0
    for i, t in enumerate(tris):
        first = min(range(3), key=lambda k: tuple(t[k]))
        tris[i] = np.roll(t, -first, axis=0)
    order = np.lexsort(tris.reshape(-1, 9).T[::-1])
    verts, inverse = np.unique(tris[order].reshape(-1, 3), axis=0, return_inverse=True)
    return verts, inverse.reshape(-1, 3)


def mesh_xml(object_id: int, mesh) -> str:
    """Return one 3MF <object> holding the mesh, with vertices and triangles in canonical order."""
    verts_arr, faces_arr = canonical_triangles(mesh)
    verts = "".join(f'<vertex x="{x:.{VERTEX_DECIMALS}f}" y="{y:.{VERTEX_DECIMALS}f}" z="{z:.{VERTEX_DECIMALS}f}"/>' for x, y, z in verts_arr)
    tris = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in faces_arr)
    return f'<object id="{object_id}" type="model"><mesh><vertices>{verts}</vertices><triangles>{tris}</triangles></mesh></object>'


def _load(shape) -> trimesh.Trimesh:
    """The shape as a mesh, meshed by the same STL export the chip's .stl file uses."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "part.stl"
        export_stl(shape, str(path))
        return trimesh.load(path, force="mesh")


def write_chip_3mf(path: Path, stem: str, name: str, body, inlay) -> None:
    """Write `path`: one object named `name`, with the part `stem` (body, filament 1) and the part `stem`_label (inlay, filament 2), lying back face down and centred on the bed."""
    body_mesh, inlay_mesh = _load(body), _load(inlay)
    centre = np.array(body_mesh.bounds).mean(axis=0) * [1, 1, 0]
    drop = body_mesh.bounds[0][2]  # back face on the bed
    head = '<?xml version="1.0" encoding="UTF-8"?>\n'
    ns = 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" requiredextensions="p"'
    object_id, sub_ids = 1, (2, 3)
    model_path = f"/3D/Objects/object_{object_id}.model"
    sub_objects, components, parts_cfg = [], [], []
    for sub_id, part_name, mesh, extruder in zip(sub_ids, (stem, f"{stem}_label"), (body_mesh, inlay_mesh), (1, INLAY_EXTRUDER)):
        local = mesh.copy()
        local.apply_translation(-centre - [0, 0, drop])  # the object's origin sits at the body's footprint centre; the build item places it
        sub_objects.append(mesh_xml(sub_id, local))
        components.append(f'<component p:path="{model_path}" objectid="{sub_id}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>')
        parts_cfg.append(
            f'<part id="{sub_id}" subtype="normal_part"><metadata key="name" value={quoteattr(part_name)}/>'
            f'<metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/><metadata key="extruder" value="{extruder}"/></part>'
        )
    files = {
        model_path.lstrip("/"): f"{head}<model unit=\"millimeter\" {ns}><resources>{''.join(sub_objects)}</resources><build/></model>",
        "[Content_Types].xml": f'{head}<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/><Default Extension="png" ContentType="image/png"/><Default Extension="gcode" ContentType="text/x.gcode"/></Types>',
        "_rels/.rels": f'{head}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
        "3D/_rels/3dmodel.model.rels": f'{head}<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="{model_path}" Id="rel-{object_id}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>',
        "3D/3dmodel.model": (
            f'{head}<model unit="millimeter" xml:lang="en-US" {ns}><metadata name="Application">BambuStudio-{ORCA_VERSION}</metadata><metadata name="BambuStudio:3mfVersion">1</metadata>'
            f'{model_metadata_xml(stem)}<resources><object id="{object_id}" type="model"><components>{"".join(components)}</components></object></resources>'
            f'<build><item objectid="{object_id}" transform="1 0 0 0 1 0 0 0 1 {BED / 2:.5f} {BED / 2:.5f} 0" printable="1"/></build></model>'
        ),
        "Metadata/model_settings.config": (
            f'{head}<config><object id="{object_id}"><metadata key="name" value={quoteattr(name)}/><metadata key="extruder" value="1"/>{"".join(parts_cfg)}</object>'
            f'<plate><metadata key="plater_id" value="1"/><metadata key="plater_name" value={quoteattr(name)}/><metadata key="locked" value="false"/>'
            f'<model_instance><metadata key="object_id" value="{object_id}"/><metadata key="instance_id" value="0"/></model_instance></plate></config>'
        ),
    }
    write_3mf_zip(path, files)
