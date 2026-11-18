"""The licence mark debossed on the finger dock's back (issue #22): where it is, how deep, and that it stays clear of everything that fits.

These build the cutter and the dock from u1_parts directly. They check placement against the dock's own extents, the sticker and the snap fingers, so a
moved strip or a deeper cut fails here. They can't tell whether 1.7 mm lettering is legible in print; that needs a test print.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "u1"), str(ROOT / "chip")]

import u1_parts as M  # noqa: E402
from chip_clip import DOCK_FLOOR, STICKER_CLEARANCE, STICKER_DIAMETER, _dock_extents  # noqa: E402

TOL = 1e-6


def test_mark_sits_in_the_plain_strip_below_the_sticker() -> None:
    """The lettering stays between the bottom stop and the sticker's edge, inside the dock's width."""
    cutter = M._licence_mark()
    bb = cutter.bounding_box()
    low, high = M.licence_mark_strip()
    assert bb.min.Y >= low - TOL and bb.max.Y <= high + TOL, (bb.min.Y, bb.max.Y, low, high)
    assert bb.max.Y <= M.STICKER_CENTRE_Y - (STICKER_DIAMETER / 2 + STICKER_CLEARANCE) + TOL
    half = _dock_extents()["outer_half"]
    assert -half < bb.min.X and bb.max.X < half


def test_mark_depth_leaves_the_back_plate() -> None:
    """It cuts only into the back face, no deeper than LICENCE_MARK_DEPTH, leaving at least LICENCE_MARK_MIN_PLATE of the plate."""
    bb = M._licence_mark().bounding_box()
    z_back = _dock_extents()["z_back"]
    assert abs(bb.min.Z - z_back) < 1e-3, bb.min.Z
    assert bb.max.Z - bb.min.Z <= M.LICENCE_MARK_DEPTH + 1e-3
    assert DOCK_FLOOR - (bb.max.Z - bb.min.Z) >= M.LICENCE_MARK_MIN_PLATE - 1e-3


def test_mark_misses_the_snap_fingers() -> None:
    """No lettering cuts into the fingers."""
    fingers = M.dock_fingers_parts(1)["fingers"]
    overlap = fingers & M._licence_mark()
    assert overlap.volume < 1e-6


def test_mark_is_cut_and_switch_turns_it_off(monkeypatch) -> None:
    """With the mark the dock loses a little volume; with LICENCE_MARK off it doesn't."""
    marked = M.dock_fingers_parts(1)["dock"].volume
    monkeypatch.setattr(M, "LICENCE_MARK", False)
    plain = M.dock_fingers_parts(1)["dock"].volume
    removed = plain - marked
    assert 0.5 < removed < 20.0, removed
