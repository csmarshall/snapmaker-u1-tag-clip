"""Draw an old-time, hand-drafted blueprint of the finger dock (the dock I actually use) into docs/images/blueprint_dock.png. For fun.

Six orthographic views in third-angle layout (front in the middle, top above, bottom below, right to its right, left to its left, back at the far right) plus an
isometric. Each view is a hidden-line projection of the real B-rep from u1_parts.dock_fingers_parts, so the drawing comes from the same model as the prints;
the overall dimensions are measured from each view's projected edges and the notes read their numbers from chip_clip's constants.

The old-time look is all in the drawing: lines get a little hand wobble (matplotlib's sketch filter) and run past their corners like a draftsman's construction
lines, the paper is Prussian blue with grain, blotches, fold creases and a dark edge, and the lettering is Architects Daughter (OFL, vendored in tools/fonts).
The random parts are seeded, so a rebuild draws the same sheet.

Run: uv run python tools/render_blueprint.py
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from build123d import Edge, GeomType, Vector  # noqa: E402
from OCP.BRepLib import BRepLib  # noqa: E402
from OCP.gp import gp_Ax1, gp_Ax2  # noqa: E402
from OCP.HLRAlgo import HLRAlgo_Projector  # noqa: E402
from OCP.HLRBRep import HLRBRep_Algo, HLRBRep_HLRToShape  # noqa: E402
from OCP.TopAbs import TopAbs_ShapeEnum  # noqa: E402
from OCP.TopExp import TopExp_Explorer  # noqa: E402
from OCP.TopoDS import TopoDS  # noqa: E402
from build123d.topology import Shape  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402
from scipy.ndimage import gaussian_filter  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "u1"))
sys.path.insert(0, str(REPO / "chip"))

from chip_clip import DOCK_FRONT_CLEARANCE, DOCK_SIDE_CLEARANCE, FIT_CLEARANCE, STICKER_DIAMETER  # type: ignore[import-not-found]  # noqa: E402
from u1_parts import STICKER_CENTRE_Y, dock_fingers_parts  # type: ignore[import-not-found]  # noqa: E402

log = logging.getLogger("render_blueprint")

OUT_PATH = REPO / "docs" / "images" / "blueprint_dock.png"
HAND_FONT_PATH = REPO / "tools" / "fonts" / "ArchitectsDaughter-Regular.ttf"

DRAWN_BY = "C. MARSHALL"
COMPANY = "SHERMER WORKS LLC"
DRAWING_NUMBER = "STC-001"
TITLE = "U1 TAG CLIP · FINGER DOCK"

PAPER_RGB = np.array([0.10, 0.25, 0.50])  # Prussian blue
INK = "#eef3ff"
FAINT = "#a9c0e4"
SEED = 1932  # fixes the paper texture, so a rebuild draws the same sheet
OUTPUT_WIDTH_PX = 4200
MM_PER_FIGURE_INCH = 9.0  # sheet millimetres per figure inch; text sizes and line widths below are in sheet mm and converted through this
PT_PER_MM = 72.0 / MM_PER_FIGURE_INCH
SMOOTH_ANGLE_DEG = 20.0  # edges where neighbouring faces meet flatter than this are tangent-ish facets (the traced finger outline) and are not drawn
ISO_SCALE = 1.6  # the isometric is drawn enlarged
LINE_MM = {"visible": 0.24, "hidden": 0.12, "thin": 0.08, "border": 0.45}

VIEW_GAP = 30.0  # mm of sheet between neighbouring views
EDGE_SAMPLES = 24  # points per projected curved edge
OVERSHOOT = 1.6  # how far straight lines run past their corners, like construction lines
DIM_OFFSET = 7.5  # how far a dimension line sits outside its view
MARGIN = 14.0  # paper edge to the drawing border
WOBBLE = (0.9, 70.0, 2.0)  # matplotlib path.sketch: (amplitude, wavelength, randomness)

# name: (camera direction from the part, camera up). Coordinates as in u1_parts: X right, Y up, +Z out of the panel toward you.
VIEWS: dict[str, tuple[tuple[float, float, float], tuple[float, float, float]]] = {
    "FRONT": ((0, 0, 1), (0, 1, 0)),
    "BACK": ((0, 0, -1), (0, 1, 0)),
    "TOP": ((0, 1, 0), (0, 0, -1)),
    "BOTTOM": ((0, -1, 0), (0, 0, 1)),
    "RIGHT": ((1, 0, 0), (0, 1, 0)),
    "LEFT": ((-1, 0, 0), (0, 1, 0)),
    "ISOMETRIC": ((1, 1, 1), (0, 1, 0)),
}

Polyline = list[tuple[float, float]]


def _hlr_edges(compound: object) -> list[Edge]:
    """Every edge in an HLR result compound, with 3D curves rebuilt (build123d does the same; without it OCC can segfault)."""
    edges: list[Edge] = []
    if compound is None or compound.IsNull():  # type: ignore[attr-defined]
        return edges
    explorer = TopExp_Explorer(compound, TopAbs_ShapeEnum.TopAbs_EDGE)  # type: ignore[arg-type]
    while explorer.More():
        raw = TopoDS.Edge(explorer.Current())
        BRepLib.BuildCurves3d_s(raw, 1e-5)
        edges.append(Edge(raw))
        explorer.Next()
    return edges


def project(shape: Shape, direction: tuple[float, float, float], up: tuple[float, float, float]) -> tuple[list[Polyline], list[Polyline], list[Polyline]]:
    """Hidden-line projection of `shape` seen from `direction`: (visible polylines, hidden polylines, visible straight segments) in view-plane mm.

    Sharp edges and silhouettes only. Edges between faces that meet within SMOOTH_ANGLE_DEG are marked regular first and left out, so the snap fingers'
    traced outline (many small facets) draws as a clean profile and not as a comb of facet lines.
    """
    BRepLib.EncodeRegularity_s(shape.wrapped, np.radians(SMOOTH_ANGLE_DEG))
    algo = HLRBRep_Algo()
    algo.Add(shape.wrapped)
    axes = gp_Ax2()
    axes.SetAxis(gp_Ax1(Vector(*(500.0 * c for c in direction)).to_pnt(), Vector(*direction).normalized().to_dir()))
    axes.SetYDirection(Vector(*up).normalized().to_dir())
    algo.Projector(HLRAlgo_Projector(axes))
    algo.Update()
    algo.Hide()
    result = HLRBRep_HLRToShape(algo)
    visible = _hlr_edges(result.VCompound()) + _hlr_edges(result.OutLineVCompound())
    hidden = _hlr_edges(result.HCompound()) + _hlr_edges(result.OutLineHCompound())

    def polylines(edges: list[Edge]) -> list[Polyline]:
        lines: list[Polyline] = []
        for edge in edges:
            samples = 1 if edge.geom_type == GeomType.LINE else EDGE_SAMPLES
            points = [edge.position_at(i / samples) for i in range(samples + 1)]
            lines.append([(p.X, p.Y) for p in points])
        return lines

    straight = [line for line, edge in zip(polylines(visible), visible) if edge.geom_type == GeomType.LINE]
    return polylines(visible), polylines(hidden), straight


def bounds(lines: list[Polyline]) -> tuple[float, float, float, float]:
    """(xmin, ymin, xmax, ymax) over every point of `lines`."""
    xs = [x for line in lines for x, _ in line]
    ys = [y for line in lines for _, y in line]
    return min(xs), min(ys), max(xs), max(ys)


def paper(width_px: int, height_px: int) -> np.ndarray:
    """An aged blueprint sheet as an RGB array: grain, soft blotches, two fold creases and a darkened edge."""
    rng = np.random.default_rng(SEED)
    grain = rng.normal(0, 0.035, (height_px, width_px))
    blotches = gaussian_filter(rng.normal(0, 1, (height_px, width_px)), sigma=min(width_px, height_px) / 12)
    blotches *= 0.10 / max(1e-9, float(np.abs(blotches).max()))
    yy, xx = np.mgrid[0:height_px, 0:width_px]
    nx, ny = xx / width_px - 0.5, yy / height_px - 0.5
    vignette = -0.55 * (nx**2 + ny**2) ** 1.4
    creases = 0.05 * np.exp(-(((xx - width_px / 2) / 3.0) ** 2)) + 0.04 * np.exp(-(((yy - height_px / 2) / 3.0) ** 2))
    shade = 1.0 + grain + blotches + vignette + creases
    return np.clip(PAPER_RGB[None, None, :] * shade[:, :, None], 0, 1)


def chalk_line(ax: Axes, xs: list[float], ys: list[float], color: str = INK) -> None:
    """One drafted line: a soft halo under a crisp stroke, both with the hand wobble."""
    ax.plot(xs, ys, color=color, lw=lw("visible") * 2.6, alpha=0.10, solid_capstyle="round")
    ax.plot(xs, ys, color=color, lw=lw("visible"), alpha=0.92, solid_capstyle="round")


def hand_text(ax: Axes, x: float, y: float, text: str, size_mm: float, **kwargs: object) -> None:
    """Lettering in the vendored hand font, `size_mm` tall-ish on the sheet."""
    props = font_manager.FontProperties(fname=str(HAND_FONT_PATH), size=size_mm * PT_PER_MM)
    ax.text(x, y, text, fontproperties=props, color=INK, **kwargs)  # type: ignore[arg-type]


def lw(kind: str) -> float:
    """A line width from LINE_MM, in points."""
    return LINE_MM[kind] * PT_PER_MM


def dimension(ax: Axes, a: tuple[float, float], b: tuple[float, float], rotation: float) -> None:
    """A dimension line from a to b with arrows both ends and its length in mm written across its middle."""
    ax.annotate("", xy=a, xytext=b, arrowprops={"arrowstyle": "<|-|>", "color": INK, "lw": lw("thin"), "shrinkA": 0, "shrinkB": 0, "mutation_scale": 2.2 * PT_PER_MM})
    length = float(np.hypot(a[0] - b[0], a[1] - b[1]))
    hand_text(ax, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, f"{length:.1f}", 2.6, ha="center", va="center", rotation=rotation,
              bbox={"facecolor": tuple(PAPER_RGB), "edgecolor": "none", "pad": 0.8})


def draw_view(ax: Axes, name: str, view: tuple[list[Polyline], list[Polyline], list[Polyline]], at: tuple[float, float], dims: bool) -> None:
    """Draw one view with the lower-left corner of its bounding box at `at`, a caption under it and, if `dims`, overall width and height."""
    visible, hidden, straight = view
    x0, y0, x1, y1 = bounds(visible)
    dx, dy = at[0] - x0, at[1] - y0
    for line in hidden:
        ax.plot([x + dx for x, _ in line], [y + dy for _, y in line], color=FAINT, lw=lw("hidden"), alpha=0.8, ls=(0, (4, 3)))
    for (ax0, ay0), (ax1, ay1) in (seg for seg in straight if len(seg) == 2):
        length = float(np.hypot(ax1 - ax0, ay1 - ay0))
        if length < 2 * OVERSHOOT:
            continue
        ux, uy = (ax1 - ax0) / length, (ay1 - ay0) / length
        ax.plot([ax0 - OVERSHOOT * ux + dx, ax1 + OVERSHOOT * ux + dx], [ay0 - OVERSHOOT * uy + dy, ay1 + OVERSHOOT * uy + dy], color=FAINT, lw=lw("thin"), alpha=0.6)
    for line in visible:
        chalk_line(ax, [x + dx for x, _ in line], [y + dy for _, y in line])
    left, bottom, right, top = at[0], at[1], at[0] + x1 - x0, at[1] + y1 - y0
    hand_text(ax, (left + right) / 2, bottom - (DIM_OFFSET + 6 if dims else 5), f"{name} VIEW" + (" (ENLARGED)" if not dims else ""), 3.4, ha="center", va="top")
    if not dims:
        return
    yd = bottom - DIM_OFFSET
    for x in (left, right):
        ax.plot([x, x], [bottom - 1.2, yd - 1.5], color=FAINT, lw=lw("thin"))
    dimension(ax, (left, yd), (right, yd), 0)
    xd = left - DIM_OFFSET
    for y in (bottom, top):
        ax.plot([left - 1.2, xd - 1.5], [y, y], color=FAINT, lw=lw("thin"))
    dimension(ax, (xd, bottom), (xd, top), 90)


def border(ax: Axes, x0: float, y0: float, x1: float, y1: float) -> None:
    """Double drawing border with zone letters down the sides and numbers along the top and bottom."""
    for inset, width in ((0.0, lw("border")), (2.2, lw("thin"))):
        ax.add_patch(Rectangle((x0 + inset, y0 + inset), x1 - x0 - 2 * inset, y1 - y0 - 2 * inset, fill=False, edgecolor=INK, lw=width, alpha=0.9))
    columns, rows = 8, 4
    for i in range(columns):
        x = x0 + (i + 0.5) * (x1 - x0) / columns
        for y, va in ((y1 + 1.5, "bottom"), (y0 - 1.5, "top")):
            hand_text(ax, x, y, str(i + 1), 3.2, ha="center", va=va)
    for j in range(rows):
        y = y1 - (j + 0.5) * (y1 - y0) / rows
        for x, ha in ((x0 - 1.5, "right"), (x1 + 1.5, "left")):
            hand_text(ax, x, y, "ABCD"[j], 3.2, ha=ha, va="center")


def title_block(ax: Axes, right: float, bottom: float) -> None:
    """The title block in the lower right: company, title, who drew it, date, drawing number, units."""
    w, h = 150.0, 44.0
    x, y = right - w, bottom
    ax.add_patch(Rectangle((x, y), w, h, fill=False, edgecolor=INK, lw=lw("border")))
    for yy in (y + 29, y + 15):
        ax.plot([x, x + w], [yy, yy], color=INK, lw=lw("thin") * 1.5)
    for xx in (x + w / 3, x + 2 * w / 3):
        ax.plot([xx, xx], [y, y + 15], color=INK, lw=lw("thin") * 1.5)
    hand_text(ax, x + w / 2, y + 36.5, COMPANY, 7.0, ha="center", va="center")
    hand_text(ax, x + w / 2, y + 22, TITLE, 4.6, ha="center", va="center")
    today = date.today().strftime("%d %b %Y").upper()
    for i, (label, value) in enumerate((("DRAWN BY", DRAWN_BY), ("DATE", today), ("DWG NO.", DRAWING_NUMBER))):
        cx = x + (i + 0.5) * w / 3
        hand_text(ax, cx, y + 11, label, 2.2, ha="center", va="center", alpha=0.8)
        hand_text(ax, cx, y + 5, value, 3.6, ha="center", va="center")
    hand_text(ax, x + w, y - 3, "UNITS: MM    THIRD-ANGLE PROJECTION    SHEET 1 OF 1", 2.6, ha="right", va="top")


def stamp(ax: Axes, cx: float, cy: float) -> None:
    """A tilted double-ring 'approved' stamp."""
    for r, width in ((19.0, lw("border")), (16.5, lw("thin"))):
        ax.add_patch(Circle((cx, cy), r, fill=False, edgecolor=INK, lw=width, alpha=0.75))
    hand_text(ax, cx - 1.2, cy + 6.5, "SHERMER WORKS", 2.8, ha="center", va="center", rotation=12, alpha=0.8)
    hand_text(ax, cx, cy, "APPROVED", 5.0, ha="center", va="center", rotation=12, alpha=0.85)
    hand_text(ax, cx + 1.2, cy - 6.5, "FOR PRINTING", 2.6, ha="center", va="center", rotation=12, alpha=0.8)


def notes(ax: Axes, x: float, y: float) -> None:
    """General notes, with their numbers read from the model's constants."""
    lines = [
        "NOTES:",
        "1. PRINT STANDING ON BOTTOM STOP. SUPPORTS UNDER SNAP FINGERS ONLY.",
        f"2. SLIDING FITS FROM FIT_CLEARANCE {FIT_CLEARANCE:g}. CHANNEL {DOCK_SIDE_CLEARANCE:g} PER SIDE, {DOCK_FRONT_CLEARANCE:g} FRONT TO BACK.",
        f"3. {STICKER_DIAMETER:g} MM NTAG215 STICKER RIDES IN THE CHIP, CENTRED ON THE SOCKET AXIS.",
        "4. SNAP FINGERS AFTER REMMULEGGUH (PRINTABLES 1625982).",
    ]
    for i, text in enumerate(lines):
        hand_text(ax, x, y - i * 6.5, text, 2.9 if i else 3.6, ha="left", va="top")


def main() -> None:
    """Build the dock, project every view, lay out the sheet and write the PNG."""
    logging.basicConfig(level=os.environ.get("TAG_CLIP_LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    log.info("building the finger dock")
    dock = dock_fingers_parts(None)["dock"]
    views = {name: project(dock, d, u) for name, (d, u) in VIEWS.items()}
    iso_visible, iso_hidden, iso_straight = views["ISOMETRIC"]
    views["ISOMETRIC"] = tuple([[(x * ISO_SCALE, y * ISO_SCALE) for x, y in line] for line in group] for group in (iso_visible, iso_hidden, iso_straight))  # type: ignore[assignment]
    size: dict[str, tuple[float, float]] = {}
    for name, view in views.items():
        bx0, by0, bx1, by1 = bounds(view[0])
        size[name] = (bx1 - bx0, by1 - by0)
    log.info("view sizes %s", {k: (round(w, 2), round(h, 2)) for k, (w, h) in size.items()})

    fw, fh = size["FRONT"]
    front_at = (MARGIN + 18 + size["LEFT"][0] + VIEW_GAP, MARGIN + 28 + size["BOTTOM"][1] + VIEW_GAP)
    places = {
        "FRONT": front_at,
        "TOP": (front_at[0] + (fw - size["TOP"][0]) / 2, front_at[1] + fh + VIEW_GAP),
        "BOTTOM": (front_at[0] + (fw - size["BOTTOM"][0]) / 2, front_at[1] - VIEW_GAP - size["BOTTOM"][1]),
        "LEFT": (front_at[0] - VIEW_GAP - size["LEFT"][0], front_at[1] + (fh - size["LEFT"][1]) / 2),
        "RIGHT": (front_at[0] + fw + VIEW_GAP, front_at[1] + (fh - size["RIGHT"][1]) / 2),
    }
    places["BACK"] = (places["RIGHT"][0] + size["RIGHT"][0] + VIEW_GAP, front_at[1] + (fh - size["BACK"][1]) / 2)
    places["ISOMETRIC"] = (places["BACK"][0] + size["BACK"][0] + VIEW_GAP, places["TOP"][1] + size["TOP"][1] - size["ISOMETRIC"][1])

    sheet_w = places["ISOMETRIC"][0] + size["ISOMETRIC"][0] + VIEW_GAP + MARGIN
    sheet_h = places["TOP"][1] + size["TOP"][1] + VIEW_GAP + MARGIN
    dpi = OUTPUT_WIDTH_PX / (sheet_w / MM_PER_FIGURE_INCH)
    fig = plt.figure(figsize=(sheet_w / MM_PER_FIGURE_INCH, sheet_h / MM_PER_FIGURE_INCH), dpi=dpi)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, sheet_w)
    ax.set_ylim(0, sheet_h)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.imshow(paper(int(sheet_w * 3), int(sheet_h * 3)), extent=(0, sheet_w, 0, sheet_h), origin="lower", interpolation="bilinear", zorder=-10)

    with plt.rc_context({"path.sketch": WOBBLE}):
        border(ax, MARGIN, MARGIN, sheet_w - MARGIN, sheet_h - MARGIN)
        for name, view in views.items():
            draw_view(ax, name, view, places[name], dims=name != "ISOMETRIC")
        for name in ("FRONT", "BACK"):
            vx0, vy0, vx1, _ = bounds(views[name][0])
            cx = places[name][0] + (-vx0 if name == "FRONT" else vx1)
            cy = places[name][1] + STICKER_CENTRE_Y - vy0
            for xs, ys in (([cx - 24, cx + 24], [cy, cy]), ([cx, cx], [cy - 24, cy + 24])):
                ax.plot(xs, ys, color=FAINT, lw=lw("thin"), ls=(0, (9, 2, 1.5, 2)))
        hand_text(ax, places["FRONT"][0] + fw / 2 + 25, places["FRONT"][1] + STICKER_CENTRE_Y - bounds(views["FRONT"][0])[1] + 1.2,
                  "CL SOCKET AXIS", 2.6, ha="left", va="bottom")
        title_block(ax, sheet_w - MARGIN - 6, MARGIN + 10)
        notes(ax, places["RIGHT"][0], places["TOP"][1] + size["TOP"][1])  # the open space between the top view and the isometric
        stamp(ax, places["LEFT"][0] + size["LEFT"][0] / 2, places["BOTTOM"][1] + size["BOTTOM"][1] / 2)  # the open corner left of the bottom view

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=dpi)
    log.info("wrote %s", OUT_PATH)


if __name__ == "__main__":
    main()
