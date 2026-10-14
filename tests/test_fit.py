"""Fit and consistency checks for the chip and docks built by coin/u1_chip_clip.py.

Run the build first, then the tests (see README). Every check except test_clip_matches_extrutim compares the parts with numbers from the same script, so passing
means the files agree with their own parameters, not that anything fits a real printer or sticker.
"""
import hashlib
import importlib.util
from pathlib import Path

import numpy as np
import pytest
import trimesh

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "coin" / "out"
MATERIALS = ("PLA", "PLAplus", "PETG", "ASA", "ABS", "TPU", "Nylon")
# Extrutim's Clip-Classic.stl from Printables 24371; not redistributed here, so the comparison skips when it is absent.
CLIP_CLASSIC = ROOT / "thingiverse" / "printables24371_clip" / "Clips" / "Clip-Classic.stl"
CLIP_CLASSIC_SHA256_PREFIX = "5cb545de106921d3"


def _load_model():
    """Import the build script as a module, for its constants."""
    spec = importlib.util.spec_from_file_location("u1_chip_clip", ROOT / "coin" / "u1_chip_clip.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


M = _load_model()


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
    assert _overlap(_mesh(f"dock_slot{slot}_digit.stl"), dock) == pytest.approx(0, abs=1e-3)


@pytest.mark.parametrize("material", MATERIALS)
def test_chip_seats_without_touching(material):
    chip, dock = _mesh(f"chip_{material}.stl"), _mesh("dock_slot3.stl")
    assert chip.is_watertight
    assert _overlap(chip, dock) == pytest.approx(0, abs=1e-3)


def test_chip_slides_in_from_above():
    chip, dock = _mesh("chip_PETG.stl"), _mesh("dock_slot3.stl")
    worst = 0.0
    for dy in np.arange(30.0, -0.01, -0.5):
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


def test_orientation_hint_is_engraved_and_shallow():
    """The hint is cut into the back plate's face above the lower pocket, and the plate behind it stays at least 0.6mm thick."""
    dock = _mesh("dock_slot3.stl")
    y_base = M.ARM_Y_HOOK_TIP - M.COVER_HOOK_CLEARANCE + M.HINT_GAP
    face = -M.DOCK_BACK_GAP
    y_chip = y_base + 7.0  # silhouette above, arrow below
    in_arrow = [0, y_base + 4.0, face - M.HINT_DEPTH / 2]
    in_silhouette = [-M.HINT_WIDTH / 4, y_chip + 2.0, face - M.HINT_DEPTH / 2]
    in_notch = [0, y_chip + 0.3, face - M.HINT_DEPTH / 2]
    assert not dock.contains([in_arrow, in_silhouette]).any()
    assert dock.contains([in_notch])[0]
    assert M.DOCK_FLOOR - M.HINT_DEPTH >= 0.6


def test_back_plate_covers_the_whole_sticker():
    dock = _mesh("dock_slot3.stl")
    r = M.POCKET_DIAMETER / 2
    probes = np.array([[x, y, -M.DOCK_BACK_GAP - M.DOCK_FLOOR / 2] for x in np.linspace(-r, r, 9) for y in np.linspace(-r, r, 9) if x * x + y * y <= r * r])
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
def test_label_is_centred_on_the_visible_face(material):
    """Docked, you see the chip from the hook finger's top up to the chip's top, between the lips; the label sits on that shape's area centroid and clear of the lips."""
    label = _mesh(f"chip_{material}_label.stl")
    (x0, y0, _), (x1, y1, _) = label.bounds
    # Independent estimate of the visible face's centroid: sample a grid of points and keep those on the chip, above the hook, between the lips.
    xs, ys = np.meshgrid(np.linspace(-16, 16, 641), np.linspace(-M.ARM_BASE_Y, M.COIN_RADIUS, 381))
    inside = (np.abs(xs) <= M.COIN_RADIUS - M.DOCK_LIP_OVERLAP) & ((ys <= 0) | (xs ** 2 + ys ** 2 <= M.COIN_RADIUS ** 2))
    assert (x0 + x1) / 2 == pytest.approx(0, abs=0.05)
    assert (y0 + y1) / 2 == pytest.approx(ys[inside].mean(), abs=0.1)
    assert max(abs(x0), abs(x1)) <= M.COIN_RADIUS - M.DOCK_LIP_OVERLAP - M.LABEL_EDGE_MARGIN + 0.05


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
