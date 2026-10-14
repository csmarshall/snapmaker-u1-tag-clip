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
ARM_LIP_HEIGHT = 2.0  # extra height of the leaning lead-in on wall A
ARM_LIP_LEAN = 0.9  # how far wall A's lip leans toward the channel
ARM_LENGTH = 20.0  # along X
WALL_A_Y = (-4.26, -3.06)  # (outer, inner) face at the clip's frame
WALL_B_Y = (-1.14, 0.06)  # at |x| >= BUMP_HALF_WIDTH
WALL_C_Y = (3.06, 4.26)
WALL_B_BUMP = 2.0  # S-bend: B moves +y by this at x=0
WALL_C_BUMP = 1.0
BUMP_HALF_WIDTH = 6.0
WALL_SAMPLES = 49  # points along each wavy wall

# ---- label ---------------------------------------------------------------------------------
LABEL_FONT_SIZE = 7.0
NUMBER_FONT_SIZE = 4.5
DOCK_NUMBER_FONT_SIZE = 5.0  # slot digit engraved on the dock's left lip
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
DOCK_COIN_PROTRUSION = 3.0  # how far the round end stands above the dock so it can be gripped; the dock still covers the whole sticker pocket

POCKET_DIAMETER = STICKER_DIAMETER + 2 * STICKER_CLEARANCE
# Arms are drawn at +Y, then the plate and arms are turned 180 degrees about Z so they sit in the flat end, below the pocket.
ARM_BASE_Y = 3.0
ARM_SHIFT_Y = ARM_BASE_Y - WALL_A_Y[0]
COIN_FLAT_END_Y = WALL_C_Y[1] + WALL_C_BUMP + ARM_SHIFT_Y + TOP_MARGIN


def _bump(x: float) -> float:
    """Smooth 0..1 bump, 1 at x=0 and 0 beyond +-BUMP_HALF_WIDTH."""
    if abs(x) >= BUMP_HALF_WIDTH:
        return 0.0
    return 0.5 * (1.0 + math.cos(math.pi * x / BUMP_HALF_WIDTH))


def _wavy_wall(y_faces: tuple[float, float], bump: float, z0: float):
    """Return a wall whose plan outline follows y_faces shifted by bump*_bump(x), standing ARM_WALL_HEIGHT high from z0."""
    xs = [-ARM_LENGTH / 2 + ARM_LENGTH * i / (WALL_SAMPLES - 1) for i in range(WALL_SAMPLES)]
    lower = [(x, y_faces[0] + ARM_SHIFT_Y + bump * _bump(x)) for x in xs]
    upper = [(x, y_faces[1] + ARM_SHIFT_Y + bump * _bump(x)) for x in reversed(xs)]
    outline = Polygon(*lower, *upper, align=None)
    return Pos(0, 0, z0) * extrude(outline, amount=ARM_WALL_HEIGHT)


def _lead_in_wall(z0: float):
    """Wall A: a straight wall with a leaning lip, extruded along X from a side profile in (y, z)."""
    outer, inner = WALL_A_Y
    profile = [
        (outer, 0.0),
        (inner, 0.0),
        (inner, ARM_WALL_HEIGHT),
        (inner + ARM_LIP_LEAN, ARM_WALL_HEIGHT + ARM_LIP_HEIGHT),
        (outer + ARM_LIP_LEAN + 0.0, ARM_WALL_HEIGHT + ARM_LIP_HEIGHT),
        (outer + 0.02, ARM_WALL_HEIGHT),
    ]
    section = Polygon(*[(y + ARM_SHIFT_Y, z) for y, z in profile], align=None)
    # Polygon is drawn in XY; rotate so its Y becomes Z and its X becomes the coin's Y, then extrude along X.
    solid = extrude(Plane.YZ * section, amount=ARM_LENGTH / 2, both=True)
    return Pos(0, 0, z0) * solid


def coin_parts(label: str, number: int | None):
    """Return (body, engraving) for one filament label and copy number: the body has the label cut out (number=None leaves the copy number off) and the engraving fills the cut exactly, so a slicer can print them in two colours."""
    # Round end and flat end: the circle's own edge would stick out past the rectangle, so cut it at COIN_FLAT_END_Y.
    below_top = Pos(0, COIN_FLAT_END_Y / 2 - COIN_RADIUS) * Rectangle(4 * COIN_RADIUS, COIN_FLAT_END_Y + 2 * COIN_RADIUS)
    outline = (Circle(COIN_RADIUS) + Pos(0, COIN_FLAT_END_Y / 2) * Rectangle(2 * COIN_RADIUS, COIN_FLAT_END_Y)) & below_top
    plate = Rot(Z=180) * extrude(outline, amount=COIN_THICKNESS)
    pocket = Pos(0, 0, -0.01) * Cylinder(POCKET_DIAMETER / 2, POCKET_DEPTH + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = plate - pocket

    arms = _lead_in_wall(COIN_THICKNESS)
    arms += _wavy_wall(WALL_B_Y, WALL_B_BUMP, COIN_THICKNESS)
    arms += _wavy_wall(WALL_C_Y, WALL_C_BUMP, COIN_THICKNESS)
    body += Rot(Z=180) * arms

    engrave = Pos(0, 6.0, COIN_THICKNESS) * extrude(Text(label, font_size=LABEL_FONT_SIZE), amount=-ENGRAVE_DEPTH)
    if number is not None:
        engrave += Pos(0, 12.0, COIN_THICKNESS) * extrude(Text(str(number), font_size=NUMBER_FONT_SIZE), amount=-ENGRAVE_DEPTH)
    return body - engrave, engrave


def dock(slot: int | None):
    """Return the placeholder dock for one U1 slot: back wall, side rails with lips, a bottom stop, top open (+Y), slot digit on the left lip (slot=None leaves it off)."""
    inner_half = COIN_RADIUS + DOCK_SLOT_CLEARANCE
    outer_half = inner_half + DOCK_RAIL_WIDTH
    z_back = -DOCK_BACK_GAP - DOCK_FLOOR
    z_front = COIN_THICKNESS + DOCK_SLOT_CLEARANCE + DOCK_LIP_THICKNESS
    y_bottom = -COIN_FLAT_END_Y - DOCK_SLOT_CLEARANCE - DOCK_BOTTOM_THICKNESS
    y_top = COIN_RADIUS - DOCK_COIN_PROTRUSION
    height = y_top - y_bottom
    depth = z_front - z_back

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
    if slot is None:
        return parts
    lip_centre_x = -(COIN_RADIUS - DOCK_LIP_OVERLAP + outer_half) / 2
    digit = Pos(lip_centre_x, (y_bottom + y_top) / 2, z_front) * extrude(Text(str(slot), font_size=DOCK_NUMBER_FONT_SIZE), amount=-ENGRAVE_DEPTH)
    return parts - digit


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
        export_stl(dock(slot), str(out / f"dock_slot{slot}.stl"))
    plain = out / "nonumber"
    plain.mkdir(exist_ok=True)
    for material in ("PLA", "PLA+", "PETG", "ASA", "ABS", "TPU", "Nylon"):
        body, engraving = coin_parts(material, None)
        stem = f"coin_{material.replace('+', 'plus')}"
        export_stl(body, str(plain / f"{stem}.stl"))
        export_stl(engraving, str(plain / f"{stem}_label.stl"))
    export_stl(dock(None), str(plain / "dock.stl"))
