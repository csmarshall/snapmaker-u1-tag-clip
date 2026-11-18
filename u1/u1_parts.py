"""The U1-specific parts built on the chip and its dock (chip/chip_clip.py): the socket adapter, the dock mount, the blank cover, and the docks that plug into the Snapmaker U1's
spool-holder socket (the dock with snap fingers, and the integrated dovetail dock), plus a stand-in of 1waynger1's hub adapter for the viewer and checks.

Frame: the chip frame of chip/chip_clip.py (X width, Y up the dock, Z out from the panel). Nothing here changes the chip or the generic dock.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "chip"))  # the generic chip and dock live beside this folder
from build123d import (  # noqa: E402
    Align,
    Circle,
    Cylinder,
    Kind,
    Plane,
    Polygon,
    Pos,
    Rectangle,
    RectangleRounded,
    Text,
    extrude,
    offset,
)
from chip_clip import ENGRAVE_DEPTH, LABEL_FONT_PATH, FIT_CLEARANCE, MOUNT_GROOVE_DEPTH, _box, _ccw, _dock_extents, dock_parts  # noqa: E402
from socket_fingers import FINGER_HEIGHT, FINGER_SPREAD, bevel_leg, hook_half_width, hook_step, spread_outline  # noqa: E402

# ---- mounts. The dock mount slides down into a slot and holds the dock on top of whatever carries that slot: 1waynger1's hub adapter (his "Snapmaker U1
# Filament Hub Replacement" base, MakerWorld 2152529, which many owners already run), or our socket adapter, which snaps into the bare socket. Both
# plug into the spool-holder socket; the stock spool holder is gone. The dock itself is the same print on either, and on its own it tapes to the panel.
# The slot is his: measured from his "Machine Interface" object (tst.3mf, 2026-10-14). His files are under a Standard Digital File License, so only these
# numbers are used here (an interface, not his model); our adapter copies the slot so the one dock mount fits both.
ADAPTER_WIDTH = 30.48
ADAPTER_LENGTH = 42.95
ADAPTER_THICKNESS = 7.87  # the adapter's plate, from the panel to its front face
# The slot, the same along the adapter's whole length and open at both ends: (half-width, depth from the plate's front face) from the mouth to the closed back.
ADAPTER_SLOT_PROFILE = ((5.22, 0.0), (5.22, 0.44), (8.93, 4.15), (4.62, 6.64))
ADAPTER_CORNER_RADIUS = 4.0
HUB_AXIS_FROM_NEAR_END = 19.37  # on his adapter the plug (and socket axis) is off-centre: this far from one end, ADAPTER_LENGTH minus this from the other
HUB_NEAR_END_UP = True  # which end of his adapter is up in the printer; not yet confirmed on Charles's printer, and it moves the sticker by about 4mm
HUB_PLUG_DIAMETER = 26.5  # for the stand-in of his adapter drawn in the viewer only
HUB_PLUG_DEPTH = 25.3
SOCKET_PLATE_FLAT = 5.0  # remmulegguh's plate is flat across its top this far above the socket axis, level with his fingers' top face, so it prints standing on both
SOCKET_ADAPTER_TOP_ABOVE_AXIS = SOCKET_PLATE_FLAT  # our adapter's top edge, level with the fingers' top face for the same reason
SOCKET_PLATE_RADIUS = 15.8  # the blank cover's round plate, as on remmulegguh's holder
SOCKET_COVER_THICKNESS = 3.0  # the blank cover's plate, as thick as remmulegguh's
# Measured, not derivable: the width of 1waynger1's plug where it meets the panel (26.87mm), the best figure we have for the socket bore until one is measured on the printer.
SOCKET_BORE_DIAMETER = 26.9
SOCKET_COVER_OVERLAP = 1.5  # how far the blank cover's plate reaches past the bore's top edge
COVER_LABEL_MAX_WIDTH = 0.7 * 2 * SOCKET_PLATE_RADIUS  # a free-text label on the cover (the spread sweep's +1.0) shrinks to fit this width
SOCKET_COVER_FLAT = SOCKET_BORE_DIAMETER / 2 + SOCKET_COVER_OVERLAP  # the cover's flat top above the axis: it stands on this when printed, the fingers on supports
MOUNT_TONGUE_LENGTH = 30.0  # how far the dock mount's tongue reaches down into the slot
MOUNT_RISER = 3.0  # the crossbar resting on the adapter's top edge, under the dock
MOUNT_ARM_WIDTH = 3.0  # each side arm, beside the dock
# The integrated dock (dock_integrated_parts) has no mount: its own stem carries the dovetail. The stem is the slot's section grown by this much, so it is wider than the slot
# and its underside rests on the adapter's top edge in the same place the mount's crossbar does. Not derivable from a fit: it only has to leave a bearing ring on the plate's top
# edge. 3 mm is the dock's own rail width, kept narrow so the ring is a short bridge when the dock prints on its tongue end.
INTEGRATED_SHOULDER = 3.0
# The dock mount's own parts: each arm ends in an L clamp over the dock's middle band (see the groove constants in chip/chip_clip.py): its side wall beside the dock and a front jaw over
# the rail's front edge, with the panel closing the C, plus a tongue in a groove in the dock's side face, which stops the dock sliding up or down.
MOUNT_TONGUE_TIP = 0.4  # flat at the tongue's tip, front to back; above it the tongue slopes back to the arm so the dock cams the arms apart as it is pushed in
MOUNT_JAW_REACH = 1.0  # how far the jaw reaches in over the rail's front edge
MOUNT_JAW_THICKNESS = 1.2


def _socket_fingers(axis_y: float, z_back: float, spread: float = FINGER_SPREAD):
    """remmulegguh's snap fingers, going into the socket from the panel at z_back, centred on a socket axis at axis_y.

    Fingers come from u1/socket_fingers.py, mapped from his frame (socket axis along x, +z down) into this one: sideways stays sideways, depth goes to -Z,
    down goes to -Y. That mapping is a proper rotation (determinant +1), so nothing is mirrored.
    `spread` (mm per side, default FINGER_SPREAD, Charles's sweep choice; 0 = the traced outline exactly) moves the arms and hooks outward with the root fixed; see socket_fingers.spread_outline.
    """
    # The outline is (depth into the socket, sideways); on a plane whose local x is this X and local y is -Z, a point is (sideways, depth - z_back).
    finger_plane = Plane(origin=(0, axis_y - FINGER_HEIGHT / 2, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
    fingers = extrude(finger_plane * Polygon(*_ccw([(side, depth - z_back) for depth, side in spread_outline(spread)]), align=None), amount=FINGER_HEIGHT)
    return fingers - _hook_bevel_cutters(axis_y, z_back, spread)


def _hook_bevel_cutters(axis_y: float, z_back: float, spread: float):
    """The two wedges that bevel the hooks' leading corners: where the retaining step meets the end face that leads when the part is turned counter-clockwise seen from the front.

    Seen from the front (+Z toward the viewer, X right, Y up, so counter-clockwise is positive rotation about +Z) the +X hook moves toward +Y and the -X hook toward -Y,
    so the leading corners are the +X hook's top (+Y) one and the -X hook's bottom (-Y) one: the two that a 180 degree turn about the socket axis exchanges. Each wedge is a right triangle
    of leg bevel_leg() in the (Y, depth) plane, with its right angle at the corner, running from the step's inner side out past the hook's widest point; the cut leaves the 45 degree face the turned hook rides inward on.
    The wedge starts at the step's inner side, so the arm and the hook's inner half are not touched, and it never reaches the fingers' mid-height section.
    """
    leg = bevel_leg(spread)
    if leg == 0:
        return None
    depth, inner, _ = hook_step(spread)
    outer = hook_half_width(spread)  # the wedge runs out past the hook's widest point, so the flank beyond the step is bevelled too
    e = 0.2  # overshoot past the faces being cut, so the wedge leaves no sliver
    wedges = None
    for sign in (1, -1):
        y_end = axis_y + sign * FINGER_HEIGHT / 2
        # (Y, depth) corners of the wedge: the right angle at the step's end corner, one leg along the end face, the other along the step; mapped to (Y, Z) with Z = z_back - depth.
        tri = [(y_end + sign * e, z_back - depth), (y_end - sign * leg, z_back - depth), (y_end + sign * e, z_back - depth - leg - e)]
        x_start = inner if sign > 0 else -outer - e  # the wedge spans the inner side of the step to e beyond the hook's widest point (on the -X hook mirrored)
        plane = Plane(origin=(x_start, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))  # local x = Y, local y = z_dir x x_dir = Z; extrudes toward +X
        wedge = extrude(plane * Polygon(*_ccw(tri), align=None), amount=outer - inner + e)
        wedges = wedge if wedges is None else wedges + wedge
    return wedges


def _band_clamp(sign: int, y_lo: float, y_hi: float):
    """One side's arm, beside the dock from y_lo to y_hi, ending in an L clamp over the dock's middle band with a tongue that snaps into the side groove.

    The jaw's front face slopes, so the dock pushes straight in from the front and cams the arms apart; the tongue's back is square, so it stays.
    """
    d = _dock_extents()
    z_back, outer, z_rail = d["z_back"], d["outer_half"], d["z_rail_front"]
    (b0, b1), (gy0, gy1), (gz0, gz1) = d["band"], d["groove_y"], d["groove_z"]
    c = FIT_CLEARANCE
    arm_in, arm_out = sign * (outer + c), sign * (outer + c + MOUNT_ARM_WIDTH)
    x0, x1 = sorted((arm_in, arm_out))
    arm = _box(x0, x1, y_lo, y_hi, z_back, z_rail)
    # The jaw: the arm's section in X-Z over the band, the side wall rising past the rail's front and the jaw leaning in over it.
    z_jaw = z_rail + c
    x_tip = sign * (outer - MOUNT_JAW_REACH)
    profile = [(arm_in, z_back), (arm_out, z_back), (arm_out, z_jaw + MOUNT_JAW_THICKNESS), (x_tip, z_jaw + MOUNT_JAW_THICKNESS * 0.2), (x_tip, z_jaw), (arm_in, z_jaw)]
    plane = Plane(origin=(0, b0 + c, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))  # local x = X, local y = Z, extruded toward +Y
    arm += extrude(plane * Polygon(*_ccw(profile), align=None), amount=-((b1 - c) - (b0 + c)))
    engage = MOUNT_GROOVE_DEPTH - c  # how far the tongue reaches into its groove
    slope = c * math.sqrt(2)  # the tongue's chamfered ends sit this far inside the groove's, measured along Y
    ty0, ty1 = gy0 + slope - c, gy1 - slope + c  # the tongue's ends at the arm's face
    tip = sign * (outer - engage)
    # The tongue is where two prisms meet: its outline seen from the front (chamfered ends, X-Y) and its section seen from above (square back, sloped front, X-Z).
    ends = Polygon(*_ccw([(arm_in, ty0), (tip, ty0 + c + engage), (tip, ty1 - c - engage), (arm_in, ty1)]), align=None)
    front = Pos(0, 0, gz0 + c) * extrude(ends, amount=(gz1 - c) - (gz0 + c))
    section = [(arm_in, gz0 + c), (tip, gz0 + c), (tip, gz0 + c + MOUNT_TONGUE_TIP), (arm_in, gz1 - c)]
    plane = Plane(origin=(0, ty0, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    return arm + (front & extrude(plane * Polygon(*_ccw(section), align=None), amount=-(ty1 - ty0)))


ADAPTERS = ("hub", "socket")  # 1waynger1's hub adapter, and our socket adapter


def _adapter_top_above_axis(adapter: str) -> float:
    if adapter == "socket":
        return SOCKET_ADAPTER_TOP_ABOVE_AXIS
    return HUB_AXIS_FROM_NEAR_END if HUB_NEAR_END_UP else ADAPTER_LENGTH - HUB_AXIS_FROM_NEAR_END


def _adapter_frame(adapter: str) -> dict[str, float]:
    """Where an adapter sits in the dock's frame: its top edge just under the dock mount's crossbar, its back on the panel, its slot centred under the dock."""
    d = _dock_extents()
    y_top = d["y_bottom"] - FIT_CLEARANCE - MOUNT_RISER
    return {"y_top": y_top, "z_back": d["z_back"], "z_front": d["z_back"] + ADAPTER_THICKNESS, "axis_y": y_top - _adapter_top_above_axis(adapter)}


def _slot_section(shrink: float):
    """The slot's section in X-Z (the adapter's front face at z_front), grown inward by `shrink` on every side when shrink is positive (the mount's tongue)."""
    z_front = _adapter_frame("socket")["z_front"]  # the same for both adapters
    half = [(w, z_front - depth) for w, depth in ADAPTER_SLOT_PROFILE]
    face = Polygon(*_ccw([(-w, z) for w, z in half] + [(w, z) for w, z in reversed(half)]), align=None)
    return offset(face, amount=-shrink, kind=Kind.INTERSECTION).faces()[0] if shrink else face


def _adapter_plate(adapter: str):
    """An adapter's plate on the panel, with the slot through its whole length."""
    f = _adapter_frame(adapter)
    plate = Pos(0, f["y_top"] - ADAPTER_LENGTH / 2, f["z_back"]) * extrude(RectangleRounded(ADAPTER_WIDTH, ADAPTER_LENGTH, ADAPTER_CORNER_RADIUS), amount=ADAPTER_THICKNESS)
    plane = Plane(origin=(0, f["y_top"] + 1, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))  # local x = X, local y = Z, extruded toward -Y
    return plate - extrude(plane * _slot_section(0), amount=ADAPTER_LENGTH + 2)


def dock_mount_parts() -> dict[str, object]:
    """The dock mount: slides down into either adapter's slot from above and holds the dock on top of the adapter.

    A tongue (the slot's section, less FIT_CLEARANCE all round) runs MOUNT_TONGUE_LENGTH down the slot; above the adapter a crossbar, as deep as the plate,
    rests on its top edge and carries the dock's bottom stop, and two arms rise beside the dock to L clamps over its middle band (see _band_clamp).
    The dock pushes in from the front; the mount lifts straight out. Prints upside down, standing on the arms' ends.
    """
    d, f = _dock_extents(), _adapter_frame("socket")
    arm_out = d["outer_half"] + FIT_CLEARANCE + MOUNT_ARM_WIDTH
    y_cross = f["y_top"] + MOUNT_RISER  # the crossbar's top, under the dock's bottom stop
    plane = Plane(origin=(0, f["y_top"], 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    mount = extrude(plane * _slot_section(FIT_CLEARANCE), amount=MOUNT_TONGUE_LENGTH)
    mount += _box(-arm_out, arm_out, f["y_top"], y_cross, f["z_back"], f["z_front"])
    for sign in (-1, 1):
        mount += _band_clamp(sign, y_cross, d["band"][1] - FIT_CLEARANCE)
    return {"dock_mount": mount}


def dock_integrated_parts(slot: int | None) -> dict[str, object]:
    """The dock with the adapter's dovetail built in, for either adapter (the slot is shared), so it slides straight into the slot with no dock mount.

    The dock is dock_parts(slot) without the mount's side grooves (there is no mount to grip them, so the rails stay full width). Below its bottom end a stem spans the FIT_CLEARANCE + MOUNT_RISER gap the mount's crossbar fills: the slot's section grown by
    INTEGRATED_SHOULDER (and kept inside the adapter plate's outline), so its underside rests on the adapter's top edge with the dock exactly where it sits on the mount.
    Under that, the tongue is the slot's section less FIT_CLEARANCE all round for MOUNT_TONGUE_LENGTH, as in dock_mount_parts. Returns dock (body, stem and tongue), accent (as in
    dock_parts) and stem (the added geometry alone).
    """
    parts = dock_parts(slot, mount_grooves=False)
    d, f = _dock_extents(), _adapter_frame("socket")
    plane = Plane(origin=(0, f["y_top"], 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))  # local x = X, local y = Z, extruded toward -Y
    tongue = extrude(plane * _slot_section(FIT_CLEARANCE), amount=MOUNT_TONGUE_LENGTH)
    shoulder_plane = Plane(origin=(0, d["y_bottom"], 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    grown = offset(_slot_section(0), amount=INTEGRATED_SHOULDER, kind=Kind.INTERSECTION).faces()[0]
    plate = _box(-ADAPTER_WIDTH / 2, ADAPTER_WIDTH / 2, f["y_top"], d["y_bottom"], f["z_back"], f["z_front"])
    shoulder = extrude(shoulder_plane * grown, amount=d["y_bottom"] - f["y_top"]) & plate
    stem = shoulder + tongue
    return {"dock": parts["dock"] + stem, "accent": parts["accent"], "stem": stem}


STICKER_CENTRE_Y = 0.0  # the chip frame's origin is the sticker's centre (the recess is centred on it), so this is also the dock's socket axis in dock_fingers_parts


def dock_fingers_parts(slot: int | None, spread: float = FINGER_SPREAD) -> dict[str, object]:
    """The dock with remmulegguh's snap fingers on its back, no adapter, slot, dovetail or mount (issue #8): it plugs into the spool-holder socket where a spool would sit.

    The dock is dock_parts(slot, mount_grooves=False) with its back face on the panel plane (z = _dock_extents()["z_back"]) and the fingers' axis through the sticker's
    centre, so the sticker sits on the socket axis. The fingers' 0.3 mm tab, in front of the panel face, is buried in the back plate. Returns dock (body and fingers),
    accent (as in dock_parts) and fingers (the added geometry alone). `spread` is as in _socket_fingers (default FINGER_SPREAD).
    """
    parts = dock_parts(slot, mount_grooves=False)
    fingers = _socket_fingers(STICKER_CENTRE_Y, _dock_extents()["z_back"], spread)
    return {"dock": parts["dock"] + fingers, "accent": parts["accent"], "fingers": fingers}


def socket_adapter_parts() -> dict[str, object]:
    """Our socket adapter: remmulegguh's snap fingers behind a plate with 1waynger1's slot, so the dock mount fits it as it fits his hub adapter.

    The plate's top edge is level with the fingers' top face (SOCKET_ADAPTER_TOP_ABOVE_AXIS), so it prints standing on both with the slot's faces upright.
    """
    f = _adapter_frame("socket")
    return {"socket_adapter": _adapter_plate("socket") + _socket_fingers(f["axis_y"], f["z_back"])}


def hub_adapter_standin() -> dict[str, object]:
    """A stand-in for 1waynger1's hub adapter, drawn from the measured numbers above, for the viewer and checks: plate, slot and plug. Not his model, and not a part to print."""
    f = _adapter_frame("hub")
    plug = Pos(0, f["axis_y"], f["z_back"] - HUB_PLUG_DEPTH) * Cylinder(HUB_PLUG_DIAMETER / 2, HUB_PLUG_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return {"hub_adapter": _adapter_plate("hub") + plug}


def sticker_above_axis(adapter: str) -> float:
    """How far above the socket axis the sticker's centre sits with the dock on the dock mount in that adapter."""
    return -_adapter_frame(adapter)["axis_y"]


def cover_parts(slot: int | None, spread: float = FINGER_SPREAD, label: str | None = None) -> dict[str, object]:
    """The blank cover for an unused socket: the snap fingers and a round plate covering the whole bore (flat across its top, to stand on when printed), with the slot digit inlaid in the accent colour (none when slot is None).

    It sits on the same socket axis as the socket adapter, so the two can be compared in place.
    `spread` (mm per side, default FINGER_SPREAD; 0 = exactly the traced fingers) widens the fingers outward for the grip sweep (u1/docs/FINGER_SPREAD.md). `label` engraves that text in place of the slot digit, scaled down if it would run wider than the plate allows.
    """
    assert SOCKET_COVER_FLAT < SOCKET_PLATE_RADIUS, "the cover's flat top would cut the plate off above its round edge"
    f = _adapter_frame("socket")
    axis_y, z_back, r = f["axis_y"], f["z_back"], SOCKET_PLATE_RADIUS
    below_flat = Pos(0, axis_y + SOCKET_COVER_FLAT - 2 * r) * Rectangle(4 * r, 4 * r)
    plate = Pos(0, 0, z_back) * extrude(((Pos(0, axis_y) * Circle(r)) & below_flat).faces()[0], amount=SOCKET_COVER_THICKNESS)
    cover = plate + _socket_fingers(axis_y, z_back, spread)
    accent = None
    if slot is not None or label is not None:
        text = str(slot) if label is None else label
        unit = Text(text, font_size=1.0, font_path=LABEL_FONT_PATH).bounding_box().size
        size = 2 * r * 0.55 / unit.Y
        if label is not None:
            size = min(size, COVER_LABEL_MAX_WIDTH / unit.X)
        accent = Pos(0, axis_y - 2, z_back + SOCKET_COVER_THICKNESS) * extrude(Text(text, font_size=size, font_path=LABEL_FONT_PATH), amount=-ENGRAVE_DEPTH)
        cover -= accent
    return {"cover": cover, "accent": accent}
