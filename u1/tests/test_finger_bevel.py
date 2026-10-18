"""Checks for the release bevel on the snap fingers' hooks (u1/docs/FINGER_SPREAD.md, issue 9). The bevel is dropped by default (FINGER_BEVEL = 0); these keep the machinery covered by passing a bevel explicitly.

What these prove: where the bevel is, which corners it is on, that it leads when the part turns counter-clockwise (computed from the mesh's own coordinates), that it is symmetric under a half turn
about the socket axis, that the mid-height section is untouched, and how much material it removes. They cannot prove that it helps a real hook pop out of a real socket, or what PETG does there.
"""
import tempfile
from pathlib import Path

import numpy as np
import pytest
import shapely
import trimesh
from build123d import export_stl

from u1_model import M, ROOT  # noqa: F401

import socket_fingers as F  # noqa: E402
from print_orientation import OVERHANG_LIMIT, UPSIDE_DOWN  # noqa: E402
from print_plates import BED_CONTACT, ON_BOTTOM_STOP  # noqa: E402

BEVEL = 1.5  # the value that was tried (Charles dropped the bevel, FINGER_BEVEL = 0); the tests pass it explicitly so the machinery stays covered
AXIS_Y, Z_BACK = 0.0, 0.0  # a bare finger piece on a socket axis through the origin, panel face at z=0


def _mesh(shape) -> trimesh.Trimesh:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "p.stl"
        export_stl(shape, str(path))
        return trimesh.load(path, force="mesh")


def _fingers(bevel: float, spread: float = F.FINGER_SPREAD, monkeypatch=None) -> trimesh.Trimesh:
    monkeypatch.setattr(F, "FINGER_BEVEL", bevel)
    return _mesh(M._socket_fingers(AXIS_Y, Z_BACK, spread))


def _bevel_faces(m: trimesh.Trimesh) -> np.ndarray:
    """Indices of faces whose normal is at 45 degrees between the end faces (+-Y) and the retaining step's normal (+Z, toward the panel), flat across X."""
    n = m.face_normals
    return np.flatnonzero((np.abs(n[:, 0]) < 1e-6) & (np.abs(np.abs(n[:, 1]) - np.sqrt(0.5)) < 1e-6) & (n[:, 2] > 0.7))


def test_the_constants_are_what_the_docs_say(monkeypatch):
    assert F.FINGER_BEVEL == 0.0 and F.FINGER_SPREAD == 2.0  # the bevel is dropped by default
    _, inner, outer = F.hook_step(0.0)
    assert (inner, outer) == (9.709, 10.796) and F.hook_step()[1:] == pytest.approx((9.709 + 2.0, 10.796 + 2.0))
    assert F.bevel_leg() == 0
    monkeypatch.setattr(F, "FINGER_BEVEL", BEVEL)
    assert F.bevel_leg() == pytest.approx(1.087)  # clipped to the retaining step, which is lower than the tried 1.5


def test_default_fingers_carry_no_bevel_anywhere():
    assert M._hook_bevel_cutters(AXIS_Y, Z_BACK, F.FINGER_SPREAD) is None
    assert len(_bevel_faces(_mesh(M._socket_fingers(AXIS_Y, Z_BACK)))) == 0
    assert len(_bevel_faces(_mesh(M.cover_parts(2)["cover"]))) == 0


def test_leg_is_clipped_to_the_step_and_the_finger_height(monkeypatch):
    monkeypatch.setattr(F, "FINGER_BEVEL", 0.5)
    assert F.bevel_leg() == 0.5
    monkeypatch.setattr(F, "FINGER_BEVEL", 99.0)
    assert F.bevel_leg() == pytest.approx(1.087) and F.bevel_leg() <= F.FINGER_HEIGHT
    monkeypatch.setattr(F, "FINGER_BEVEL", 0.0)
    assert F.bevel_leg() == 0 and M._hook_bevel_cutters(AXIS_Y, Z_BACK, 2.0) is None


def test_bevel_is_on_the_two_leading_corners_only(monkeypatch):
    m = _fingers(BEVEL, monkeypatch=monkeypatch)
    faces = _bevel_faces(m)
    centres = m.triangles_center[faces]
    corners = {(int(np.sign(c[0])), int(np.sign(c[1]))) for c in centres}
    assert corners == {(1, 1), (-1, -1)}  # +X hook's top end and -X hook's bottom end; (1, -1) and (-1, 1) are the unbevelled mirror pair
    for c, n in zip(centres, m.face_normals[faces]):
        assert np.sign(n[1]) == np.sign(c[1])  # the bevel faces outward along the end it is on
        assert F.FINGER_HEIGHT / 2 - F.bevel_leg() - 1e-6 <= abs(c[1]) <= F.FINGER_HEIGHT / 2  # within one leg of the end face
        assert Z_BACK - F.HOOK_REAR_DEPTH - F.bevel_leg() < c[2] < Z_BACK - F.HOOK_REAR_DEPTH  # beside the step, one leg deep at most
    plain = _fingers(0.0, monkeypatch=monkeypatch)
    assert len(_bevel_faces(plain)) == 0


def test_the_bevelled_corners_lead_when_turned_counter_clockwise_seen_from_the_front(monkeypatch):
    """From the coordinates alone: the viewer is on +Z (the fingers go to -Z, into the printer); with X to the right and Y up, X cross Y is +Z toward the viewer, so counter-clockwise is the positive rotation about +Z.

    A point at p turning by +delta moves along (-p_y, p_x). A face leads when that motion has a positive component along its outward normal.
    """
    m = _fingers(BEVEL, monkeypatch=monkeypatch)
    assert m.bounds[0][2] < -29 and m.bounds[1][2] < 1  # the fingers lie behind the panel (-Z), so the front, where the viewer is, is +Z
    assert np.cross([1, 0, 0], [0, 1, 0]) @ [0, 0, 1] > 0  # X right, Y up: Z toward the viewer
    delta = 1e-3
    rot = np.array([[np.cos(delta), -np.sin(delta)], [np.sin(delta), np.cos(delta)]])  # counter-clockwise for a viewer on +Z
    assert rot @ [1.0, 0.0] == pytest.approx([np.cos(delta), np.sin(delta)])  # +X moves toward +Y
    faces = _bevel_faces(m)
    assert len(faces) > 0
    for c, n in zip(m.triangles_center[faces], m.face_normals[faces]):
        moved = rot @ c[:2] - c[:2]
        assert moved @ n[:2] > 0  # leads
    # the mirror pair's end faces (the unbevelled corners) trail
    for sign_x, sign_y in ((1, -1), (-1, 1)):
        c = np.array([sign_x * 11.5, sign_y * F.FINGER_HEIGHT / 2])
        assert (rot @ c - c) @ [0, sign_y] < 0


def test_bevel_is_symmetric_under_a_half_turn_about_the_socket_axis(monkeypatch):
    m = _fingers(BEVEL, monkeypatch=monkeypatch)
    centres = m.triangles_center[_bevel_faces(m)]
    turned = centres * [-1, -1, 1]  # 180 degrees about the axis (the Z line through the origin)
    # the traced hooks differ by 0.02 mm side to side, so match within 0.05
    for t in turned:
        assert np.linalg.norm(centres - t, axis=1).min() < 0.05
    assert len(centres) % 2 == 0


def test_mid_height_section_is_the_spread_outline(monkeypatch):
    m = _fingers(BEVEL, monkeypatch=monkeypatch)
    section = m.section(plane_origin=[0, 0, 0], plane_normal=[0, 1, 0])
    area = shapely.Polygon()
    for loop in section.discrete:
        area = area.symmetric_difference(shapely.Polygon(loop[:, [0, 2]]))
    expected = shapely.Polygon([(side, Z_BACK - depth) for depth, side in F.spread_outline(F.FINGER_SPREAD)])
    assert expected.area > 100
    assert area.symmetric_difference(expected).area < 1e-3
    assert m.bounds[0][1] == pytest.approx(-F.FINGER_HEIGHT / 2) and m.bounds[1][1] == pytest.approx(F.FINGER_HEIGHT / 2)  # the height is untouched


def _expected_removed_volume(spread: float) -> float:
    """The two wedges' volume from the outline alone: per side, the integral over the sideways coordinate of the triangle's area where hook material lies behind the step."""
    leg = F.bevel_leg(spread)
    outline = F.spread_outline(spread)
    total = 0.0
    for sign in (1, -1):
        poly = shapely.Polygon([(depth, sign * side) for depth, side in outline])
        _, inner, outer = F.hook_step(spread)
        xs = np.linspace(inner, F.hook_half_width(spread), 4001)
        areas = []
        for x in xs:
            cut = poly.intersection(shapely.LineString([(F.HOOK_REAR_DEPTH - 1e-9, x), (F.HOOK_REAR_DEPTH + 10, x)]))
            if cut.is_empty:
                areas.append(0.0)
                continue
            first = shapely.get_coordinates(cut)[:, 0].min()
            t = max(0.0, first - F.HOOK_REAR_DEPTH)
            areas.append(0.5 * max(0.0, leg - t) ** 2)
        total += float(np.trapezoid(areas, xs))
    return total


def test_removed_volume_matches_the_chamfer_geometry(monkeypatch):
    plain = _fingers(0.0, monkeypatch=monkeypatch)
    bevelled = _fingers(BEVEL, monkeypatch=monkeypatch)
    removed = plain.volume - bevelled.volume
    expected = _expected_removed_volume(F.FINGER_SPREAD)
    assert expected > 1.0
    assert removed == pytest.approx(expected, rel=0.03)
    # and nothing else changed: the bevelled part lies inside the plain one
    inter = trimesh.boolean.intersection([plain, bevelled], engine="manifold")
    assert inter.volume == pytest.approx(bevelled.volume, rel=1e-6)


def _overhang_area(mesh: trimesh.Trimesh, rotation: np.ndarray) -> float:
    m = mesh.copy()
    m.vertices = m.vertices @ rotation.T
    m.apply_translation([0, 0, -m.bounds[0][2]])
    over = (m.face_normals[:, 2] < -OVERHANG_LIMIT) & (m.triangles_center[:, 2] > BED_CONTACT)
    return float(m.area_faces[over].sum())


@pytest.mark.parametrize("name,build,rotation", [
    ("socket adapter", lambda: M.socket_adapter_parts()["socket_adapter"], UPSIDE_DOWN),
    ("blank cover", lambda: M.cover_parts(2)["cover"], UPSIDE_DOWN),
    ("dock with fingers", lambda: M.dock_fingers_parts(1)["dock"], ON_BOTTOM_STOP),
])
def test_bevel_if_restored_adds_no_overhang_in_the_print_orientations(monkeypatch, name, build, rotation):
    """If the bevel is restored, its faces are at exactly 45 degrees, which the rule does not count (it counts steeper); the area needing support must not grow."""
    monkeypatch.setattr(F, "FINGER_BEVEL", 0.0)
    before = _overhang_area(_mesh(build()), rotation)
    monkeypatch.setattr(F, "FINGER_BEVEL", BEVEL)
    after = _overhang_area(_mesh(build()), rotation)
    assert after <= before + 1e-6
