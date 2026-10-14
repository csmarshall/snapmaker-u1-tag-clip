"""Draw the hanger on a print bed in each candidate orientation and mark the faces that would need support (facing down more steeply than 45 degrees, not on the bed).

Writes a PNG for the review page. Run after the build: uv run --with trimesh --with numpy --with matplotlib --with scipy --with networkx python tools/print_orientation.py <out.png>
"""
import sys
from pathlib import Path

import matplotlib
import numpy as np
import trimesh

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "coin" / "out"
OVERHANG_LIMIT = np.cos(np.radians(45))  # a face needs support when it faces down more steeply than this
LIGHT = np.array([-0.3, 0.6, 0.75]) / np.linalg.norm([-0.3, 0.6, 0.75])


# Chip frame (X width, Y up the dock, Z out from the panel) to printer frame (Z up from the bed), as proper rotations (rows are the printer axes).
UPRIGHT = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)  # arms' ends on the bed
UPSIDE_DOWN = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)  # the plate's flat top and the fingers' top face on the bed


def orient(mesh: trimesh.Trimesh, rotation: np.ndarray) -> trimesh.Trimesh:
    """The mesh turned into the printer frame and sitting on the bed."""
    assert np.isclose(np.linalg.det(rotation), 1.0)
    m = mesh.copy()
    m.vertices = m.vertices @ rotation.T
    m.apply_translation([0, 0, -m.bounds[0][2]])
    return m


def draw(ax, mesh: trimesh.Trimesh, view: np.ndarray, title: str) -> float:
    """Draw with painter's algorithm from `view` (3x3 rows: screen x, screen y, toward viewer); overhang faces red, bed contact blue. Returns overhang area."""
    sub = mesh.subdivide_to_size(0.8)
    n = sub.face_normals
    centre_z = sub.triangles_center[:, 2]
    overhang = (n[:, 2] < -OVERHANG_LIMIT) & (centre_z > 0.15)
    on_bed = (n[:, 2] < -0.99) & (centre_z <= 0.15)
    t = sub.triangles @ view.T
    nv = n @ view.T
    keep = nv[:, 2] > 0
    shade = 0.4 + 0.6 * np.clip(nv @ LIGHT, 0, 1)
    colour = np.tile([0.47, 0.53, 0.6], (len(t), 1)) * shade[:, None]
    colour[overhang] = np.array([0.85, 0.2, 0.2]) * (0.6 + 0.4 * shade[overhang, None])
    colour[on_bed] = [0.25, 0.45, 0.85]
    order = np.argsort(t[keep][:, :, 2].mean(1))
    ax.add_collection(PolyCollection(t[keep][order][:, :, :2], facecolors=colour[keep][order], edgecolors=colour[keep][order], linewidths=0.2))
    p = t[:, :, :2].reshape(-1, 2)
    ax.axhline(0, color="k", lw=2)  # the bed
    ax.set_xlim(p[:, 0].min() - 5, p[:, 0].max() + 5)
    ax.set_ylim(-3, p[:, 1].max() + 5)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=11)
    ax.set_xticks([]); ax.set_yticks([])
    return float(sub.area_faces[overhang].sum())


def main() -> int:
    """Render both orientations side by side to the path given on the command line."""
    dock = trimesh.load(OUT / "hanger.stl")
    az, el = np.radians(40), np.radians(-25)  # from the front-right and a little below, so downward-facing faces show
    cam = np.array([np.cos(el) * np.sin(az), -np.cos(el) * np.cos(az), np.sin(el)])  # unit vector toward the viewer
    right = np.cross([0, 0, 1], cam); right /= np.linalg.norm(right)
    upv = np.cross(cam, right)
    below = np.array([right, upv, cam])
    fig, axs = plt.subplots(2, 2, figsize=(14, 12))
    for col, (rotation, name) in enumerate(((UPRIGHT, "Upright: arms' ends on the bed"), (UPSIDE_DOWN, "Upside down: plate's flat top and fingers on the bed (use this)"))):
        m = orient(dock, rotation)
        out_of_panel = rotation @ [0, 0, 1]  # the chip's front direction in the printer frame, drawn to the right
        side = np.array([out_of_panel, [0, 0, 1], np.cross(out_of_panel, [0, 0, 1])], float)
        area = draw(axs[0, col], m, side, f"{name}\nside profile: the panel is on the left, the fingers poke left into it")
        draw(axs[1, col], m, below, f"seen from below; needs support: about {area:.0f} mm\u00b2")
    fig.suptitle("Hanger on the print bed. Red: faces overhanging more than 45\u00b0 (need support). Blue: on the bed. Black line: the bed.", fontsize=12)
    fig.tight_layout()
    fig.savefig(sys.argv[1], dpi=80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
