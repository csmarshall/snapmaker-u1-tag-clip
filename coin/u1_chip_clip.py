"""Filament-clip coin for the Snapmaker U1 tag holder, plus a placeholder coin dock.

The coin carries a 25mm NTAG215 sticker in a pocket on its back, and three spring arms on its front that
pinch the filament end, with the material name engraved below the arms. The dock is a top-open slot that
takes the coin sticker-side first, with a thin back wall between the sticker and the printer panel.

Clip arm proportions (wall thickness, wall height, channel gaps, S-bend offsets, lead-in lip) were
measured from Extrutim's Clip-Classic.stl (Printables 24371, CC BY-NC-SA) at 1.75mm filament and
re-drawn here from those numbers; the dock's snap fingers come from remmulegguh's holder
(Printables 1625982, CC BY-NC-SA). The coin idea (sticker coin per filament) follows A-Jey
(Thingiverse 7268905, CC BY-NC-SA). Files made from this script carry the same licence.

Coin frame: X = width, Y = up (coin slides down -Y into the dock, flat end first), Z = front (arms side), back face at Z=0.
The round end is up with the label under it, upright; the flat end holds the clip arms and seats on the dock's bottom stop.
"""
import math

from build123d import (
    Align,
    Box,
    Circle,
    Cylinder,
    Plane,
    Polygon,
    Pos,
    Rot,
    Rectangle,
    Text,
    export_step,
    export_stl,
    extrude,
)

# ---- sticker and coin body (mm) -------------------------------------------------------------
STICKER_DIAMETER = 25.0
STICKER_CLEARANCE = 0.3  # per side
POCKET_DEPTH = 0.6  # sticker is ~0.4mm thick; the dock wall closes the pocket
COIN_THICKNESS = 2.0  # plate behind the arms; 1.4mm remains in front of the pocket
COIN_RADIUS = 16.0  # half-width of the coin, and radius of its rounded bottom
TOP_MARGIN = 1.5  # space between the last arm wall and the flat end

# ---- clip arms, measured from Clip-Classic.stl at x=-8.5 and x=0 (y across the arms, z up) ------
ARM_WALL_THICKNESS = 1.2
ARM_WALL_HEIGHT = 3.0  # wall A, B and C stand this high above the plate
ARM_LIP_HEIGHT = 2.02  # extra height of the curved-over lead-in on wall A (total clip height 5.92 - 0.9 base = 5.02)
# Wall A's top curls toward the channel. Rows are (height above the straight part, outer-face shift, inner-face shift) in mm, measured from Clip-Classic.stl at x=-5.
WALL_A_LIP = ((0.0, 0.0, 0.0), (0.1, 0.02, 0.0), (0.3, 0.05, 0.01), (0.5, 0.11, 0.03), (0.7, 0.18, 0.05), (0.9, 0.26, 0.09), (1.1, 0.35, 0.15),
              (1.3, 0.46, 0.21), (1.5, 0.58, 0.29), (1.7, 0.71, 0.38), (1.9, 0.86, 0.48), (2.02, 0.94, 0.45))
# A small nub on wall A's inner face at the clip's centre (x=0), cosine-shaped, running the wall's full height; measured at x=0 and x=+-0.2..1.5.
A_NUB_AMPLITUDE = 0.48
A_NUB_HALF_WIDTH = 1.5
A_NUB_HEIGHT = 4.9
ARM_LENGTH = 20.0  # along X
WALL_A_Y = (-4.26, -3.06)  # (outer, inner) face at the clip's frame
WALL_B_Y = (-1.137, 0.064)  # (lower, upper) face in the straight sections, |x| >= 6
WALL_C_Y = (3.064, 4.265)
# S-bend of walls B and C, traced from Clip-Classic.stl at z=2.5 in 0.3mm steps of |x| (symmetric about x=0): (|x|, B lower, B upper, C lower, C upper).
# The faces do not shift by the same amount, so B thickens from 1.2 to 1.35mm mid-bend; a plain cosine bump was off by up to 0.4mm.
S_BEND = (
    (0.0, 0.861, 2.064, 4.062, 5.262), (0.3, 0.854, 2.057, 4.059, 5.260), (0.6, 0.834, 2.039, 4.052, 5.252), (0.9, 0.796, 2.007, 4.034, 5.235),
    (1.2, 0.744, 1.964, 4.012, 5.215), (1.5, 0.674, 1.907, 3.982, 5.190), (1.8, 0.589, 1.836, 3.947, 5.157), (2.1, 0.486, 1.751, 3.904, 5.117),
    (2.4, 0.366, 1.654, 3.857, 5.072), (2.7, 0.226, 1.541, 3.802, 5.022), (3.0, 0.066, 1.414, 3.739, 4.965), (3.3, -0.116, 1.269, 3.669, 4.902),
    (3.6, -0.324, 1.106, 3.594, 4.832), (3.9, -0.554, 0.924, 3.509, 4.757), (4.2, -0.747, 0.721, 3.422, 4.672), (4.5, -0.894, 0.499, 3.324, 4.585),
    (4.8, -1.004, 0.301, 3.217, 4.487), (5.1, -1.079, 0.171, 3.122, 4.387), (5.4, -1.122, 0.096, 3.072, 4.302), (5.7, -1.137, 0.066, 3.064, 4.267),
    (6.0, -1.137, 0.064, 3.064, 4.265),
)
# A catch on wall C's inner face at each end: ramps in over x = 8.7..8.95, then stays to the end (10). Bands are (height above base from, to, inner face y), traced at x=9.5.
C_CATCH_X = (8.7, 8.95)
C_CATCH_BANDS = ((0.0, 1.3, 2.68), (1.3, 1.85, 2.43), (1.85, 3.0, 1.92))

# ---- label ---------------------------------------------------------------------------------
COIN_END_CORNER_RADIUS = 5.0  # rounds the flat end's two corners so the coin is nearly pill-shaped
LABEL_FONT_SIZE = 7.0
NUMBER_FONT_SIZE = 4.5
COVER_DIGIT_MARGIN = 1.2  # gap between the slot digit and the cover's edges; the digit is scaled to fill the cover height minus this
U1_SLOTS = (1, 2, 3, 4)  # one dock per U1 filament position, numbered as Charles labels them
ENGRAVE_DEPTH = 0.6  # deep enough to paint or fill, per Charles

# ---- placeholder dock (in the coin frame) --------------------------------------------------
DOCK_BACK_GAP = 0.2  # air between the coin's back face and the dock's back wall
DOCK_FLOOR = 1.2  # plastic between sticker and printer panel, tune from the standoff-strip test
DOCK_SLOT_CLEARANCE = 0.3  # per side, coin edge to rail
DOCK_RAIL_WIDTH = 3.0
DOCK_LIP_OVERLAP = 2.0  # rail lip over the coin's front-plate edge
DOCK_LIP_THICKNESS = 1.2
DOCK_BOTTOM_THICKNESS = 2.0
COVER_ARM_CLEARANCE = 1.0  # air between the tallest clip-arm point and the cover's inside face
COVER_PLATE_THICKNESS = 1.5
FILAMENT_DIAMETER = 1.75
FILAMENT_SLOT_CLEARANCE = 0.5  # per side, around the filament where it leaves the clip sideways
DOCK_FUNNEL_LENGTH = 6.0  # how far down from the open top the entry funnel reaches
DOCK_FUNNEL_FLARE = 2.0  # extra half-width of the slot mouth at the very top
DOCK_COIN_PROTRUSION = 3.0  # how far the round end stands above the dock so it can be gripped; the dock still covers the whole sticker pocket

POCKET_DIAMETER = STICKER_DIAMETER + 2 * STICKER_CLEARANCE
# The clip is built as measured, wall A (the tallest, with the curled-over top and nub) at +ARM_BASE_Y, then turned 180 degrees about Z as one unit so wall A faces the chip's centre
# and the S-bend end sits in the flat end. Nothing inside the clip changes.
ARM_BASE_Y = 3.0
ARM_SHIFT_Y = ARM_BASE_Y - WALL_A_Y[0]  # applied before the turn
COIN_FLAT_END_Y = S_BEND[0][4] + ARM_SHIFT_Y + TOP_MARGIN  # distance from the pocket centre to the flat end
ARM_Y_NEAR = -ARM_BASE_Y  # after the turn: arm edge nearest the sticker pocket (wall A's outer face)
ARM_Y_FAR = -(S_BEND[0][4] + ARM_SHIFT_Y)
ARM_TOP_Z = COIN_THICKNESS + ARM_WALL_HEIGHT + ARM_LIP_HEIGHT
# Where the filament runs through the clip at the arm ends (y of each channel centre, before the S-bend moves it).
CLIP_CHANNEL_Y = tuple(-((near + far) / 2 + ARM_SHIFT_Y) for near, far in ((WALL_A_Y[1], WALL_B_Y[0]), (WALL_B_Y[1], WALL_C_Y[0])))


def _cosine_bump(x: float, half_width: float) -> float:
    """Smooth 0..1 bump, 1 at x=0 and 0 beyond +-half_width."""
    if abs(x) >= half_width:
        return 0.0
    return 0.5 * (1.0 + math.cos(math.pi * x / half_width))


def _ccw(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Return the points counter-clockwise; a clockwise face would extrude toward -Z."""
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]))
    return points if area > 0 else points[::-1]


def _s_bend_wall(lower_col: int, upper_col: int, z0: float):
    """Wall B (columns 1, 2 of S_BEND) or wall C (3, 4): plan outline from the traced S-bend table, standing ARM_WALL_HEIGHT high from z0."""
    rows = [row for row in S_BEND]
    half = [(row[0], row[lower_col], row[upper_col]) for row in rows]
    xs = [-ARM_LENGTH / 2] + [-x for x, _, _ in reversed(half)] + [x for x, _, _ in half[1:]] + [ARM_LENGTH / 2]
    lo = [half[-1][1]] + [lo_y for _, lo_y, _ in reversed(half)] + [lo_y for _, lo_y, _ in half[1:]] + [half[-1][1]]
    hi = [half[-1][2]] + [hi_y for _, _, hi_y in reversed(half)] + [hi_y for _, _, hi_y in half[1:]] + [half[-1][2]]
    lower = [(x, y + ARM_SHIFT_Y) for x, y in zip(xs, lo)]
    upper = [(x, y + ARM_SHIFT_Y) for x, y in reversed(list(zip(xs, hi)))]
    return Pos(0, 0, z0) * extrude(Polygon(*_ccw(lower + upper), align=None), amount=ARM_WALL_HEIGHT)


def _c_catches(z0: float):
    """The catch on wall C's inner face at both ends, as stacked bands that approximate the traced slope."""
    ramp_start, ramp_end = C_CATCH_X
    c_inner = WALL_C_Y[0] + ARM_SHIFT_Y
    catches = None
    for sign in (-1, 1):
        for dz0, dz1, y_catch in C_CATCH_BANDS:
            y_in = y_catch + ARM_SHIFT_Y
            plan = [(sign * ramp_start, c_inner + 0.05), (sign * ramp_end, y_in), (sign * ARM_LENGTH / 2, y_in), (sign * ARM_LENGTH / 2, c_inner + 0.05)]
            band = Pos(0, 0, z0 + dz0) * extrude(Polygon(*_ccw(plan), align=None), amount=dz1 - dz0)
            catches = band if catches is None else catches + band
    return catches


def _lead_in_wall(z0: float):
    """Wall A: a straight wall whose top curls toward the channel (WALL_A_LIP), extruded along X from a side profile in (y, z), plus the centre nub on its inner face."""
    outer, inner = WALL_A_Y
    rows = [(ARM_WALL_HEIGHT + dz, outer + d_out, inner + d_in) for dz, d_out, d_in in WALL_A_LIP]
    profile = [(outer, 0.0), (inner, 0.0)] + [(y_in, z) for z, _, y_in in rows] + [(y_out, z) for z, y_out, _ in reversed(rows)]
    section = Polygon(*[(y + ARM_SHIFT_Y, z) for y, z in profile], align=None)
    # Polygon is drawn in XY; rotate so its Y becomes Z and its X becomes the coin's Y, then extrude along X.
    solid = extrude(Plane.YZ * section, amount=ARM_LENGTH / 2, both=True)
    xs = [-A_NUB_HALF_WIDTH + 2 * A_NUB_HALF_WIDTH * i / 30 for i in range(31)]
    y_face = inner + ARM_SHIFT_Y
    nub_outline = Polygon(*[(x, y_face - 0.05) for x in xs], *[(x, y_face + A_NUB_AMPLITUDE * _cosine_bump(x, A_NUB_HALF_WIDTH)) for x in reversed(xs)], align=None)
    return Pos(0, 0, z0) * (solid + extrude(nub_outline, amount=A_NUB_HEIGHT))


def coin_parts(label: str, number: int | None):
    """Return (body, engraving) for one filament label and copy number: the body has the label cut out (number=None leaves the copy number off) and the engraving fills the cut exactly, so a slicer can print them in two colours."""
    # Round end and flat end: the circle's own edge would stick out past the rectangle, so cut it at COIN_FLAT_END_Y.
    below_top = Pos(0, COIN_FLAT_END_Y / 2 - COIN_RADIUS) * Rectangle(4 * COIN_RADIUS, COIN_FLAT_END_Y + 2 * COIN_RADIUS)
    outline = (Circle(COIN_RADIUS) + Pos(0, COIN_FLAT_END_Y / 2) * Rectangle(2 * COIN_RADIUS, COIN_FLAT_END_Y)) & below_top
    face = outline.faces()[0]
    flat_corners = [v for v in face.vertices() if abs(v.Y - COIN_FLAT_END_Y) < 1e-6]
    plate = Rot(Z=180) * extrude(face.fillet_2d(COIN_END_CORNER_RADIUS, flat_corners), amount=COIN_THICKNESS)
    pocket = Pos(0, 0, -0.01) * Cylinder(POCKET_DIAMETER / 2, POCKET_DEPTH + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = plate - pocket

    arms = _lead_in_wall(COIN_THICKNESS)
    arms += _s_bend_wall(1, 2, COIN_THICKNESS)
    arms += _s_bend_wall(3, 4, COIN_THICKNESS)
    arms += _c_catches(COIN_THICKNESS)
    body += Rot(Z=180) * arms

    engrave = Pos(0, 6.0, COIN_THICKNESS) * extrude(Text(label, font_size=LABEL_FONT_SIZE), amount=-ENGRAVE_DEPTH)
    if number is not None:
        engrave += Pos(0, 12.0, COIN_THICKNESS) * extrude(Text(str(number), font_size=NUMBER_FONT_SIZE), amount=-ENGRAVE_DEPTH)
    return body - engrave, engrave


def dock_parts(slot: int | None):
    """Return (dock, digit) for one U1 slot: back wall, side rails with lips, a bottom stop, top open (+Y), and a full-width cover over the clip-arm area carrying the big slot digit.

    The cover's top edge lines up with the clip arms' top edge so a thumb run up the front catches the arms and lifts the coin out. It stands off the dock front on full side walls so it clears the arms; a narrow slot through the rail, lip and wall at each clip channel lets filament leave straight out sideways, while the tracks otherwise run unbroken from the open top to the bottom stop. digit is None when slot is None.
    """
    inner_half = COIN_RADIUS + DOCK_SLOT_CLEARANCE
    outer_half = inner_half + DOCK_RAIL_WIDTH
    z_back = -DOCK_BACK_GAP - DOCK_FLOOR
    z_front = COIN_THICKNESS + DOCK_SLOT_CLEARANCE + DOCK_LIP_THICKNESS
    y_bottom = -COIN_FLAT_END_Y - DOCK_SLOT_CLEARANCE - DOCK_BOTTOM_THICKNESS
    y_top = COIN_RADIUS - DOCK_COIN_PROTRUSION
    cover_top = ARM_Y_NEAR
    slot_top_z = COIN_THICKNESS + FILAMENT_DIAMETER + 2 * FILAMENT_SLOT_CLEARANCE
    slot_half = FILAMENT_DIAMETER / 2 + FILAMENT_SLOT_CLEARANCE
    z_cover_in = ARM_TOP_Z + COVER_ARM_CLEARANCE
    z_cover_out = z_cover_in + COVER_PLATE_THICKNESS

    def box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float):
        return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)

    z_slot_front = COIN_THICKNESS + DOCK_SLOT_CLEARANCE
    parts = box(-outer_half, outer_half, y_bottom, y_top, z_back, -DOCK_BACK_GAP)  # back wall
    for sign in (-1, 1):
        x_in, x_out = sorted((sign * inner_half, sign * outer_half))
        parts += box(x_in, x_out, y_bottom, y_top, z_back, z_front)  # rail
        lip_in = sign * (COIN_RADIUS - DOCK_LIP_OVERLAP)
        lip_lo, lip_hi = sorted((lip_in, sign * outer_half))
        parts += box(lip_lo, lip_hi, y_bottom, y_top, z_slot_front, z_front)  # lip over the coin edge
    parts += box(-outer_half, outer_half, y_bottom, y_bottom + DOCK_BOTTOM_THICKNESS, z_back, z_front)  # bottom stop
    # Entry funnel at the open top: rails and lips flare outward in plan, and the lips' undersides ramp up, so a coin that is a little off finds the track.
    flare_y = y_top - DOCK_FUNNEL_LENGTH
    ramp = (z_front - z_slot_front) / DOCK_FUNNEL_LENGTH
    lip_ramp = Polygon((flare_y, z_slot_front), (y_top + 1, z_slot_front), (y_top + 1, z_front + ramp), align=None)
    parts -= extrude(Plane.YZ * lip_ramp, amount=outer_half + 1, both=True)
    for sign in (-1, 1):
        for x_start, z0 in ((sign * inner_half, z_back), (sign * (COIN_RADIUS - DOCK_LIP_OVERLAP), z_slot_front)):
            x_mouth = sign * (inner_half + DOCK_FUNNEL_FLARE)
            corners = [(x_start, flare_y), (x_mouth, y_top), (x_mouth, y_top + 1), (x_start, y_top + 1)]
            mouth = Polygon(*(corners if sign > 0 else corners[::-1]), align=None)  # counter-clockwise, or extrude would run toward -Z
            parts -= Pos(0, 0, z0) * extrude(mouth, amount=z_front - z0 + 1)
    for sign in (-1, 1):
        x_in, x_out = sorted((sign * inner_half, sign * outer_half))
        parts += box(x_in, x_out, y_bottom, cover_top, z_front, z_cover_out)  # side wall carrying the cover
    parts += box(-outer_half, outer_half, y_bottom, cover_top, z_cover_in, z_cover_out)  # cover plate
    for channel_y in CLIP_CHANNEL_Y:
        for sign in (-1, 1):
            x0, x1 = sorted((sign * ARM_LENGTH / 2, sign * (outer_half + 1)))
            parts -= box(x0, x1, channel_y - slot_half, channel_y + slot_half, COIN_THICKNESS, slot_top_z)  # filament exit slot
    if slot is None:
        return parts, None
    unit_height = Text(str(slot), font_size=1.0).bounding_box().size.Y
    digit_size = (cover_top - y_bottom - 2 * COVER_DIGIT_MARGIN) / unit_height
    digit = Pos(0, (y_bottom + cover_top) / 2, z_cover_out) * extrude(Text(str(slot), font_size=digit_size), amount=-ENGRAVE_DEPTH)
    return parts - digit, digit


if __name__ == "__main__":
    from pathlib import Path

    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)
    for index, material in enumerate(("PLA", "PLA+", "PETG", "ASA", "ABS", "TPU", "Nylon"), start=1):
        body, engraving = coin_parts(material, index)
        stem = f"coin_{material.replace('+', 'plus')}_{index}"
        export_stl(body, str(out / f"{stem}.stl"))
        export_step(body, str(out / f"{stem}.step"))
        export_stl(engraving, str(out / f"{stem}_label.stl"))
    for slot in U1_SLOTS:
        dock_body, dock_digit = dock_parts(slot)
        export_stl(dock_body, str(out / f"dock_slot{slot}.stl"))
        export_stl(dock_digit, str(out / f"dock_slot{slot}_digit.stl"))
    plain = out / "nonumber"
    plain.mkdir(exist_ok=True)
    for material in ("PLA", "PLA+", "PETG", "ASA", "ABS", "TPU", "Nylon"):
        body, engraving = coin_parts(material, None)
        stem = f"coin_{material.replace('+', 'plus')}"
        export_stl(body, str(plain / f"{stem}.stl"))
        export_stl(engraving, str(plain / f"{stem}_label.stl"))
    export_stl(dock_parts(None)[0], str(plain / "dock.stl"))
