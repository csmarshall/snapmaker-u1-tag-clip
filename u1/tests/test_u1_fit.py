"""Fit and consistency checks for the U1-specific parts built by u1/u1_parts.py: dock mount, socket adapter, blank cover and 1waynger1's hub adapter.

Run both builds first (chip/chip_clip.py, u1/u1_build.py). As in tests/test_fit.py, most checks compare the parts with numbers from the same script, so passing means the
files agree with their own parameters, not that anything fits a real printer.
"""
import numpy as np
import pytest
import shapely
import trimesh
from build123d import export_stl

from u1_model import CHIP_OUT, M, ROOT, U1_OUT, _mesh, _overlap  # noqa: F401

OUT = U1_OUT

HUB_BASE = ROOT / "thingiverse" / "makerworld2152529_hub" / "1.stl"  # 1waynger1's "Machine Interface", split out of tst.3mf; not redistributed
ADAPTER_MESHES = {"socket": "socket_adapter.stl", "hub": "hub_adapter_standin.stl"}


@pytest.mark.parametrize("adapter", M.ADAPTERS)
def test_chip_slides_in_from_above_past_the_mount(adapter):
    chip = _mesh(f"{M.CHIP_FILE_PREFIX}PETG.stl")
    rest = trimesh.util.concatenate([_mesh("dock_slot3.stl"), _mesh("dock_mount.stl"), _mesh(ADAPTER_MESHES[adapter])])
    worst = 0.0
    for dy in np.arange(45.0, -0.01, -0.5):
        moved = chip.copy()
        moved.apply_translation([0, dy, 0])
        worst = max(worst, _overlap(moved, rest))
    assert worst == pytest.approx(0, abs=1e-3)


def test_mount_holds_the_dock_without_touching_it():
    mount, dock = _mesh("dock_mount.stl"), _mesh("dock_slot3.stl")
    assert mount.is_watertight
    assert _overlap(mount, dock) == pytest.approx(0, abs=0.01)


@pytest.mark.parametrize("shift", [(0, 1.0, 0), (0, -1.0, 0), (0, 0, 1.0)])
def test_clamps_lock_the_dock_up_down_and_away_from_the_panel(shift):
    """Seated, the dock cannot move 1mm up, down or out from the panel without running into the clamps (sideways is the other arm's job)."""
    mount, dock = _mesh("dock_mount.stl"), _mesh("dock_slot3.stl")
    dock.apply_translation(shift)
    assert _overlap(mount, dock) > 0.05


def test_grip_band_is_centred_and_matches_the_pocket():
    """The band is what is left of the dock's length once the lower pocket's height comes off both ends, centred on the dock."""
    d = M._dock_extents()
    pocket = d["cover_top"] - d["y_bottom"]
    y0, y1 = d["band"]
    assert y1 - y0 == pytest.approx((d["y_rim"] - d["y_bottom"]) - 2 * pocket)
    assert (y0 + y1) / 2 == pytest.approx(d["y_mid"])
    g0, g1 = d["groove_y"]
    assert (g0 + g1) / 2 == pytest.approx(d["y_mid"])


def test_dock_pushes_into_the_mount_from_the_front_past_the_clamps_only():
    """Pushed straight in toward the panel, the dock only ever meets the jaws and tongues in its middle band, which the arms flex outward to pass."""
    mount, dock = _mesh("dock_mount.stl"), _mesh("dock_slot3.stl")
    d = M._dock_extents()
    engage = max(M.MOUNT_JAW_REACH, M.MOUNT_GROOVE_DEPTH - M.FIT_CLEARANCE)
    touched = False
    for dz in np.arange(12.0, 0.01, -0.25):
        moved = dock.copy()
        moved.apply_translation([0, 0, dz])
        inter = trimesh.boolean.intersection([moved, mount], engine="manifold")
        if len(inter.vertices) and inter.volume > 1e-3:
            touched = True
            assert np.abs(inter.vertices[:, 0]).min() >= d["outer_half"] - engage - 0.05
            assert d["band"][0] - 0.05 <= inter.vertices[:, 1].min() and inter.vertices[:, 1].max() <= d["band"][1] + 0.05
    assert touched  # the clamps do catch it: that is the snap


def _slides_in_clean(base: trimesh.Trimesh) -> None:
    mount = _mesh("dock_mount.stl")
    for dy in np.arange(35.0, -0.01, -0.5):
        moved = mount.copy()
        moved.apply_translation([0, dy, 0])
        assert _overlap(moved, base) == pytest.approx(0, abs=1e-3), f"touches at {dy} mm above its seat"


def _held_by(base: trimesh.Trimesh, shift) -> None:
    mount = _mesh("dock_mount.stl")
    mount.apply_translation(shift)
    assert _overlap(mount, base) > 0.01


HELD_SHIFTS = [(0, -0.5, 0), (0.5, 0, 0), (-0.5, 0, 0), (0, 0, 0.5)]  # cannot drop (crossbar on the top edge) or move sideways or out (dovetail)


def test_mount_slides_into_our_socket_adapter():
    adapter = _mesh("socket_adapter.stl")
    assert adapter.is_watertight
    _slides_in_clean(adapter)


@pytest.mark.parametrize("shift", HELD_SHIFTS)
def test_mount_is_held_by_our_socket_adapter(shift):
    _held_by(_mesh("socket_adapter.stl"), shift)


def _finger_top(m: trimesh.Trimesh) -> float:
    """The highest point of the snap fingers (everything behind the panel face)."""
    return m.vertices[(m.vertices[:, 2] < -M.DOCK_BACK_GAP - M.DOCK_FLOOR - 0.5)][:, 1].max()


def test_socket_adapter_stands_on_one_flat_face_for_printing():
    """Standing on its top: the plate's flat top and the fingers' top face are the highest points, level with each other."""
    top = M._adapter_frame("socket")["axis_y"] + M.SOCKET_PLATE_FLAT
    m = _mesh("socket_adapter.stl")
    assert m.bounds[1][1] == pytest.approx(top, abs=0.02)
    assert _finger_top(m) == pytest.approx(top, abs=0.02)


def test_cover_stands_on_its_flat_top_with_fingers_below_it():
    """The cover's flat top is its highest point (it prints standing on it); the fingers stop SOCKET_PLATE_FLAT above the axis, so they print on supports."""
    axis_y = M._adapter_frame("socket")["axis_y"]
    m = _mesh("cover_slot3.stl")
    assert m.bounds[1][1] == pytest.approx(axis_y + M.SOCKET_COVER_FLAT, abs=0.02)
    assert _finger_top(m) == pytest.approx(axis_y + M.SOCKET_PLATE_FLAT, abs=0.02)


def test_cover_plate_hides_his_plug_outline():
    """Independent check: 1waynger1's plug, where it meets the panel (the best stand-in we have for the socket bore), lies wholly inside the cover's plate, seen from the front."""
    his = _his_hub_base()
    shift = M._adapter_frame("socket")["axis_y"] - M._adapter_frame("hub")["axis_y"]
    z_back = M._adapter_frame("socket")["z_back"]
    plug = his.section(plane_origin=[0, 0, z_back - 0.3], plane_normal=[0, 0, 1])
    bore = shapely.unary_union([shapely.Polygon(e[:, :2] + [0, shift]) for e in plug.discrete]).convex_hull
    plate = _mesh("cover_slot3.stl").section(plane_origin=[0, 0, z_back + 0.1], plane_normal=[0, 0, 1])
    face = shapely.unary_union([shapely.Polygon(e[:, :2]) for e in plate.discrete]).convex_hull
    assert bore.area > 500  # the plug's outside, not just its screw hole
    assert face.contains(bore)
    assert face.exterior.distance(bore) > M.SOCKET_COVER_OVERLAP - 0.5


def test_cover_parts_are_watertight_and_disjoint():
    cover, accent = _mesh("cover_slot3.stl"), _mesh("cover_slot3_accent.stl")
    assert cover.is_watertight and accent.is_watertight
    assert _overlap(cover, accent) == pytest.approx(0, abs=0.01)


def _traced_piece(piece: str) -> trimesh.Trimesh:
    """A socket piece built with spread 0, so its fingers are the traced ones (the built files carry FINGER_SPREAD)."""
    axis_y, z_back = M._adapter_frame("socket")["axis_y"], M._adapter_frame("socket")["z_back"]
    shape = M.cover_parts(3, spread=0)["cover"] if piece.startswith("cover") else M._adapter_plate("socket") + M._socket_fingers(axis_y, z_back, 0)
    path = OUT / f"_traced_{piece}"
    OUT.mkdir(exist_ok=True)
    export_stl(shape, str(path))
    mesh = trimesh.load(path, force="mesh")
    path.unlink()
    return mesh


def _finger_volumes(mesh: trimesh.Trimesh) -> tuple[float, float, float]:
    """Independent check helper: the fingers of `mesh` against remmulegguh's, both in the dock frame, in the fingers' region (1-30mm deep, clear of the plates). Returns (his volume, our volume, shared volume)."""
    src = ROOT / "thingiverse" / "printables1625982" / "holderrfid_short.stl"
    if not src.exists():
        pytest.skip("remmulegguh's holderrfid_short.stl is not present (it is not redistributed)")
    his = trimesh.load(src, force="mesh")
    his.apply_translation([0, -219.3, 6.5])  # his socket axis to the origin
    plate_back = 179.15
    z_back, axis_y = -M.DOCK_BACK_GAP - M.DOCK_FLOOR, M._adapter_frame("socket")["axis_y"]
    # His frame to ours: sideways y -> X, down +z -> -Y, depth x -> -Z. A proper rotation: no mirror.
    R = np.array([[0, 1, 0], [0, 0, -1], [-1, 0, 0]], float)
    assert np.linalg.det(R) == pytest.approx(1.0)
    his.vertices = his.vertices @ R.T + [0, axis_y, z_back + plate_back]
    probe = trimesh.creation.box(extents=[40, 20, 29])
    probe.apply_translation([0, axis_y, z_back - 15.5])  # the fingers' region, 1-30mm deep, clear of the plates
    ours = trimesh.boolean.intersection([mesh, probe], engine="manifold")
    theirs = trimesh.boolean.intersection([his, probe], engine="manifold")
    shared = trimesh.boolean.intersection([ours, theirs], engine="manifold")
    return theirs.volume, ours.volume, shared.volume


@pytest.mark.parametrize("piece", ["socket_adapter.stl", "cover_slot3.stl"])
def test_socket_fingers_match_remmulegguh(piece):
    """Independent check: the fingers built with spread 0 (the traced ones), mapped into the dock frame, coincide with his holder's fingers within 2% by volume."""
    theirs, ours, shared = _finger_volumes(_traced_piece(piece))
    assert theirs > 100
    assert shared == pytest.approx(theirs, rel=0.02)
    assert shared == pytest.approx(ours, rel=0.02)


def _his_hub_base() -> trimesh.Trimesh:
    """1waynger1's hub adapter moved into the dock's frame: turned 180 degrees about X (plug into the panel, his y=0 end up), slot centred, back on the panel.

    The turn is a proper rotation (determinant +1). Which end is up is HUB_NEAR_END_UP; the plug-centre test checks the placement against his plug.
    """
    if not HUB_BASE.exists():
        pytest.skip("1waynger1's hub base is not present (it is not redistributed)")
    base = trimesh.load(HUB_BASE, force="mesh")
    base.apply_translation(-base.bounds[0])
    R = np.diag([1.0, -1.0, -1.0])
    assert np.linalg.det(R) == pytest.approx(1.0)
    f = M._adapter_frame("hub")
    if not M.HUB_NEAR_END_UP:
        base.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1], [M.ADAPTER_WIDTH / 2, M.ADAPTER_LENGTH / 2, 0]))
    base.vertices = base.vertices @ R.T + [-M.ADAPTER_WIDTH / 2, f["y_top"], f["z_front"]]
    return base


def test_hub_frame_puts_the_socket_axis_on_his_plug():
    """Independent check of the measured numbers: the centre of his plug's screw hole lands on the axis the model assumes."""
    base, f = _his_hub_base(), M._adapter_frame("hub")
    sec = base.section(plane_origin=[0, f["axis_y"], f["z_back"] - 5], plane_normal=[0, 0, 1])
    hole = sorted(sec.discrete, key=lambda e: np.ptp(e[:, 0]))[0]
    assert np.ptp(hole[:, 0]) < 4  # the screw hole, not the plug's outside
    assert hole[:, 0].mean() == pytest.approx(0, abs=0.1)
    assert (hole[:, 1].min() + hole[:, 1].max()) / 2 == pytest.approx(f["axis_y"], abs=0.1)


def test_mount_slides_into_his_hub_adapter():
    """Independent check: the mount's tongue, lowered from 35mm above into his real slot, never touches his adapter."""
    _slides_in_clean(_his_hub_base())


@pytest.mark.parametrize("shift", HELD_SHIFTS)
def test_mount_is_held_by_his_hub_adapter(shift):
    _held_by(_his_hub_base(), shift)


def _plate_region(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """The slotted plate of an adapter, away from its ends and plug: the part that has to match between his and ours."""
    f = M._adapter_frame("hub")
    probe = trimesh.creation.box(extents=[M.ADAPTER_WIDTH - 2 * M.ADAPTER_CORNER_RADIUS, 27, M.ADAPTER_THICKNESS - 0.02])
    probe.apply_translation([0, f["y_top"] - 4 - 13.5, f["z_back"] + M.ADAPTER_THICKNESS / 2])
    return trimesh.boolean.intersection([mesh, probe], engine="manifold")


@pytest.mark.parametrize("ours", ["socket_adapter.stl", "hub_adapter_standin.stl"])
def test_our_plates_match_his_slotted_plate(ours):
    """Independent check that our copy of his slot is his slot: over the plate's middle, ours and his coincide within 2% by volume."""
    his, mine = _plate_region(_his_hub_base()), _plate_region(_mesh(ours))
    shared = trimesh.boolean.intersection([his, mine], engine="manifold")
    assert his.volume > 1000
    assert shared.volume == pytest.approx(his.volume, rel=0.02)
    assert shared.volume == pytest.approx(mine.volume, rel=0.02)
