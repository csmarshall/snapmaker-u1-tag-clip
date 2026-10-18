"""Fallback socket adapter in two printed pieces: a harness plate and a separate snap-finger piece that slides into it on a dovetail.

Use it if the integral socket adapter's fingers (u1_parts.socket_adapter_parts) prove too stiff, too weak or print badly in PETG. It is an independent set of
parts: nothing in chip/chip_clip.py or u1/u1_parts.py changes, and the integral adapter, dock mount, cover and chip are built exactly as before.

Frame: the chip frame of chip/chip_clip.py (X width, Y up, Z out from the panel; the plate's back face on the panel at z_back, the fingers going to -Z through the socket).

Finger piece: remmulegguh's traced fingers (the very same _socket_fingers call as the integral adapter, so FINGER_OUTLINE and FINGER_HEIGHT are used unchanged, including
the thin tab that the outline starts behind the panel face) plus two dovetail tongues that stand out of the tab's front face into the plate, each with a detent ridge.
Harness plate: the integral adapter's plate (its outer envelope, dock-mount slot and corners untouched) with a shallow rebate for the tab and two matching dovetail grooves
cut into its back face. The grooves open at the plate's top edge, so the finger piece slides down from above until its bottom face meets the grooves' stop; its top face then sits
flush with the plate's top edge, as in the integral adapter, and each ridge drops into a dimple in its groove's floor to hold it there.

Printing: both pieces print standing on the plate's top edge, as the integral adapter does (u1/tools/finger_fallback_plate.py checks every face-down orientation and reports the
overhang area); the dovetails run along Y, so they are straight vertical extrusions in that orientation.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "chip"))  # the generic chip and dock live beside this folder
from build123d import Plane, Polygon, extrude  # noqa: E402
from chip_clip import ARM_WALL_THICKNESS, FIT_CLEARANCE, _box, _ccw  # noqa: E402
from socket_fingers import FINGER_HEIGHT, FINGER_OUTLINE  # noqa: E402
from u1_parts import (  # noqa: E402
    ADAPTER_SLOT_PROFILE,
    ADAPTER_THICKNESS,
    ADAPTER_WIDTH,
    _adapter_frame,
    _adapter_plate,
    _socket_fingers,
)

# ---- joint -----------------------------------------------------------------------------------
TAB_THICKNESS = -min(depth for depth, _ in FINGER_OUTLINE)  # how far the traced outline reaches behind the panel face: it sits inside the plate, so the plate needs a rebate for it
DOVETAIL_DEPTH = ARM_WALL_THICKNESS  # how far a tongue reaches into the plate beyond the tab: as thick as the walls elsewhere on the model, so it prints as solid perimeters
DOVETAIL_FLANK_RUN = DOVETAIL_DEPTH  # sideways run of each flank over the tongue's depth, so 45 degrees. Not derivable: any lean locks the piece against pulling out; 45 degrees is a common dovetail that does not wedge in a sliding fit
DETENT_INTERFERENCE = FIT_CLEARANCE / 2  # how far a ridge presses into its groove floor while sliding. Not derivable: it is a stiffness guess for PETG, to be tuned from the first print
DETENT_HEIGHT = FIT_CLEARANCE + DETENT_INTERFERENCE  # ridge height above the tongue's front face: across the clearance, plus the interference
DETENT_HALF_LENGTH = ARM_WALL_THICKNESS  # the ridge's half length along Y. Not derivable: a ramp gentle enough to push over; its steepest slope, DETENT_HEIGHT * pi / 2 / this, stays under 45 degrees
BOOLEAN_OVERLAP = 0.1  # how far a joined solid is sunk into its neighbour so the union has no coincident faces. Not derivable: it only has to exceed the kernel's tolerance, and it adds no volume outside the part


def _slot_edge_distance(x: float, z: float) -> float:
    """Distance in the X-Z section from (x, z above the back face) to the mount slot's side wall (right-hand half; the slot is symmetric)."""
    edge = [(w, ADAPTER_THICKNESS - depth) for w, depth in ADAPTER_SLOT_PROFILE]
    best = math.inf
    for (x0, z0), (x1, z1) in zip(edge, edge[1:]):
        dx, dz = x1 - x0, z1 - z0
        t = max(0.0, min(1.0, ((x - x0) * dx + (z - z0) * dz) / (dx * dx + dz * dz)))
        best = min(best, math.hypot(x - (x0 + t * dx), z - (z0 + t * dz)))
    return best


def joint_geometry() -> dict[str, float]:
    """The joint's dimensions, all derived: Z positions above the back face, and X edges of the right-hand tongue and groove (the left-hand ones mirror them).

    The grooves must keep ARM_WALL_THICKNESS of plate between themselves and the dock mount's slot, and the same from the plate's side edge, so the groove's inner and outer
    corners at its floor are found from those walls. The tongue is the groove less FIT_CLEARANCE on every face; a flank leaning at slope k moves sideways by clearance times sqrt(1 + k^2).
    """
    c = FIT_CLEARANCE
    z_tab = TAB_THICKNESS  # the tab's front face, where the tongues' necks start
    z_head = z_tab + DOVETAIL_DEPTH  # the tongues' front face
    z_floor = z_head + c  # the grooves' floor
    groove_out = ADAPTER_WIDTH / 2 - ARM_WALL_THICKNESS
    lo, hi = 0.0, groove_out  # the inner corner: the smallest x whose floor corner keeps the wall from the slot
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if _slot_edge_distance(mid, z_floor) < ARM_WALL_THICKNESS else (lo, mid)
    slope = DOVETAIL_FLANK_RUN / DOVETAIL_DEPTH
    return {"z_tab": z_tab, "z_head": z_head, "z_floor": z_floor, "groove_in": hi, "groove_out": groove_out, "slope": slope, "side": c * math.sqrt(1 + slope ** 2)}


def tongue_edges(j: dict[str, float], z: float) -> tuple[float, float]:
    """The right-hand tongue's (inner, outer) X edges at Z above the back face: narrowest at the neck, widening toward the head."""
    grow = (j["z_floor"] - z) * j["slope"]
    return j["groove_in"] + j["side"] + grow, j["groove_out"] - j["side"] - grow


def groove_edges(j: dict[str, float], z: float) -> tuple[float, float]:
    """The right-hand groove's (inner, outer) X edges at Z above the back face (the tongue's, grown by FIT_CLEARANCE)."""
    grow = (j["z_floor"] - z) * j["slope"]
    return j["groove_in"] + grow, j["groove_out"] - grow


def _prism(sign: int, z_lo: float, edges_lo: tuple[float, float], z_hi: float, edges_hi: tuple[float, float], z0: float, y0: float, length: float):
    """A prism along Y from y0, `length` long, whose X-Z section is the trapezoid between (z_lo, edges_lo) and (z_hi, edges_hi), each (inner, outer) as for the right-hand side; sign=-1 mirrors it.

    z0 is the back face's Z.
    """
    pts = [(sign * edges_lo[0], z0 + z_lo), (sign * edges_lo[1], z0 + z_lo), (sign * edges_hi[1], z0 + z_hi), (sign * edges_hi[0], z0 + z_hi)]
    plane = Plane(origin=(0, y0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))  # local x = X, local y = Z, extruded toward -Y
    return extrude(plane * Polygon(*_ccw(pts), align=None), amount=-length)


def _ridge(sign: int, x_in: float, x_out: float, y_centre: float, z_base: float, amplitude: float, half_length: float):
    """A cosine ridge across X (from x_in to x_out, mirrored by sign) on the face at z_base, `amplitude` proud at y_centre and tapering to nothing over half_length each way.

    Its base is sunk BOOLEAN_OVERLAP under z_base so it overlaps the solid it joins.
    """
    steps = 24
    ys = [y_centre - half_length + 2 * half_length * i / steps for i in range(steps + 1)]
    pts = [(y, z_base + amplitude * 0.5 * (1 + math.cos(math.pi * (y - y_centre) / half_length))) for y in ys] + [(ys[-1], z_base - BOOLEAN_OVERLAP), (ys[0], z_base - BOOLEAN_OVERLAP)]
    xa, xb = sorted((sign * x_in, sign * x_out))
    plane = Plane(origin=(xa, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))  # local x = Y, local y = Z, extruded toward +X
    return extrude(plane * Polygon(*_ccw(pts), align=None), amount=xb - xa)


def finger_piece():
    """The separately printed snap-finger piece: the integral adapter's fingers and tab, plus two dovetail tongues each with a detent ridge on its front face."""
    f, j = _adapter_frame("socket"), joint_geometry()
    z0, y_lo = f["z_back"], f["axis_y"] - FINGER_HEIGHT / 2
    piece = _socket_fingers(f["axis_y"], z0)
    z_in = j["z_tab"] - BOOLEAN_OVERLAP  # the tongue starts inside the tab so it fuses with it
    for sign in (-1, 1):
        piece += _prism(sign, z_in, tongue_edges(j, z_in), j["z_head"], tongue_edges(j, j["z_head"]), z0, y_lo, FINGER_HEIGHT)
        piece += _ridge(sign, *tongue_edges(j, j["z_head"] - BOOLEAN_OVERLAP), f["axis_y"], z0 + j["z_head"], DETENT_HEIGHT, DETENT_HALF_LENGTH)  # as wide as the tongue is where the ridge's sunk base ends, so it stays inside the flanks
    return piece


def harness_plate():
    """The plate for the fallback: the integral adapter's plate, less a back-face rebate for the tab and, for each tongue, a dovetail groove with a detent dimple in its floor."""
    f, j = _adapter_frame("socket"), joint_geometry()
    c, z0, y_lo = FIT_CLEARANCE, f["z_back"], f["axis_y"] - FINGER_HEIGHT / 2
    plate = _adapter_plate("socket")
    plate -= _box(-ADAPTER_WIDTH, ADAPTER_WIDTH, y_lo, f["y_top"] + 1, z0 - 1, z0 + j["z_tab"] + c)  # rebate: the tab's seat, open at the sides and top
    for sign in (-1, 1):
        # the groove opens at the plate's top edge and stops at y_lo, where the finger piece's bottom face seats
        plate -= _prism(sign, 0.0, groove_edges(j, 0.0), j["z_floor"], groove_edges(j, j["z_floor"]), z0, y_lo, f["y_top"] + 1 - y_lo)
        # the dimple: the ridge's shape grown by c in length and width, DETENT_HEIGHT into the floor, so the seated ridge (c below the floor) has c of air around its tip
        plate -= _ridge(sign, *tongue_edges(j, j["z_floor"] - BOOLEAN_OVERLAP), f["axis_y"], z0 + j["z_floor"], DETENT_HEIGHT, DETENT_HALF_LENGTH + c)
    return plate


if __name__ == "__main__":
    from build123d import export_step, export_stl

    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)
    for name, shape in (("u1_finger_fallback_plate", harness_plate()), ("u1_finger_fallback_fingers", finger_piece())):
        export_stl(shape, str(out / f"{name}.stl"))
        export_step(shape, str(out / f"{name}.step"))
    j = joint_geometry()
    print(f"fallback: groove floor x {j['groove_in']:.2f}..{j['groove_out']:.2f} at {j['z_floor']:.2f} mm above the back face, ridge {DETENT_HEIGHT:.2f} mm high")
