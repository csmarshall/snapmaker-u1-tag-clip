"""Clip chip for the Snapmaker U1 tag dock, plus four numbered docks (one per U1 slot).

The chip carries a 25mm NTAG215 sticker sealed inside it (dropped in during a print pause), a clip on its front that holds the
filament end while the spool is on the shelf, and the material name engraved under its round end. The dock is a top-open slot
that takes the chip flat end first; its parts use the terms in the README: back plate, channels (with a funnel on top), lower
pocket (with the big slot digit), bottom stop and key post.

The clip arms are a close trace of Extrutim's Clip-Classic.stl (Printables 24371, CC BY-NC-SA), turned 180 degrees as one unit,
with the hook finger (wall A) made 2mm taller on purpose. The dock is to be attached to remmulegguh's snap-in plate (Printables
1625982, CC BY-NC-SA); the sticker-chip idea follows A-Jey (Thingiverse 7268905, CC BY-NC-SA). Files made from this script carry
the same licence; SOURCES.md has the details.

Chip frame: X = width, Y = up (the chip slides down -Y into the dock, flat end first), Z = front (arms side), back face at Z=0.

Printing: the chip prints back-down and pauses at PAUSE_HEIGHT for the sticker; the dock prints standing on its bottom stop
(flat end down), so nothing on it bridges or overhangs more than 45 degrees.
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
    loft,
)

# ---- fit -------------------------------------------------------------------------------------
FIT_CLEARANCE = 0.3  # every sliding gap between chip and dock derives from this; tune it with a fit test

# ---- sticker and chip body (mm) ---------------------------------------------------------------
STICKER_DIAMETER = 25.0
STICKER_CLEARANCE = 0.3  # per side, so the sticker drops into its pocket during the pause
BACK_SKIN = 0.6  # plastic between the sticker and the chip's back face (three 0.2mm layers)
POCKET_DEPTH = 0.6  # sealed sticker pocket; the sticker is about 0.4mm thick (not yet measured)
COIN_THICKNESS = 2.4  # plate behind the arms; leaves 0.6mm between the engraved label's floor and the pocket ceiling
COIN_RADIUS = 16.0  # half-width of the chip, and radius of its round end
TOP_MARGIN = 1.5  # space between the last arm wall and the start of the key extension
KEY_FLAT_END_EXTENSION = 6.0  # extra flat end below the clip arms that carries the key notch
KEY_POST_WIDTH = 4.0
KEY_POST_HEIGHT = 5.0  # an upside-down chip's round end lands on the post and sits this much too high
COIN_END_CORNER_RADIUS = 5.0  # rounds the flat end's two corners so the chip is nearly pill-shaped
PAUSE_HEIGHT = BACK_SKIN + POCKET_DEPTH  # pause the chip print at the layer that starts here and drop the sticker in

# ---- clip arms, measured from Clip-Classic.stl (y across the arms, z up) ------------------------
ARM_WALL_THICKNESS = 1.2
ARM_WALL_HEIGHT = 3.0  # wall A, B and C stand this high above the plate
ARM_LIP_HEIGHT = 2.02  # extra height of the curved-over lead-in on wall A (total clip height 5.92 - 0.9 base = 5.02)
# Wall A's top curls toward the channel. Rows are (height above the straight part, outer-face shift, inner-face shift) in mm, measured from Clip-Classic.stl at x=-5.
WALL_A_LIP = ((0.0, 0.0, 0.0), (0.1, 0.02, 0.0), (0.3, 0.05, 0.01), (0.5, 0.11, 0.03), (0.7, 0.18, 0.05), (0.9, 0.26, 0.09), (1.1, 0.35, 0.15),
              (1.3, 0.46, 0.21), (1.5, 0.58, 0.29), (1.7, 0.71, 0.38), (1.9, 0.86, 0.48), (2.02, 0.94, 0.45))
WALL_A_EXTRA_HEIGHT = 2.0  # the one deliberate change to Extrutim's clip, asked for by Charles: the hook finger (wall A) is this much taller so it stands proud of the pocket
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

# ---- engraving ---------------------------------------------------------------------------------
# The known names; their letters all share one line on the chip. Beyond the original set, these come from a 2026 survey of common filaments a U1 can print
# (Snapmaker, Bambu Lab, Polymaker, eSun listings); high-temperature lines (PAHT-CF, PPS-CF) are left out, and nylon keeps the "Nylon" spelling.
FILAMENTS = (
    "PLA", "PLA+", "PLA Silk", "PLA Matte", "PLA-CF",
    "PETG", "PETG+", "PETG HF", "PETG-CF", "PCTG",
    "ASA", "ABS", "PC",
    "TPU", "TPU 95A", "TPU 90A",
    "Nylon", "Nylon CF", "Nylon GF",
    "PVA",
)
LABEL_FONT_SIZE = 9.0
LABEL_EDGE_MARGIN = 1.5  # the engraved name stays this far inside the chip's edge
LABEL_HOOK_GAP = 1.5  # space between the top of the hook finger and the bottom of the label
COVER_DIGIT_MARGIN = 1.2  # gap between the slot digit and the lower pocket's edges; the digit is scaled to fill the height minus this
U1_SLOTS = (1, 2, 3, 4)  # one dock per U1 filament position, numbered left to right
ENGRAVE_DEPTH = 0.6  # deep enough to paint or fill, or to print in a second colour

# ---- dock (in the chip frame) ------------------------------------------------------------------
DOCK_BACK_GAP = FIT_CLEARANCE  # air between the chip's back face and the back plate
DOCK_SLOT_CLEARANCE = FIT_CLEARANCE  # per side, chip edge to channel wall, and chip front to lip
DOCK_FLOOR = 1.2  # back plate thickness: plastic between the chip and the printer panel, to be tuned from the standoff-strip test
DOCK_RAIL_WIDTH = 3.0
DOCK_LIP_OVERLAP = 2.0  # how far the lips reach over the chip's edge
DOCK_LIP_THICKNESS = 1.2
DOCK_BOTTOM_THICKNESS = 2.0
COVER_ARM_CLEARANCE = 2 * FIT_CLEARANCE  # air between the tops of walls B and C and the lower pocket's inside face
COVER_PLATE_THICKNESS = 1.2
COVER_HOOK_CLEARANCE = FIT_CLEARANCE  # the lower pocket's top edge stops this far beyond the hook finger's curled tip
TRACK_INTO_POCKET = 7.5  # the channels run this far down past the lower pocket's top edge and stop (5 to 10mm per Charles)
DOCK_COIN_PROTRUSION = 3.0  # how far the chip's round end would stand above the channels; the funnel sits on top of them
DOCK_FUNNEL_FLARE = 2.0  # how far each side of the mouth opens at the rim; 1mm of channel wall remains there
# Each side of the mouth follows the chip's own corner arc (COIN_END_CORNER_RADIUS): upright at the rim, curving in to meet the channel this far below it.
DOCK_FUNNEL_HEIGHT = math.sqrt(COIN_END_CORNER_RADIUS ** 2 - (COIN_END_CORNER_RADIUS - DOCK_FUNNEL_FLARE) ** 2)
DOCK_FUNNEL_BACK_DEPTH = 0.8  # how far the mouth opens toward the back at the rim, on the same curve; it starts above the sticker, which stays covered
DOCK_FUNNEL_LIP_DEPTH = 0.8  # how far the lips' undersides open toward the front at the rim, on the same curve; 0.4mm of lip remains there
FUNNEL_STEPS = 16  # slices along the arc
HINT_WIDTH = 12.0  # orientation hint engraved in the back plate above the lower pocket: the chip's bottom with its key cut-out, and a down arrow
HINT_DEPTH = 0.4  # leaves 0.8mm of back plate under the hint
HINT_GAP = 1.0  # space between the lower pocket's top edge and the hint

POCKET_DIAMETER = STICKER_DIAMETER + 2 * STICKER_CLEARANCE
# The clip is built as measured, wall A (the tallest, with the curled-over top and nub) at +ARM_BASE_Y, then turned 180 degrees about Z as one unit so wall A faces the
# chip's centre and the S-bend end sits in the flat end. Nothing inside the clip changes.
ARM_BASE_Y = 3.0
ARM_SHIFT_Y = ARM_BASE_Y - WALL_A_Y[0]  # applied before the turn
COIN_FLAT_END_Y = S_BEND[0][4] + ARM_SHIFT_Y + TOP_MARGIN + KEY_FLAT_END_EXTENSION  # distance from the sticker centre to the flat end
ARM_Y_FAR = -(S_BEND[0][4] + ARM_SHIFT_Y)  # after the turn: arm edge nearest the flat end
ARM_WALL_TOP_Z = COIN_THICKNESS + ARM_WALL_HEIGHT  # tops of walls B and C, and of wall A's straight part
ARM_TOP_Z = ARM_WALL_TOP_Z + WALL_A_EXTRA_HEIGHT + ARM_LIP_HEIGHT  # the hook finger's top
ARM_Y_HOOK_TIP = -(WALL_A_Y[1] + ARM_SHIFT_Y + max(row[2] for row in WALL_A_LIP))  # how far the hook's curled tip reaches toward the flat end, after the turn
KEY_NOTCH_WIDTH = KEY_POST_WIDTH + 2 * FIT_CLEARANCE
KEY_NOTCH_HEIGHT = KEY_POST_HEIGHT + 2 * FIT_CLEARANCE  # one clearance for the seat gap under the chip, one above the post


def _cosine_bump(x: float, half_width: float) -> float:
    """Smooth 0..1 bump, 1 at x=0 and 0 beyond +-half_width."""
    if abs(x) >= half_width:
        return 0.0
    return 0.5 * (1.0 + math.cos(math.pi * x / half_width))


def _ccw(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Return the points counter-clockwise; a clockwise face would extrude toward -Z."""
    area = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]))
    return points if area > 0 else points[::-1]


def _box(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float):
    """Axis-aligned box from its two corners."""
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)


def _s_bend_wall(lower_col: int, upper_col: int, z0: float):
    """Wall B (columns 1, 2 of S_BEND) or wall C (3, 4): plan outline from the traced S-bend table, standing ARM_WALL_HEIGHT high from z0."""
    half = [(row[0], row[lower_col], row[upper_col]) for row in S_BEND]
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
    """Wall A, the hook finger: a straight wall whose top curls toward the channel (WALL_A_LIP), extruded along X from a side profile in (y, z), plus the centre nub on its inner face."""
    outer, inner = WALL_A_Y
    rows = [(ARM_WALL_HEIGHT + WALL_A_EXTRA_HEIGHT + dz, outer + d_out, inner + d_in) for dz, d_out, d_in in WALL_A_LIP]
    profile = [(outer, 0.0), (inner, 0.0)] + [(y_in, z) for z, _, y_in in rows] + [(y_out, z) for z, y_out, _ in reversed(rows)]
    section = Polygon(*[(y + ARM_SHIFT_Y, z) for y, z in profile], align=None)
    # Polygon is drawn in XY; rotate so its Y becomes Z and its X becomes the chip's Y, then extrude along X.
    solid = extrude(Plane.YZ * section, amount=ARM_LENGTH / 2, both=True)
    xs = [-A_NUB_HALF_WIDTH + 2 * A_NUB_HALF_WIDTH * i / 30 for i in range(31)]
    y_face = inner + ARM_SHIFT_Y
    nub_outline = Polygon(*[(x, y_face - 0.05) for x in xs], *[(x, y_face + A_NUB_AMPLITUDE * _cosine_bump(x, A_NUB_HALF_WIDTH)) for x in reversed(xs)], align=None)
    return Pos(0, 0, z0) * (solid + extrude(nub_outline, amount=A_NUB_HEIGHT + WALL_A_EXTRA_HEIGHT))


def _cap_band(size: float) -> tuple[float, float]:
    """Baseline and cap height of the label font at this size, in the font's own frame (where Text puts them with align=None)."""
    bb = Text("H", font_size=size, align=None).bounding_box()
    return bb.min.Y, bb.max.Y


def _label_text(label: str, size: float, cap_centre_y: float):
    """The label centred left to right by its ink, with the middle of its capital-letter band at cap_centre_y, so descenders hang below and every name's letters share one line."""
    text = Text(label, font_size=size, align=None)
    bb = text.bounding_box()
    cap_lo, cap_hi = _cap_band(size)
    return Pos(-(bb.min.X + bb.max.X) / 2, cap_centre_y - (cap_lo + cap_hi) / 2) * text


def _label_font_size(label: str, cap_centre_y: float) -> float:
    """Largest font size up to LABEL_FONT_SIZE whose bounding box stays LABEL_EDGE_MARGIN inside the round end and clear of the dock's lips, so long names shrink instead of being hidden."""
    limit = COIN_RADIUS - LABEL_EDGE_MARGIN
    x_limit = COIN_RADIUS - DOCK_LIP_OVERLAP - LABEL_EDGE_MARGIN
    size = LABEL_FONT_SIZE
    while size > 2.0:
        bb = _label_text(label, size, cap_centre_y).bounding_box()
        corner = math.hypot(max(abs(bb.min.X), abs(bb.max.X)), max(abs(bb.min.Y), abs(bb.max.Y)))
        if corner <= limit and max(abs(bb.min.X), abs(bb.max.X)) <= x_limit:
            return size
        size -= 0.1
    return size


def _label_line() -> float:
    """The shared height for the middle of every name's capital letters: as low as it can go while the lowest descender of any known name keeps LABEL_HOOK_GAP above the hook finger.

    Sizes depend on the height (the round end narrows) and the height on the sizes, so this settles them together in a few passes.
    """
    floor = -ARM_BASE_Y + LABEL_HOOK_GAP
    line = floor + LABEL_FONT_SIZE
    for _ in range(4):
        lowest = min(_label_text(name, _label_font_size(name, line), line).bounding_box().min.Y for name in FILAMENTS)
        line += floor - lowest
    return line


LABEL_LINE_Y = _label_line()


def file_stem(label: str) -> str:
    """File-name-safe form of a filament name: "PLA+" -> "PLAplus", "Nylon CF" -> "Nylon_CF"."""
    return label.replace("+", "plus").replace(" ", "_")


def chip_parts(label: str):
    """Return (body, engraving) for one filament label: the body has the label cut out and the engraving fills the cut exactly, so a slicer can print them in two colours.

    There is no copy number: chips travel with spools and end up in any position. The sticker pocket is sealed inside the body (BACK_SKIN under it), filled during a print pause.
    """
    # Round end and flat end: the circle's own edge would stick out past the rectangle, so cut it at COIN_FLAT_END_Y.
    below_top = Pos(0, COIN_FLAT_END_Y / 2 - COIN_RADIUS) * Rectangle(4 * COIN_RADIUS, COIN_FLAT_END_Y + 2 * COIN_RADIUS)
    outline = (Circle(COIN_RADIUS) + Pos(0, COIN_FLAT_END_Y / 2) * Rectangle(2 * COIN_RADIUS, COIN_FLAT_END_Y)) & below_top
    # The key notch is cut before the turn, at +Y, and all four corners along the flat end (two outer, two at the notch) get the same rounding,
    # so the flat end reads like a little ghost's feet.
    key_notch = Pos(0, COIN_FLAT_END_Y - KEY_NOTCH_HEIGHT / 2 + 0.5) * Rectangle(KEY_NOTCH_WIDTH, KEY_NOTCH_HEIGHT + 1)
    face = (outline - key_notch).faces()[0]
    flat_corners = [v for v in face.vertices() if abs(v.Y - COIN_FLAT_END_Y) < 1e-6]
    plate = Rot(Z=180) * extrude(face.fillet_2d(COIN_END_CORNER_RADIUS, flat_corners), amount=COIN_THICKNESS)
    sticker_pocket = Pos(0, 0, BACK_SKIN) * Cylinder(POCKET_DIAMETER / 2, POCKET_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = plate - sticker_pocket

    arms = _lead_in_wall(COIN_THICKNESS)
    arms += _s_bend_wall(1, 2, COIN_THICKNESS)
    arms += _s_bend_wall(3, 4, COIN_THICKNESS)
    arms += _c_catches(COIN_THICKNESS)
    body += Rot(Z=180) * arms

    engrave = Pos(0, 0, COIN_THICKNESS) * extrude(_label_text(label, _label_font_size(label, LABEL_LINE_Y), LABEL_LINE_Y), amount=-ENGRAVE_DEPTH)
    return body - engrave, engrave


def _funnel_section(y: float, flare: float, back: float, lip: float, inner_half: float, lip_in: float, z_slot_front: float, z_open: float):
    """Cross-section of the chip's path at height y, as one T-shaped face in X-Z: the slot the chip fills plus the opening between the lips, grown by the given flares."""
    w, l = inner_half + flare, lip_in + flare
    zb, zs = -DOCK_BACK_GAP - back, z_slot_front + lip
    # z_dir (0,-1,0) makes the plane's local y point along global +Z, so the points read as (x, z).
    plane = Plane(origin=(0, y, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    return plane * Polygon((-w, zb), (w, zb), (w, zs), (l, zs), (l, z_open), (-l, z_open), (-l, zs), (-w, zs), align=None)


def _orientation_hint(y_base: float):
    """The cut for the hint engraved into the back plate's front face, read top to bottom: a scaled silhouette of the chip's flat end (rounded corners, rounded key notch left uncut), then a down arrow under it."""
    scale = HINT_WIDTH / (2 * COIN_RADIUS)
    height, arrow_len, gap = 4.0, 6.0, 1.0
    y_chip = y_base + arrow_len + gap  # silhouette's feet
    notch_w, notch_h = KEY_NOTCH_WIDTH * scale, KEY_NOTCH_HEIGHT * scale
    body = Pos(0, y_chip + height / 2) * Rectangle(HINT_WIDTH, height)
    notch = Pos(0, y_chip + notch_h / 2 - 0.5) * Rectangle(notch_w, notch_h + 1)
    face = (body - notch).faces()[0]
    feet = [v for v in face.vertices() if abs(v.Y - y_chip) < 1e-6]
    silhouette = face.fillet_2d(COIN_END_CORNER_RADIUS * scale, feet)
    tip = y_base  # the arrow points down, toward the lower pocket
    arrow = Polygon(*_ccw([(0, tip), (1.6, tip + 2.0), (0.5, tip + 2.0), (0.5, tip + arrow_len), (-0.5, tip + arrow_len), (-0.5, tip + 2.0), (-1.6, tip + 2.0)]), align=None)
    z_face = -DOCK_BACK_GAP
    return Pos(0, 0, z_face - HINT_DEPTH) * (extrude(silhouette, amount=HINT_DEPTH + 0.01) + extrude(arrow, amount=HINT_DEPTH + 0.01))


def dock_parts(slot: int | None) -> dict[str, object]:
    """Return the named parts of the dock for one U1 slot: back_plate, channels, lower_pocket, digit (None when slot is None), and dock, their union.

    The parts touch but do not overlap, so they can be coloured or printed in different filaments. The channels (rails, the band walls beside the lower pocket's top,
    and the lips) run from the open top to TRACK_INTO_POCKET below the lower pocket's top edge; a lofted funnel bevels the back plate, rails and lips evenly into one
    flat top rim. The lower pocket (side walls, cover plate, full-depth bottom stop and key post) carries the slot digit; its top edge stops just past the hook
    finger, which stands proud of it so a thumb run up the cover catches it and lifts the chip out.
    """
    inner_half = COIN_RADIUS + DOCK_SLOT_CLEARANCE
    outer_half = inner_half + DOCK_RAIL_WIDTH
    lip_in = COIN_RADIUS - DOCK_LIP_OVERLAP
    z_back = -DOCK_BACK_GAP - DOCK_FLOOR
    z_slot_front = COIN_THICKNESS + DOCK_SLOT_CLEARANCE
    z_front = z_slot_front + DOCK_LIP_THICKNESS
    z_cover_in = ARM_WALL_TOP_Z + COVER_ARM_CLEARANCE
    z_cover_out = z_cover_in + COVER_PLATE_THICKNESS
    y_bottom = -COIN_FLAT_END_Y - DOCK_SLOT_CLEARANCE - DOCK_BOTTOM_THICKNESS
    y_stop = y_bottom + DOCK_BOTTOM_THICKNESS
    y_top = COIN_RADIUS - DOCK_COIN_PROTRUSION  # where the whole channels end and the funnel begins
    y_rim = y_top + DOCK_FUNNEL_HEIGHT
    cover_top = ARM_Y_HOOK_TIP - COVER_HOOK_CLEARANCE
    track_end = cover_top - TRACK_INTO_POCKET

    back_plate = _box(-outer_half, outer_half, y_bottom, y_rim, z_back, -DOCK_BACK_GAP)

    channels = None
    for sign in (-1, 1):
        x_in, x_out = sorted((sign * inner_half, sign * outer_half))
        rail = _box(x_in, x_out, cover_top, y_rim, -DOCK_BACK_GAP, z_front)
        band_wall = _box(x_in, x_out, track_end, cover_top, -DOCK_BACK_GAP, z_cover_out)  # beside the lower pocket's top, as tall as the pocket
        # Lip with a 45 degree lower end, so it prints without support when the dock stands on its bottom stop.
        lip_profile = Polygon(*_ccw([(track_end + DOCK_LIP_THICKNESS, z_slot_front), (y_rim, z_slot_front), (y_rim, z_front), (track_end, z_front)]), align=None)
        lip_x0, lip_x1 = sorted((sign * lip_in, sign * inner_half))
        lip = Pos((lip_x0 + lip_x1) / 2, 0, 0) * extrude(Plane.YZ * lip_profile, amount=(lip_x1 - lip_x0) / 2, both=True)
        piece = rail + band_wall + lip
        channels = piece if channels is None else channels + piece

    # The funnel: the chip's path grows along the chip's corner arc from y_top (no flare) to the rim (full flare, arc upright), sliced and lofted,
    # then carried on past the rim so the cut leaves one flat top face. The back and lip bevels grow in the same proportion so the mouth is one shape.
    z_open = z_cover_out + 1
    r = COIN_END_CORNER_RADIUS
    sections = []
    for i in range(FUNNEL_STEPS + 1):
        y = y_top + DOCK_FUNNEL_HEIGHT * i / FUNNEL_STEPS
        flare = max(0.0, math.sqrt(max(r * r - (y_rim - y) ** 2, 0.0)) - (r - DOCK_FUNNEL_FLARE))
        grow = flare / DOCK_FUNNEL_FLARE
        sections.append(_funnel_section(y, flare, DOCK_FUNNEL_BACK_DEPTH * grow, DOCK_FUNNEL_LIP_DEPTH * grow, inner_half, lip_in, z_slot_front, z_open))
    above = _funnel_section(y_rim + 1, DOCK_FUNNEL_FLARE, DOCK_FUNNEL_BACK_DEPTH, DOCK_FUNNEL_LIP_DEPTH, inner_half, lip_in, z_slot_front, z_open)
    funnel = loft(sections, ruled=True) + loft([sections[-1], above], ruled=True)
    back_plate -= funnel
    back_plate -= _orientation_hint(cover_top + HINT_GAP)
    channels -= funnel

    lower_pocket = _box(-inner_half, inner_half, y_bottom, cover_top, z_cover_in, z_cover_out)  # cover plate
    for sign in (-1, 1):
        x_in, x_out = sorted((sign * inner_half, sign * outer_half))
        lower_pocket += _box(x_in, x_out, y_bottom, track_end, -DOCK_BACK_GAP, z_cover_out)  # side wall
    lower_pocket += _box(-outer_half, outer_half, y_bottom, y_stop, -DOCK_BACK_GAP, z_cover_out)  # bottom stop, full depth so the pocket is closed at the bottom
    lower_pocket += _box(-KEY_POST_WIDTH / 2, KEY_POST_WIDTH / 2, y_stop - 0.01, y_stop + KEY_POST_HEIGHT, -DOCK_BACK_GAP, z_cover_in)  # key post

    digit = None
    if slot is not None:
        unit_height = Text(str(slot), font_size=1.0).bounding_box().size.Y
        digit_size = (cover_top - y_bottom - 2 * COVER_DIGIT_MARGIN) / unit_height
        digit = Pos(0, (y_bottom + cover_top) / 2, z_cover_out) * extrude(Text(str(slot), font_size=digit_size), amount=-ENGRAVE_DEPTH)
        lower_pocket -= digit
    return {"back_plate": back_plate, "channels": channels, "lower_pocket": lower_pocket, "digit": digit, "dock": back_plate + channels + lower_pocket}


if __name__ == "__main__":
    from pathlib import Path

    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)
    for material in FILAMENTS:
        body, engraving = chip_parts(material)
        stem = f"chip_{file_stem(material)}"
        export_stl(body, str(out / f"{stem}.stl"))
        export_step(body, str(out / f"{stem}.step"))
        export_stl(engraving, str(out / f"{stem}_label.stl"))
    for slot in U1_SLOTS:
        parts = dock_parts(slot)
        for name, shape in parts.items():
            export_stl(shape, str(out / (f"dock_slot{slot}.stl" if name == "dock" else f"dock_slot{slot}_{name}.stl")))
        export_step(parts["dock"], str(out / f"dock_slot{slot}.step"))
    print(f"chip: pause at {PAUSE_HEIGHT:.2f} mm (start of that layer) and drop the sticker in; print back-down")
    print("dock: print standing on its bottom stop (flat end down)")
