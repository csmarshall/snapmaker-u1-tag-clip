"""Checks for the integrated dock (the dock with the adapter's dovetail built in; u1/docs/INTEGRATED_DOCK.md).

Run the build first. These compare the part with numbers from the same script (and, where his base is present, with 1waynger1's real slot), so passing means the file agrees
with its own parameters and the slot as measured, not that it fits a printed adapter.
"""

import numpy as np
import pytest
import shapely
import trimesh

from build123d import export_stl  # noqa: E402
from test_u1_fit import ADAPTER_MESHES, _his_hub_base  # noqa: E402
from u1_model import M, _mesh, _overlap  # noqa: E402

from print_orientation import OVERHANG_LIMIT  # noqa: E402
from print_plates import BED_CONTACT, INTEGRATED_PARTS, ON_SIDE  # noqa: E402

D = M._dock_extents()
F = M._adapter_frame("socket")
BELOW_THE_DOCK = trimesh.creation.box(bounds=[[-100, -200, -100], [100, D["y_bottom"], 100]])  # everything under the dock's bottom end
ABOVE_THE_STEM = trimesh.creation.box(bounds=[[-100, D["y_bottom"], -100], [100, 200, 100]])


def _part(slot: int = 1) -> trimesh.Trimesh:
    return _mesh(f"dock_integrated_slot{slot}.stl")


def _groove_free_dock(slot: int, tmp_path) -> trimesh.Trimesh:
    """dock_parts(slot, mount_grooves=False) built here and exported, the dock the integrated part must contain."""
    path = tmp_path / f"dock_slot{slot}_flat.stl"
    export_stl(M.dock_parts(slot, mount_grooves=False)["dock"], str(path))
    return trimesh.load(path, force="mesh")


@pytest.mark.parametrize("slot", M.U1_SLOTS)
def test_integrated_dock_minus_the_stem_is_the_dock_without_grooves(slot, tmp_path):
    """Above the dock's bottom end the integrated part is the existing dock minus only its mount grooves: same volume as the groove-free build, and the two overlap completely."""
    new, flat = _part(slot), _groove_free_dock(slot, tmp_path)
    assert new.is_watertight
    body = trimesh.boolean.intersection([new, ABOVE_THE_STEM], engine="manifold")
    assert body.volume == pytest.approx(flat.volume, rel=1e-6)
    assert _overlap(body, flat) == pytest.approx(flat.volume, rel=1e-6)
    old = _mesh(f"dock_slot{slot}.stl")
    assert _overlap(body, old) == pytest.approx(old.volume, rel=1e-6)  # the existing dock lies wholly inside it: the grooves are the only difference


def test_integrated_dock_has_flat_side_faces_and_the_default_dock_keeps_its_grooves():
    d = M._dock_extents()
    gy0, gy1 = d["groove_y"]
    gz0, gz1 = d["groove_z"]
    probe = trimesh.creation.box(bounds=[[d["outer_half"] - M.MOUNT_GROOVE_DEPTH / 2 - 0.01, gy0, gz0], [d["outer_half"] - M.MOUNT_GROOVE_DEPTH / 2 + 0.01, gy1, gz1]])
    groove_volume = probe.volume
    assert _overlap(_part(), probe) == pytest.approx(groove_volume, rel=1e-2)  # (STL is float32) solid where the groove would be
    assert _overlap(_mesh("dock_slot1.stl"), probe) == pytest.approx(0, abs=1e-6)  # the default dock is cut there
    assert M.dock_parts(1)["dock"].volume < M.dock_parts(1, mount_grooves=False)["dock"].volume
    ys = _part().section(plane_origin=[0, (gy0 + gy1) / 2, 0], plane_normal=[0, 1, 0]).bounds
    assert ys[1][0] == pytest.approx(d["outer_half"], abs=1e-3)  # the band's side face is at full width


def test_stem_is_all_below_the_dock_and_adds_only_the_stem(tmp_path):
    new, old = _part(), _groove_free_dock(1, tmp_path)
    stem = trimesh.boolean.intersection([new, BELOW_THE_DOCK], engine="manifold")
    assert stem.volume == pytest.approx(new.volume - old.volume, rel=1e-6)
    assert stem.bounds[0][1] == pytest.approx(F["y_top"] - M.MOUNT_TONGUE_LENGTH, abs=1e-3)
    assert new.bounds[1] == pytest.approx(old.bounds[1], abs=1e-4)  # nothing added above, in front or beside the dock


def test_accent_is_the_existing_slot_digit_and_hint():
    new, old = _mesh("dock_integrated_slot1_accent.stl"), _mesh("dock_slot1_accent.stl")
    assert new.volume == pytest.approx(old.volume, rel=1e-3)
    assert new.bounds == pytest.approx(old.bounds, abs=1e-3)


def test_sticker_centre_is_where_it_is_on_the_mount():
    """Seated, the stem's underside is the adapter's top edge, so the sticker is 28.6 mm above the socket axis on our adapter, as with the dock mount."""
    stem = trimesh.boolean.intersection([_part(), BELOW_THE_DOCK], engine="manifold")
    underside = stem.vertices[:, 1][np.isclose(stem.vertices[:, 1], F["y_top"], atol=1e-3)]
    assert len(underside) > 0
    assert M.sticker_above_axis("socket") == pytest.approx(28.6, abs=0.05)
    assert F["y_top"] - M.SOCKET_ADAPTER_TOP_ABOVE_AXIS == pytest.approx(-28.6, abs=0.05)  # the sticker centre is the dock frame's origin
    assert D["y_bottom"] - F["y_top"] == pytest.approx(M.FIT_CLEARANCE + M.MOUNT_RISER)  # the gap the mount's crossbar fills, so the dock sits where it does on the mount


def test_back_plate_stays_where_it_was_and_nothing_goes_behind_the_panel():
    new, old = _part(), _mesh("dock_slot1.stl")
    assert new.bounds[0][2] == pytest.approx(old.bounds[0][2], abs=1e-4) == pytest.approx(F["z_back"], abs=1e-4)
    assert D["z_back"] == pytest.approx(-(M.DOCK_BACK_GAP + M.DOCK_FLOOR))
    assert new.bounds[1][2] == pytest.approx(old.bounds[1][2], abs=1e-4)
    stem = trimesh.boolean.intersection([new, trimesh.creation.box(bounds=[[-100, -200, -100], [100, D["y_bottom"] - 0.01, 100]])], engine="manifold")  # clear of the dock's own bottom face
    assert stem.bounds[0][2] >= F["z_back"] - 1e-4 and stem.bounds[1][2] <= F["z_front"] + 1e-4  # inside the adapter plate's thickness


def test_tongue_section_is_the_slot_section_less_the_fit_clearance():
    """A slice through the tongue, well below the shoulder, against the slot polygon from the measured profile eroded by FIT_CLEARANCE with mitred corners."""
    mesh = _part()
    section = mesh.section(plane_origin=[0, F["y_top"] - 15, 0], plane_normal=[0, 1, 0])
    assert len(section.discrete) == 1
    got = shapely.Polygon(section.discrete[0][:, [0, 2]])  # X and Z of the slice, which lies in the plane y = const
    half = [(w, F["z_front"] - depth) for w, depth in M.ADAPTER_SLOT_PROFILE]
    slot = shapely.Polygon([(-w, z) for w, z in half] + [(w, z) for w, z in reversed(half)])
    expected = slot.buffer(-M.FIT_CLEARANCE, join_style="mitre", mitre_limit=10)
    assert got.symmetric_difference(expected).area < 0.01 * expected.area
    assert got.area == pytest.approx(M._slot_section(M.FIT_CLEARANCE).area, rel=1e-3)
    assert got.area < slot.area


def _lowered_clean(base: trimesh.Trimesh) -> None:
    dock = _part()
    for dy in np.arange(35.0, -0.01, -1.0):
        moved = dock.copy()
        moved.apply_translation([0, dy, 0])
        assert _overlap(moved, base) == pytest.approx(0, abs=1e-3), f"touches at {dy} mm above its seat"


@pytest.mark.parametrize("adapter", M.ADAPTERS)
def test_dovetail_slides_into_the_adapter_slot(adapter):
    """Lowered straight down from 35 mm above onto either adapter (the hub one is a stand-in drawn from the same numbers), it never interferes, and it arrives with the shoulder on the top edge."""
    _lowered_clean(_mesh(ADAPTER_MESHES[adapter]))


def test_dovetail_slides_into_his_real_slot():
    """Independent of our numbers: the same, against 1waynger1's actual adapter mesh when it is present."""
    _lowered_clean(_his_hub_base())


@pytest.mark.parametrize("shift", [(0, -0.5, 0), (0.5, 0, 0), (-0.5, 0, 0), (0, 0, 0.5)])
@pytest.mark.parametrize("adapter", M.ADAPTERS)
def test_dock_is_held_by_the_adapter(adapter, shift):
    """Seated, it cannot drop (the shoulder is on the top edge), move sideways or come away from the panel (the dovetail)."""
    moved = _part()
    moved.apply_translation(shift)
    assert _overlap(moved, _mesh(ADAPTER_MESHES[adapter])) > 0.01


def test_dock_lifts_straight_out_so_it_is_only_held_by_gravity():
    """No detent is built in: moving up frees it. This pins the claim in the docs, so adding a detent has to change both."""
    moved = _part()
    moved.apply_translation([0, 0.01, 0])
    assert _overlap(moved, _mesh("socket_adapter.stl")) == pytest.approx(0, abs=1e-3)


def test_printed_on_its_side_the_stem_needs_almost_no_support():
    """As laid out in the one-plate 3MF (ON_SIDE), the faces the stem and tongue add that face down more steeply than 45 degrees amount to a few mm2."""
    (_, _, _, rotation, files) = INTEGRATED_PARTS[0]
    assert np.isclose(np.linalg.det(rotation), 1.0) and np.allclose(rotation, ON_SIDE)
    mesh = _part()
    centres_before = mesh.triangles_center
    mesh.vertices = mesh.vertices @ rotation.T
    mesh.apply_translation([0, 0, -mesh.bounds[0][2]])
    over = (mesh.face_normals[:, 2] < -OVERHANG_LIMIT) & (mesh.triangles_center[:, 2] > BED_CONTACT)
    in_stem = centres_before[:, 1] <= D["y_bottom"] + 1e-6
    assert mesh.area_faces[over & in_stem].sum() < 15
