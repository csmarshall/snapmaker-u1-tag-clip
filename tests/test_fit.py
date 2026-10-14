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
import trimesh

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


def test_sticker_pocket_is_sealed():
    """The pocket is inside the chip: a point in it is outside the solid, and the back face under it is solid."""
    chip = _mesh("chip_PETG.stl")
    assert not chip.contains([[0, 0, M.BACK_SKIN + M.POCKET_DEPTH / 2]])[0]
    assert chip.contains([[0, 0, M.BACK_SKIN / 2]])[0]
    assert chip.contains([[0, 0, M.PAUSE_HEIGHT + 0.1]])[0]


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
    assert M.COIN_THICKNESS - M.ENGRAVE_DEPTH - M.PAUSE_HEIGHT >= 0.4


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


HANGER_POSES = ["hanger.stl", "hanger_pose_above.stl"]  # the same print, dock below the socket and turned 180 degrees with the dock above


@pytest.mark.parametrize("pose", HANGER_POSES)
def test_chip_slides_in_from_above_past_the_hanger(pose):
    chip, dock = _mesh("chip_PETG.stl"), trimesh.util.concatenate([_mesh("dock_slot3.stl"), _mesh(pose)])
    worst = 0.0
    for dy in np.arange(45.0, -0.01, -0.5):  # from well above, past the hanger's plate when it is above the dock
        moved = chip.copy()
        moved.apply_translation([0, dy, 0])
        worst = max(worst, _overlap(moved, dock))
    assert worst == pytest.approx(0, abs=1e-3)


@pytest.mark.parametrize("pose", HANGER_POSES)
def test_hanger_holds_the_dock_without_touching_it(pose):
    hanger, dock = _mesh(pose), _mesh("dock_slot3.stl")
    assert hanger.is_watertight
    assert _overlap(hanger, dock) == pytest.approx(0, abs=0.01)


@pytest.mark.parametrize("pose", HANGER_POSES)
@pytest.mark.parametrize("shift", [(0, 1.0, 0), (0, -1.0, 0), (0, 0, 1.0)])
def test_tongues_lock_the_dock_up_down_and_away_from_the_panel(pose, shift):
    """Seated, the dock cannot move 1mm up, down or out from the panel without running into the tongues (sideways is the other arm's job)."""
    hanger, dock = _mesh(pose), _mesh("dock_slot3.stl")
    dock.apply_translation(shift)
    assert _overlap(hanger, dock) > 0.05


def test_grip_band_is_centred_and_matches_the_pocket():
    """The band is what is left of the dock's length once the lower pocket's height comes off both ends, so the 180 degree turn maps it onto itself."""
    d = M._dock_extents()
    pocket = d["cover_top"] - d["y_bottom"]
    y0, y1 = d["band"]
    assert y1 - y0 == pytest.approx((d["y_rim"] - d["y_bottom"]) - 2 * pocket)
    assert (y0 + y1) / 2 == pytest.approx(d["y_mid"])
    g0, g1 = d["groove_y"]
    assert (g0 + g1) / 2 == pytest.approx(d["y_mid"])


@pytest.mark.parametrize("pose", HANGER_POSES)
def test_dock_pushes_into_the_hanger_from_the_front_past_the_tongues_only(pose):
    """Pushed straight in toward the panel, the dock only ever meets the tongues, which the arms flex outward to pass; it never meets the plate or yoke."""
    hanger, dock = _mesh(pose), _mesh("dock_slot3.stl")
    d = M._dock_extents()
    engage = M.HANGER_GROOVE_DEPTH - M.FIT_CLEARANCE
    touched = False
    for dz in np.arange(12.0, 0.01, -0.25):
        moved = dock.copy()
        moved.apply_translation([0, 0, dz])
        inter = trimesh.boolean.intersection([moved, hanger], engine="manifold")
        if len(inter.vertices) and inter.volume > 1e-3:
            touched = True
            assert np.abs(inter.vertices[:, 0]).min() >= d["outer_half"] - engage - 0.05
            assert d["groove_y"][0] - 0.05 <= inter.vertices[:, 1].min() and inter.vertices[:, 1].max() <= d["groove_y"][1] + 0.05
    assert touched  # the tongues do catch it: that is the snap


def test_hanger_and_cover_stand_on_one_flat_face_for_printing():
    """Upside down, the plate's flat top and the fingers' top face are the lowest points, level with each other."""
    top = M.SOCKET_ABOVE_STICKER + M.SOCKET_PLATE_FLAT
    for name in ("hanger.stl", "cover_slot3.stl"):
        m = _mesh(name)
        assert m.bounds[1][1] == pytest.approx(top, abs=0.02)
        finger_tops = m.vertices[(m.vertices[:, 2] < -M.DOCK_BACK_GAP - M.DOCK_FLOOR - 0.5)][:, 1]
        assert finger_tops.max() == pytest.approx(top, abs=0.02)


def test_cover_parts_are_watertight_and_disjoint():
    cover, accent = _mesh("cover_slot3.stl"), _mesh("cover_slot3_accent.stl")
    assert cover.is_watertight and accent.is_watertight
    assert _overlap(cover, accent) == pytest.approx(0, abs=0.01)


@pytest.mark.parametrize("piece", ["hanger.stl", "cover_slot3.stl"])
def test_socket_fingers_match_remmulegguh(piece):
    """Independent check: the traced fingers, mapped into the dock frame, coincide with his holder's fingers within 2% by volume."""
    src = ROOT / "thingiverse" / "printables1625982" / "holderrfid_short.stl"
    if not src.exists():
        pytest.skip("remmulegguh's holderrfid_short.stl is not present (it is not redistributed)")
    his = trimesh.load(src, force="mesh")
    his.apply_translation([0, -219.3, 6.5])  # his socket axis to the origin
    plate_back = 179.15
    z_back = -M.DOCK_BACK_GAP - M.DOCK_FLOOR
    # His frame to ours: sideways y -> X, down +z -> -Y, depth x -> -Z. A proper rotation: no mirror.
    R = np.array([[0, 1, 0], [0, 0, -1], [-1, 0, 0]], float)
    assert np.linalg.det(R) == pytest.approx(1.0)
    his.vertices = his.vertices @ R.T + [0, M.SOCKET_ABOVE_STICKER, z_back + plate_back]
    probe = trimesh.creation.box(extents=[40, 20, 29])
    probe.apply_translation([0, M.SOCKET_ABOVE_STICKER, z_back - 15.5])  # the fingers' region, 1-30mm deep, clear of both plates
    ours = trimesh.boolean.intersection([_mesh(piece), probe], engine="manifold")
    theirs = trimesh.boolean.intersection([his, probe], engine="manifold")
    shared = trimesh.boolean.intersection([ours, theirs], engine="manifold")
    assert theirs.volume > 100
    assert shared.volume == pytest.approx(theirs.volume, rel=0.02)
    assert shared.volume == pytest.approx(ours.volume, rel=0.02)
