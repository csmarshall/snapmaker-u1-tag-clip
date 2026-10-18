"""Checks for the dock with remmulegguh's snap fingers on its back (u1/docs/DOCK_FINGERS.md, issue #8).

Run the build first. Most checks compare the part with numbers from the same script, so they show consistency with its own parameters, not that anything fits a socket
or that a sticker reads at the loop centre. The check against his holder's real fingers is independent when his file is present locally.
"""
import functools
from pathlib import Path

import numpy as np
import pytest
import shapely
import trimesh
from build123d import export_stl

from u1_model import M, ROOT, _mesh, _overlap  # noqa: E402

from socket_fingers import FINGER_SPREAD, spread_outline  # noqa: E402

from print_orientation import OVERHANG_LIMIT  # noqa: E402
from print_plates import BED_CONTACT, FINGERS_PARTS, ON_BOTTOM_STOP  # noqa: E402

Z_BACK = M._dock_extents()["z_back"]
TAB_DEPTH = 0.3  # the traced outline starts this far in front of the panel face (see socket_fingers.py)
BORE_RADIUS = M.SOCKET_BORE_DIAMETER / 2


def _part(slot: int = 1) -> trimesh.Trimesh:
    return _mesh(f"dock_fingers_slot{slot}.stl")


@functools.lru_cache(maxsize=None)
def _flat_dock(slot: int) -> trimesh.Trimesh:
    """dock_parts(slot, mount_grooves=False), built here: the dock the finger variant must contain."""
    path = Path(ROOT / "u1" / "out" / f"_flat_dock_slot{slot}.stl")
    export_stl(M.dock_parts(slot, mount_grooves=False)["dock"], str(path))
    mesh = trimesh.load(path, force="mesh")
    path.unlink()
    return mesh


@pytest.mark.parametrize("slot", M.U1_SLOTS)
def test_dock_above_and_around_the_fingers_is_the_groove_free_dock(slot):
    """The groove-free dock lies wholly inside the part, and in front of the tab the part has exactly the dock's volume."""
    new, flat = _part(slot), _flat_dock(slot)
    assert new.is_watertight
    assert _overlap(new, flat) == pytest.approx(flat.volume, rel=1e-6)
    in_front = trimesh.creation.box(bounds=[[-100, -100, Z_BACK + TAB_DEPTH], [100, 100, 100]])
    assert trimesh.boolean.intersection([new, in_front], engine="manifold").volume == pytest.approx(trimesh.boolean.intersection([flat, in_front], engine="manifold").volume, rel=1e-6)


def test_accent_is_the_slot_digit_and_hint():
    new, ref = _mesh("dock_fingers_slot1_accent.stl"), _mesh("dock_integrated_slot1_accent.stl")
    assert new.volume == pytest.approx(ref.volume, rel=1e-3)
    assert new.bounds == pytest.approx(ref.bounds, abs=1e-3)


def test_nothing_of_the_dock_reaches_behind_the_panel_plane():
    """So the only things that can meet the fingers are the back plate and the tab: no funnel, channel, pocket, stop or post is behind z_back."""
    assert _flat_dock(1).bounds[0][2] == pytest.approx(Z_BACK, abs=1e-4)
    fingers = trimesh.creation.box(bounds=[[-100, -100, -100], [100, 100, Z_BACK - 1e-3]])
    assert _overlap(_flat_dock(1), fingers) == pytest.approx(0, abs=1e-6)


def test_back_plate_covers_the_tab_and_the_bore():
    flat = _flat_dock(1)
    xs = [side for _, side in M.FINGER_OUTLINE]
    tab = trimesh.creation.box(bounds=[[min(xs), -M.FINGER_HEIGHT / 2, Z_BACK], [max(xs), M.FINGER_HEIGHT / 2, Z_BACK + TAB_DEPTH]])
    assert _overlap(flat, tab) == pytest.approx(tab.volume, rel=1e-6)  # the plate is solid across the whole tab, so the fingers fuse to it
    # the bore's whole disc, just inside the plate's back face, is dock
    r, a = np.meshgrid(np.linspace(0, BORE_RADIUS, 12), np.linspace(0, 2 * np.pi, 48, endpoint=False))
    disc = np.c_[(r * np.cos(a)).ravel(), (r * np.sin(a)).ravel(), np.full(r.size, Z_BACK + 0.05)]
    assert flat.contains(disc).all()
    # and it stays at least DOCK_FLOOR minus the funnel's back bevel thick there (the bore's top edge reaches the funnel's start)
    top = np.array([[0.0, BORE_RADIUS, Z_BACK + M.DOCK_FLOOR - M.DOCK_FUNNEL_BACK_DEPTH - 0.05]])
    assert flat.contains(top).all()


def test_fingers_fit_inside_the_bore():
    """Every point of the outline in front of the tab, at the fingers' full height, is inside the socket bore (the tab is the part that lives in the plate)."""
    reach = max(np.hypot(side, M.FINGER_HEIGHT / 2) for depth, side in M.FINGER_OUTLINE if depth > 0.01)
    assert reach < BORE_RADIUS
    assert max(abs(side) for depth, side in M.FINGER_OUTLINE if depth <= 0.01) > BORE_RADIUS  # the tab is wider than the bore, so it sits on the panel face


def test_sticker_centre_is_on_the_socket_axis():
    """The chip frame's origin is the sticker's centre and the fingers are centred on it: x = 0 and y = 0 (the fingers' axis), where a spool's centre would be."""
    assert M.STICKER_CENTRE_Y == 0.0
    body = trimesh.boolean.intersection([_part(), trimesh.creation.box(bounds=[[-100, -100, -100], [100, 100, Z_BACK - 0.5]])], engine="manifold")
    assert (body.bounds[0][1] + body.bounds[1][1]) / 2 == pytest.approx(0, abs=1e-3)
    assert body.bounds[1][1] - body.bounds[0][1] == pytest.approx(M.FINGER_HEIGHT, abs=1e-3)
    assert (body.bounds[0][0] + body.bounds[1][0]) / 2 == pytest.approx(0, abs=0.05)
    pocket = M.POCKET_DIAMETER / 2  # the chip's recess is centred on the chip frame's origin
    assert pocket > 0
    chip = _mesh(f"{M.CHIP_FILE_PREFIX}PETG.stl")
    section = chip.section(plane_origin=[0, 0, M.POCKET_DEPTH / 2], plane_normal=[0, 0, 1])
    circle = min(section.discrete, key=lambda p: abs(np.ptp(p[:, 0]) - M.POCKET_DIAMETER))  # the recess's outline, not the chip's
    assert np.ptp(circle[:, 0]) == pytest.approx(M.POCKET_DIAMETER, abs=0.05)
    assert (circle[:, :2].min(axis=0) + circle[:, :2].max(axis=0)) / 2 == pytest.approx([0, 0], abs=0.05)


def test_sticker_is_close_to_the_panel_plane():
    """The chip's back face is DOCK_BACK_GAP + DOCK_FLOOR from the panel plane; the sticker, in a POCKET_DEPTH recess, is at most that plus the recess depth."""
    assert -Z_BACK == pytest.approx(M.DOCK_BACK_GAP + M.DOCK_FLOOR)
    assert -Z_BACK + M.POCKET_DEPTH == pytest.approx(2.1)


def test_finger_section_matches_the_traced_outline():
    """A slice through the fingers' mid-height behind the panel plane is the traced outline, spread by FINGER_SPREAD, mapped as depth into -Z and sideways into X, no mirror."""
    section = _part().section(plane_origin=[0, 0.37, 0], plane_normal=[0, 1, 0])
    area = shapely.Polygon()
    for loop in section.discrete:
        area = area.symmetric_difference(shapely.Polygon(loop[:, [0, 2]]))
    behind = area.intersection(shapely.box(-100, -100, 100, Z_BACK))
    expected = shapely.Polygon([(side, Z_BACK - depth) for depth, side in spread_outline(FINGER_SPREAD)]).intersection(shapely.box(-100, -100, 100, Z_BACK))
    assert expected.area > 100
    assert behind.symmetric_difference(expected).area < 0.005 * expected.area


def _traced_part() -> trimesh.Trimesh:
    """The finger dock built with spread 0, so the traced fingers themselves can be compared with his."""
    path = Path(ROOT / "u1" / "out" / "_traced_dock_fingers.stl")
    export_stl(M.dock_fingers_parts(1, spread=0)["dock"], str(path))
    mesh = trimesh.load(path, force="mesh")
    path.unlink()
    return mesh


def test_fingers_match_remmulegguh():
    """Independent check: the fingers built with spread 0, in the dock frame, coincide with his holder's fingers within 2% by volume."""
    src = ROOT / "thingiverse" / "printables1625982" / "holderrfid_short.stl"
    if not src.exists():
        pytest.skip("remmulegguh's holderrfid_short.stl is not present (it is not redistributed)")
    his = trimesh.load(src, force="mesh")
    his.apply_translation([0, -219.3, 6.5])  # his socket axis to the origin
    plate_back = 179.15
    R = np.array([[0, 1, 0], [0, 0, -1], [-1, 0, 0]], float)  # his frame to ours: sideways y -> X, down +z -> -Y, depth x -> -Z; a proper rotation
    assert np.linalg.det(R) == pytest.approx(1.0)
    his.vertices = his.vertices @ R.T + [0, 0, Z_BACK + plate_back]
    probe = trimesh.creation.box(extents=[40, 20, 29])
    probe.apply_translation([0, 0, Z_BACK - 15.5])
    ours = trimesh.boolean.intersection([_traced_part(), probe], engine="manifold")
    theirs = trimesh.boolean.intersection([his, probe], engine="manifold")
    shared = trimesh.boolean.intersection([ours, theirs], engine="manifold")
    assert theirs.volume > 100
    assert shared.volume == pytest.approx(theirs.volume, rel=0.02)
    assert shared.volume == pytest.approx(ours.volume, rel=0.02)


def test_standing_on_its_bottom_stop_only_the_fingers_underside_needs_support():
    """As laid out in the 3MF (ON_BOTTOM_STOP): the fingers' own overhang is what needs support, and the dock's own overhang is the plain dock's."""
    assert np.allclose(FINGERS_PARTS[0][3], ON_BOTTOM_STOP) and np.isclose(np.linalg.det(ON_BOTTOM_STOP), 1.0)
    mesh = _part()
    behind = mesh.triangles_center[:, 2] < Z_BACK - 1e-6
    mesh.vertices = mesh.vertices @ ON_BOTTOM_STOP.T
    mesh.apply_translation([0, 0, -mesh.bounds[0][2]])
    over = (mesh.face_normals[:, 2] < -OVERHANG_LIMIT) & (mesh.triangles_center[:, 2] > BED_CONTACT)
    assert mesh.area_faces[over & ~behind].sum() < 25
    assert mesh.area_faces[over & behind].sum() > 100
