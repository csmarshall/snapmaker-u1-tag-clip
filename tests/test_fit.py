"""Fit and consistency checks for the chip and docks built by coin/u1_chip_clip.py.

Run the build first, then the tests (see README). Every check except test_clip_matches_extrutim compares the parts with numbers from the same script, so passing
means the files agree with their own parameters, not that anything fits a real printer or sticker.
"""
import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
import shapely
import trimesh
from build123d import export_stl

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "coin" / "out"
# Extrutim's Clip-Classic.stl from Printables 24371; not redistributed here, so the comparison skips when it is absent.
CLIP_CLASSIC = ROOT / "thingiverse" / "printables24371_clip" / "Clips" / "Clip-Classic.stl"
CLIP_CLASSIC_SHA256_PREFIX = "5cb545de106921d3"


def _load_model():
    """Import the build script as a module, for its constants."""
    sys.path.insert(0, str(ROOT / "coin"))  # the model imports its traced data (socket_fingers) from beside it
    spec = importlib.util.spec_from_file_location("u1_chip_clip", ROOT / "coin" / "u1_chip_clip.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


M = _load_model()
MATERIALS = tuple(M.file_stem(name) for name in M.FILAMENTS)


def _mesh(name: str) -> trimesh.Trimesh:
    path = OUT / name
    if not path.exists():
        pytest.skip(f"{path} missing: run the build first")
    return trimesh.load(path, force="mesh")


def _overlap(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    inter = trimesh.boolean.intersection([a, b], engine="manifold")
    return float(inter.volume) if len(inter.vertices) else 0.0


def _turned(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """The chip turned upside down in its own plane (round end first), the one wrong way it could still be pushed into the slot."""
    turned = mesh.copy()
    turned.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [0, 0, 1]))
    return turned


@pytest.mark.parametrize("slot", M.U1_SLOTS)
def test_dock_parts_are_watertight_and_disjoint(slot):
    dock = _mesh(f"dock_slot{slot}.stl")
    parts = [_mesh(f"dock_slot{slot}_{name}.stl") for name in ("back_plate", "channels", "lower_pocket")]
    assert dock.is_watertight and all(p.is_watertight for p in parts)
    assert sum(p.volume for p in parts) == pytest.approx(dock.volume, abs=0.5)
    accent = _mesh(f"dock_slot{slot}_accent.stl")
    assert accent.is_watertight
    assert _overlap(accent, dock) == pytest.approx(0, abs=0.01)  # the inlay's curved faces coincide with the recess; meshing leaves ~0.002mm3 of noise


@pytest.mark.parametrize("material", MATERIALS)
def test_chip_seats_without_touching(material):
    chip, dock = _mesh(f"chip_{material}.stl"), _mesh("dock_slot3.stl")
    assert chip.is_watertight
    assert _overlap(chip, dock) == pytest.approx(0, abs=1e-3)


def test_chip_slides_in_from_above():
    chip, dock = _mesh("chip_PETG.stl"), _mesh("dock_slot3.stl")
    worst = 0.0
    for dy in np.arange(45.0, -0.01, -0.5):
        moved = chip.copy()
        moved.apply_translation([0, dy, 0])
        worst = max(worst, _overlap(moved, dock))
    assert worst == pytest.approx(0, abs=1e-3)


def test_upside_down_chip_cannot_seat():
    """Round end first, the chip must stop on the key post, its lowest point at least most of the post's height above where a correct chip's flat end seats."""
    chip, dock = _turned(_mesh("chip_PETG.stl")), _mesh("dock_slot3.stl")
    lowest = None
    for dy in np.arange(30.0, -15.01, -0.25):
        moved = chip.copy()
        moved.apply_translation([0, dy, 0])
        if _overlap(moved, dock) > 1e-3:
            break
        lowest = float(moved.bounds[0][1])
    assert lowest is not None
    assert lowest - (-M.COIN_FLAT_END_Y) >= M.KEY_POST_HEIGHT - 1.0


@pytest.mark.parametrize("dx, dz", [(1.8, 0), (-1.8, 0), (0, 0.4), (0, -0.6), (1.5, 0.3)])
def test_funnel_catches_an_off_centre_chip(dx, dz):
    dock = _mesh("dock_slot3.stl")
    slab = trimesh.creation.box(extents=[2 * M.COIN_RADIUS, 0.5, M.COIN_THICKNESS])
    slab.apply_translation([dx, dock.bounds[1][1] - 0.25, M.COIN_THICKNESS / 2 + dz])
    assert _overlap(slab, dock) == pytest.approx(0, abs=1e-3)


def test_top_rim_is_one_flat_plane():
    """Every face that reaches the dock's top is flat at the same height: no notches or steps in the rim."""
    dock = _mesh("dock_slot3.stl")
    top = dock.bounds[1][1]
    near_top = dock.vertices[dock.vertices[:, 1] > top - 0.05]
    assert np.allclose(near_top[:, 1], top, atol=1e-4)


def test_orientation_hint_is_an_accent_inlay():
    """The hint is cut into the back plate's face above the lower pocket and filled by the accent part; the plate behind it stays at least 0.6mm thick."""
    dock, accent = _mesh("dock_slot3.stl"), _mesh("dock_slot3_accent.stl")
    y_base = M.ARM_Y_HOOK_TIP - M.COVER_HOOK_CLEARANCE + M.HINT_GAP
    face = -M.DOCK_BACK_GAP
    y_chip = y_base + 7.0  # silhouette above, arrow below
    in_arrow = [0, y_base + 4.0, face - M.HINT_DEPTH / 2]
    in_silhouette = [0, y_chip + 6.0, face - M.HINT_DEPTH / 2]  # the squat chip's middle
    in_notch = [0, y_chip + 0.3, face - M.HINT_DEPTH / 2]
    assert not dock.contains([in_arrow, in_silhouette]).any()
    assert accent.contains([in_arrow, in_silhouette]).all()
    assert dock.contains([in_notch])[0]
    assert M.DOCK_FLOOR - M.HINT_DEPTH >= 0.6
    # Nothing is engraved within HINT_TOP_MARGIN of where the back plate starts to bevel (y_top), across the hint's width.
    y_bevel = M.COIN_RADIUS - M.DOCK_COIN_PROTRUSION
    probes = [[x, y, face - M.HINT_DEPTH / 2] for x in np.linspace(-M.HINT_WIDTH / 2, M.HINT_WIDTH / 2, 25) for y in np.linspace(y_bevel - M.HINT_TOP_MARGIN + 0.05, y_bevel - 0.05, 5)]
    assert dock.contains(probes).all()


def test_back_plate_covers_the_whole_sticker():
    dock = _mesh("dock_slot3.stl")
    r = M.POCKET_DIAMETER / 2
    z_inside = -M.DOCK_BACK_GAP - M.DOCK_FLOOR + 0.2  # within the plate that stays behind the hint's inlay
    probes = np.array([[x, y, z_inside] for x in np.linspace(-r, r, 9) for y in np.linspace(-r, r, 9) if x * x + y * y <= r * r])
    assert dock.contains(probes).all()


def test_sticker_pocket_opens_on_the_back():
    """The pocket is a recess in the back face, so the sticker goes in after printing and can be swapped: open at the back face, solid above its ceiling."""
    chip = _mesh("chip_PETG.stl")
    assert not chip.contains([[0, 0, 0.05]])[0]
    assert not chip.contains([[0, 0, M.POCKET_DEPTH - 0.05]])[0]
    assert chip.contains([[0, 0, M.POCKET_DEPTH + 0.1]])[0]
    edge = M.POCKET_DIAMETER / 2 - 0.1
    assert not chip.contains([[edge, 0, M.POCKET_DEPTH / 2]])[0]


def test_sticker_sits_below_the_back_face():
    """A sticker in the recess stays under the back face, so it never rubs the dock's back plate."""
    assert M.POCKET_DEPTH - M.STICKER_THICKNESS >= 0.1


@pytest.mark.parametrize("material", MATERIALS)
def test_label_stays_inside_the_chip(material):
    label = _mesh(f"chip_{material}_label.stl")
    assert np.hypot(label.vertices[:, 0], label.vertices[:, 1]).max() <= M.COIN_RADIUS - M.LABEL_EDGE_MARGIN + 0.05


@pytest.mark.parametrize("material", MATERIALS)
def test_label_is_centred_and_clear_of_the_lips(material):
    label = _mesh(f"chip_{material}_label.stl")
    (x0, y0, _), (x1, y1, _) = label.bounds
    assert (x0 + x1) / 2 == pytest.approx(0, abs=0.05)
    assert max(abs(x0), abs(x1)) <= M.COIN_RADIUS - M.DOCK_LIP_OVERLAP - M.LABEL_EDGE_MARGIN + 0.05


def test_labels_share_one_line_above_the_hook():
    """All-capital names (no descenders) have their letters centred at the same height; no name's ink comes closer than LABEL_HOOK_GAP to the hook, and the lowest one sits right at it."""
    bounds = {m: _mesh(f"chip_{m}_label.stl").bounds for m in MATERIALS}
    caps_only = [M.file_stem(n) for n in M.FILAMENTS if n.upper() == n]
    centres = [(bounds[m][0][1] + bounds[m][1][1]) / 2 for m in caps_only]
    assert max(centres) - min(centres) <= 0.15  # round letters (S, G, U) overshoot the baseline by about 0.1mm, as fonts do
    floor = -M.ARM_BASE_Y + M.LABEL_HOOK_GAP
    lows = [bounds[m][0][1] for m in MATERIALS]
    assert min(lows) >= floor - 0.05
    assert min(lows) == pytest.approx(floor, abs=0.1)


def test_label_floor_clears_the_sticker_pocket():
    assert M.COIN_THICKNESS - M.ENGRAVE_DEPTH - M.POCKET_DEPTH >= 0.4


def test_hook_finger_stands_proud_of_the_lower_pocket():
    chip, pocket = _mesh("chip_PETG.stl"), _mesh("dock_slot3_lower_pocket.stl")
    assert chip.bounds[1][2] - pocket.bounds[1][2] >= 2.0


def test_clip_matches_extrutim():
    """Independent check: the chip's clip, turned back, is a shifted copy of Extrutim's original within 0.1mm, apart from the end-catch ramp and the taller hook finger."""
    if not CLIP_CLASSIC.exists():
        pytest.skip("Extrutim's Clip-Classic.stl is not present (it is not redistributed)")
    assert hashlib.sha256(CLIP_CLASSIC.read_bytes()).hexdigest().startswith(CLIP_CLASSIC_SHA256_PREFIX)
    shapely = pytest.importorskip("shapely.geometry")
    orig = trimesh.load(CLIP_CLASSIC, force="mesh")
    chip = _turned(_mesh("chip_PETG.stl"))
    base_shift = M.COIN_THICKNESS - 0.9  # chip plate top minus the original's base top
    to_yz = np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, 1]], float)

    def edges(mesh, x, z, lo, hi):
        polys = list(mesh.section(plane_origin=[x, 0, 0], plane_normal=[1, 0, 0]).to_2D(to_2D=to_yz)[0].polygons_full)
        ys = np.linspace(lo, hi, 3000)
        inside = np.array([any(p.contains(shapely.Point(y, z)) for p in polys) for y in ys]).astype(int)
        return ys[np.flatnonzero(np.diff(inside))]

    dy = edges(chip, -8.5, 2.5 + base_shift, -2, 22)[0] - edges(orig, -8.5, 2.5, -6, 17)[0]
    worst = 0.0
    for x in (-7, -5, -3, -1.2, -0.6, 0, 0.6, 1.2, 3, 5, 7):  # stays clear of the end catches at |x| > 8.7
        for z in (1.5, 2.5, 3.5):  # within the original's straight wall height, so the taller hook finger does not count
            o, c = edges(orig, x, z, -6, 17), edges(chip, x, z + base_shift, -2, 22) - dy
            assert len(o) == len(c), f"wall count differs at x={x} z={z}"
            worst = max(worst, float(np.abs(o - c).max()))
    assert worst <= 0.1


HUB_BASE = ROOT / "thingiverse" / "makerworld2152529_hub" / "1.stl"  # 1waynger1's "Machine Interface", split out of tst.3mf; not redistributed
ADAPTER_MESHES = {"socket": "socket_adapter.stl", "hub": "hub_adapter_standin.stl"}


@pytest.mark.parametrize("adapter", M.ADAPTERS)
def test_chip_slides_in_from_above_past_the_mount(adapter):
    chip = _mesh("chip_PETG.stl")
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
