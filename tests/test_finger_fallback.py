"""Checks for the fallback socket adapter (coin/finger_fallback.py): a harness plate and a separate snap-finger piece joined by a dovetail with detent ridges.

The parts are built here from the model, not read from coin/out. Every number the checks compare against comes from the same constants the parts were built from
(FIT_CLEARANCE, FINGER_OUTLINE, the adapter's dimensions), so passing means the pieces agree with their own parameters and with the traced outline; it does not mean
they fit a real printer, that PETG prints these dimensions, or that the detent has a usable push-in force. Those need the printed test.
"""
import sys
import zipfile
from functools import reduce
from pathlib import Path
from xml.etree import ElementTree

import numpy as np
import pytest
import shapely
import trimesh
from build123d import export_stl
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "coin"))
sys.path.insert(0, str(ROOT / "tools"))
import finger_fallback as FF  # noqa: E402
import finger_fallback_plate as FP  # noqa: E402
from print_orientation import orient  # noqa: E402
import u1_chip_clip as M  # noqa: E402
from socket_fingers import FINGER_HEIGHT, FINGER_OUTLINE  # noqa: E402

FRAME = M._adapter_frame("socket")
Z0, AXIS_Y, Y_TOP = FRAME["z_back"], FRAME["axis_y"], FRAME["y_top"]
C = M.FIT_CLEARANCE
J = FF.joint_geometry()


def _to_mesh(shape, tmp_path_factory, name: str) -> trimesh.Trimesh:
    path = tmp_path_factory.mktemp(name) / f"{name}.stl"
    export_stl(shape, str(path))
    return trimesh.load(path, force="mesh")


@pytest.fixture(scope="module")
def meshes(tmp_path_factory):
    """The plate, the finger piece and the integral adapter and its plain plate, meshed."""
    return {
        "plate": _to_mesh(FF.harness_plate(), tmp_path_factory, "plate"),
        "fingers": _to_mesh(FF.finger_piece(), tmp_path_factory, "fingers"),
        "adapter": _to_mesh(M.socket_adapter_parts()["socket_adapter"], tmp_path_factory, "adapter"),
        "plain_plate": _to_mesh(M._adapter_plate("socket"), tmp_path_factory, "plain_plate"),
    }


def _section(mesh: trimesh.Trimesh, y: float) -> Polygon:
    """The mesh cut by the plane Y=y, as a shapely shape in (X, Z) (loops combined even-odd, so holes are holes)."""
    loops = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0]).discrete
    return reduce(lambda a, b: a.symmetric_difference(b), [Polygon(loop[:, [0, 2]]) for loop in loops])


def _overlap(a: trimesh.Trimesh, b: trimesh.Trimesh) -> float:
    """Volume shared by two meshes (mm3)."""
    return float(a.intersection(b, engine="manifold").volume)


def _moved(mesh: trimesh.Trimesh, dx=0.0, dy=0.0, dz=0.0) -> trimesh.Trimesh:
    m = mesh.copy()
    m.apply_translation([dx, dy, dz])
    return m


def test_joint_constants_are_derived_from_the_fit_clearance():
    """The tongue is the groove less FIT_CLEARANCE on every face: floor, and each flank measured square to itself."""
    assert J["z_floor"] - J["z_head"] == pytest.approx(C)
    flank_gap = FF.tongue_edges(J, J["z_tab"])[0] - FF.groove_edges(J, J["z_tab"])[0]
    assert flank_gap == pytest.approx(J["side"])
    assert flank_gap / np.sqrt(1 + J["slope"] ** 2) == pytest.approx(C)  # the square-on distance between the two flank lines


def test_finger_piece_matches_the_traced_outline(meshes):
    """The piece's section through the fingers' mid-height, seen from the same side as the trace, is FINGER_OUTLINE, and its height is FINGER_HEIGHT centred on the socket axis."""
    piece = meshes["fingers"]
    section = _section(piece, AXIS_Y)
    # chip frame (X, Z) back to the trace's (depth into the socket, sideways): depth = z_back - Z. The tongues and ridges stand in front of the tab (depth < -TAB), outside the trace.
    traced = Polygon([(side, Z0 - depth) for depth, side in FINGER_OUTLINE])
    behind_tab = shapely.box(-100, -100, 100, Z0 + FF.TAB_THICKNESS)
    assert section.intersection(behind_tab).symmetric_difference(traced).area < 1e-3
    assert piece.bounds[0][1] == pytest.approx(AXIS_Y - FINGER_HEIGHT / 2, abs=1e-4)
    assert piece.bounds[1][1] == pytest.approx(AXIS_Y + FINGER_HEIGHT / 2, abs=1e-4)
    # the same trace as the integral adapter's fingers, to the vertex
    adapter_section = _section(meshes["adapter"], AXIS_Y)
    in_fingers = shapely.box(-100, -100, 100, Z0)  # depth >= 0: the fingers proper, beyond the plate
    assert section.intersection(in_fingers).symmetric_difference(adapter_section.intersection(in_fingers)).area < 1e-3


def test_harness_plate_keeps_envelope_and_slot(meshes):
    """The plate has the integral adapter's bounding box, and only back-face material is gone: the slot and the front face are untouched."""
    plate, plain = meshes["plate"], meshes["plain_plate"]
    assert plate.bounds == pytest.approx(plain.bounds, abs=1e-4)
    assert plain.volume - plate.volume > 0
    z_cut = Z0 + J["z_floor"] + FF.DETENT_HEIGHT  # the dimples' ceiling
    for y, expect_cut in ((AXIS_Y - FINGER_HEIGHT / 2 - 0.5, False), (AXIS_Y - FINGER_HEIGHT, False), (AXIS_Y - 1.0, True), (AXIS_Y, True), (Y_TOP - 0.1, True)):
        gone = _section(plain, y).difference(_section(plate, y))
        assert (gone.area > 0) == expect_cut, f"y={y:.2f}"
        if expect_cut:
            assert gone.bounds[3] <= z_cut + 1e-4  # nothing is cut past the dimples' ceiling
    # the slot cavity itself is the same: the plate's and the plain plate's front-face sections match above the cuts
    above_cuts = shapely.box(-100, z_cut, 100, 100)
    y_probe = AXIS_Y - 1.0  # inside the finger piece's span, away from the dimples
    assert _section(plate, y_probe).intersection(above_cuts).symmetric_difference(_section(plain, y_probe).intersection(above_cuts)).area < 1e-6


def test_grooves_keep_their_wall_from_the_slot(meshes):
    """Beside the dock mount's slot every groove keeps ARM_WALL_THICKNESS of plate, and the rebate leaves the slot's rear wall the thickness left over (reported, not assumed adequate)."""
    plate, plain = meshes["plate"], meshes["plain_plate"]
    y = AXIS_Y - 1.0
    removed = _section(plain, y).difference(_section(plate, y))
    slot_half = [(w, M.ADAPTER_THICKNESS - depth + Z0) for w, depth in M.ADAPTER_SLOT_PROFILE]
    slot = Polygon([(-w, z) for w, z in slot_half] + [(w, z) for w, z in reversed(slot_half)])
    grooves = removed.intersection(shapely.box(-100, Z0 + FF.TAB_THICKNESS + C + 1e-6, 100, 100))
    assert grooves.distance(slot) >= M.ARM_WALL_THICKNESS - 1e-3
    side_wall = M.ADAPTER_WIDTH / 2 - max(abs(x) for x in shapely.get_coordinates(grooves)[:, 0])
    assert side_wall >= M.ARM_WALL_THICKNESS - 1e-3
    rear_wall = removed.distance(slot)  # the rebate's ceiling to the slot's rear wall
    assert rear_wall == pytest.approx(M.ADAPTER_THICKNESS - M.ADAPTER_SLOT_PROFILE[-1][1] - FF.TAB_THICKNESS - C, abs=1e-3)
    assert rear_wall > 0.5  # recorded in docs/FINGER_FALLBACK.md: about 0.63 mm, thinner than the integral adapter's 1.23


def test_pieces_assemble_without_interference_and_with_the_derived_clearance(meshes):
    """Seated, the pieces share no volume, the top faces are flush, and in a section through the joint their gap is FIT_CLEARANCE everywhere (the ridge's tip included)."""
    plate, piece = meshes["plate"], meshes["fingers"]
    assert _overlap(plate, piece) == pytest.approx(0.0, abs=1e-6)
    assert piece.bounds[1][1] == pytest.approx(plate.bounds[1][1], abs=1e-4)  # the finger piece's top face is level with the plate's top edge
    for y in (AXIS_Y - 3.0, AXIS_Y, AXIS_Y + 3.0):  # through the ridge's tip and either side of it
        gap = _section(plate, y).distance(_section(piece, y))
        assert gap == pytest.approx(C, abs=2e-3), f"gap {gap:.4f} at y={y:.2f}"


def test_finger_piece_seats_on_the_groove_stop(meshes):
    """Pushing the finger piece further down meets the plate's stop; there is no play to speak of before it."""
    plate, piece = meshes["plate"], meshes["fingers"]
    assert _overlap(plate, _moved(piece, dy=-0.05)) > 0
    assert _overlap(plate, _moved(piece, dy=-C / 10)) > 0


def test_dovetail_locks_the_piece_against_pulling_straight_out(meshes):
    """Pulling the finger piece out of the plate (-Z), or sideways, makes the tongues meet the groove flanks well inside a millimetre."""
    plate, piece = meshes["plate"], meshes["fingers"]
    assert _overlap(plate, _moved(piece, dz=-1.0)) > 0
    assert _overlap(plate, _moved(piece, dx=1.0)) > 0 and _overlap(plate, _moved(piece, dx=-1.0)) > 0


def test_detent_engages(meshes):
    """The ridges are proud of the groove floor by DETENT_INTERFERENCE, so sliding the seated piece up pushes them into the plate; the dimples hold them seated, and clear them by FIT_CLEARANCE."""
    plate, piece = meshes["plate"], meshes["fingers"]
    ridge_top = Z0 + J["z_head"] + FF.DETENT_HEIGHT
    assert ridge_top - (Z0 + J["z_floor"]) == pytest.approx(FF.DETENT_INTERFERENCE)
    # Seated, the ridge sits in its dimple with no contact (checked in the assembly test). Slid up a little, its ramp meets the dimple's edge.
    up = FF.DETENT_HALF_LENGTH * 0.7
    assert _overlap(plate, _moved(piece, dy=up)) > 0
    # Slid out of the dimple altogether, the ridge presses into the floor by exactly the interference, and no further.
    out = _overlap(plate, _moved(piece, dy=2 * (FF.DETENT_HALF_LENGTH + C)))
    assert out > 0
    clipped = plate.intersection(_moved(piece, dy=2 * (FF.DETENT_HALF_LENGTH + C)), engine="manifold")
    assert clipped.extents[2] == pytest.approx(FF.DETENT_INTERFERENCE, abs=1e-4)


def test_detent_ridge_is_gentle_enough_to_print_and_to_push_over():
    """The ridge's steepest slope (along Y, which prints vertically) is under the 45 degree overhang limit."""
    steepest = FF.DETENT_HEIGHT * np.pi / 2 / FF.DETENT_HALF_LENGTH
    assert steepest < 1.0


def test_orientation_is_the_one_with_least_overhang(meshes):
    """Each piece is turned to its least-overhang face down; the finger piece stands on a flat end of its extrusion with none, the plate beats the integral adapter's orientation (top edge down), where the grooves' stops would bridge."""
    for name, mesh in (("plate", meshes["plate"]), ("fingers", meshes["fingers"])):
        rows = FP.candidates(mesh)
        choice = FP.best(rows)
        assert len(rows) == 6
        assert all(choice["overhang_mm2"] <= r["overhang_mm2"] + 1e-9 for r in rows)
        if name == "fingers":
            assert choice["overhang_mm2"] < 0.1  # a sliver of the trace's own facets at most
            assert choice["height"] == pytest.approx(FINGER_HEIGHT, abs=1e-4)
    rows = FP.candidates(meshes["plate"])
    top_edge = next(r for r in rows if r["face"].startswith("top edge"))  # the integral adapter's orientation
    assert FP.best(rows)["overhang_mm2"] < top_edge["overhang_mm2"]  # the groove stops would be bridges with the top edge down


def test_fallback_3mf_builds(meshes, tmp_path):
    """The plate file is well-formed XML, holds both pieces on a plate inside the bed, and every piece sits on the bed."""
    placed = []
    for name, mesh in (("Harness plate", meshes["plate"]), ("Finger piece", meshes["fingers"])):
        choice = FP.best(FP.candidates(mesh))
        placed.append({"name": name, "choice": choice, "rows": [], "mesh": orient(mesh, choice["rotation"])})
    placed[1]["mesh"].apply_translation([placed[0]["mesh"].extents[0] + 12.0, 0, 0])
    path = tmp_path / "fallback.3mf"
    FP.write_3mf(path, placed)
    with zipfile.ZipFile(path) as z:
        for member in z.namelist():
            ElementTree.fromstring(z.read(member))
        assert sum(n.startswith("3D/Objects/object_") for n in z.namelist()) == 2
        assert z.read("Metadata/model_settings.config").count(b"<plate>") == 1
    assert all(p["mesh"].bounds[0][2] == pytest.approx(0.0, abs=1e-4) for p in placed)
