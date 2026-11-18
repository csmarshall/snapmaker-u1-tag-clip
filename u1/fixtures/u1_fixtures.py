"""Test fixtures for finding where and how thickly a tag reads on the Snapmaker U1 side panel.

Run with: uv run python u1_fixtures.py
Writes u1_standoff_strip.{stl,step} and u1_coil_finder_puck.{stl,step} beside this file.
"""
import sys
from pathlib import Path

from build123d import Box, Cylinder, Part, Pos, Text, extrude

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "chip"))  # the vendored label font lives with the chip
from chip_clip import LABEL_FONT_PATH  # noqa: E402
from licence_notice import export_step_with_notice, export_stl_with_notice  # noqa: E402

STICKER_DIAMETER = 25.0  # NTAG215 round sticker, as used by A-Jey's thing:7268905
FIT_CLEARANCE = 0.3  # per side, so the sticker drops in and out
POCKET_DEPTH = 0.6  # recess above the floor; the sticker is ~0.4mm thick, tune after printing
WALL = 3.0
POCKET_OVERSHOOT = 1.0  # cutter pokes above the top face so no coplanar sliver remains

STRIP_FLOORS = (0.4, 0.8, 1.2, 1.6, 2.0)  # plastic between sticker and panel, mm
LABEL_BAND = 6.0
ENGRAVE_DEPTH = 0.2

FINDER_FLOOR = 0.6  # thin on purpose; raise to the thickest standoff that still reads
HANDLE_WIDTH = 20.0
HANDLE_LENGTH = 50.0  # measured from the puck centre
MARK_HOLE_DIAMETER = 1.5  # pencil or awl hole at the sticker centre for marking the panel

POCKET_DIAMETER = STICKER_DIAMETER + 2 * FIT_CLEARANCE


def standoff_strip() -> Part:
    """Return a row of sticker pockets whose floors (the plastic over the tag) step through STRIP_FLOORS."""
    cell_x = POCKET_DIAMETER + 2 * WALL
    cell_y = cell_x + LABEL_BAND
    strip = None
    for index, floor in enumerate(STRIP_FLOORS):
        height = floor + POCKET_DEPTH
        x = index * cell_x
        cell = Pos(x, 0, height / 2) * Box(cell_x, cell_y, height)
        pocket = Pos(x, LABEL_BAND / 2, floor + (POCKET_DEPTH + POCKET_OVERSHOOT) / 2) * Cylinder(
            POCKET_DIAMETER / 2, POCKET_DEPTH + POCKET_OVERSHOOT
        )
        label_y = -cell_y / 2 + (LABEL_BAND + WALL) / 2
        label = Pos(x, label_y, height) * extrude(Text(f"{floor:.1f}", font_size=LABEL_BAND * 0.7, font_path=LABEL_FONT_PATH), amount=-ENGRAVE_DEPTH)
        cell = cell - pocket - label
        strip = cell if strip is None else strip + cell
    return strip


def coil_finder_puck() -> Part:
    """Return a handled puck holding one sticker under FINDER_FLOOR of plastic, with a centre mark hole."""
    puck_diameter = POCKET_DIAMETER + 2 * WALL
    height = FINDER_FLOOR + POCKET_DEPTH
    body = Pos(0, 0, height / 2) * Cylinder(puck_diameter / 2, height)
    handle = Pos(0, HANDLE_LENGTH / 2, height / 2) * Box(HANDLE_WIDTH, HANDLE_LENGTH, height)
    pocket = Pos(0, 0, FINDER_FLOOR + (POCKET_DEPTH + POCKET_OVERSHOOT) / 2) * Cylinder(
        POCKET_DIAMETER / 2, POCKET_DEPTH + POCKET_OVERSHOOT
    )
    mark_hole = Pos(0, 0, height / 2) * Cylinder(MARK_HOLE_DIAMETER / 2, height + 2 * POCKET_OVERSHOOT)
    return body + handle - pocket - mark_hole


if __name__ == "__main__":
    out = Path(__file__).parent
    for name, shape in (("u1_standoff_strip", standoff_strip()), ("u1_coil_finder_puck", coil_finder_puck())):
        export_stl_with_notice(shape, out / f"{name}.stl")
        export_step_with_notice(shape, out / f"{name}.step")
