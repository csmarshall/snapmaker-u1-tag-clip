"""Checks for the finger-spread sweep (docs/FINGER_SPREAD.md, issue 9).

What these prove: the spread is an explicit, bounded offset from the traced outline, the root does not move, and the six covers are valid, separate solids on the bed.
What they cannot prove: that any spread grips the real socket. That depends on the real bore (assumed 26.9 mm) and on PETG shrinkage, and only a print answers it.
"""
import sys
import zipfile
import numpy as np
import pytest
import trimesh

from test_fit import M, ROOT, _finger_volumes, _overlap

sys.path.insert(0, str(ROOT / "tools"))
import make_spread_3mf as S  # noqa: E402
import socket_fingers as F  # noqa: E402

SPREADS = S.SPREADS


@pytest.fixture(scope="module")
def covers() -> list[trimesh.Trimesh]:
    """The six sweep covers in the model's frame, built once."""
    return [S.cover_mesh(s) for s in SPREADS]


def test_spread_zero_is_the_traced_outline_itself():
    assert F.spread_outline(0.0) is F.FINGER_OUTLINE
    assert F.spread_outline() == F.FINGER_OUTLINE


@pytest.mark.parametrize("spread", SPREADS)
def test_root_is_unmoved(spread):
    moved = F.spread_outline(spread)
    assert len(moved) == len(F.FINGER_OUTLINE)
    root = [i for i, (depth, _) in enumerate(F.FINGER_OUTLINE) if depth <= F.ROOT_DEPTH]
    assert len(root) == 7  # the tab's corners and the inner edge across the middle
    for i in root:
        assert moved[i] == F.FINGER_OUTLINE[i]
    for (d0, _), (d1, _) in zip(F.FINGER_OUTLINE, moved):
        assert d0 == d1  # depth never changes


@pytest.mark.parametrize("spread", SPREADS)
def test_every_point_moves_outward_by_at_most_the_spread(spread):
    for (_, s0), (_, s1) in zip(F.FINGER_OUTLINE, F.spread_outline(spread)):
        grow = abs(s1) - abs(s0)
        assert -1e-12 <= grow <= spread + 1e-12
        assert np.sign(s1) == np.sign(s0)  # never across the axis


@pytest.mark.parametrize("spread", SPREADS)
def test_width_grows_by_exactly_the_spread_per_side_at_the_hooks(spread):
    assert F.hook_half_width(spread) == pytest.approx(F.hook_half_width(0.0) + spread, abs=1e-9)
    assert F.hook_half_width(0.0) == pytest.approx(11.009)
    hooks = [(a, b) for a, b in zip(F.FINGER_OUTLINE, F.spread_outline(spread)) if a[0] >= F.ROOT_DEPTH + F.SPREAD_RAMP]
    assert len(hooks) > 60  # the whole far end, not just the tip
    for (_, s0), (_, s1) in hooks:
        assert abs(s1) - abs(s0) == pytest.approx(spread, abs=1e-9)


def test_arms_keep_their_thickness_past_the_ramp():
    """The inner and outer faces move together, so where the arm is fully shifted (depth 25.006) it is as thick as traced (2.0 mm: 9.709 outer, 7.709 inner)."""
    for spread in SPREADS:
        side = sorted(b for d, b in F.spread_outline(spread) if d == 25.006 and b > 0)
        assert side == pytest.approx([7.709 + spread, 9.709 + spread])
        assert side[1] - side[0] == pytest.approx(2.0)


def test_cover_at_spread_zero_reproduces_the_traced_fingers():
    """The independent trace check (his holder's fingers, within 2% by volume) on a cover built with spread 0 explicitly, and on a spread 2.5 cover, which it must reject."""
    theirs, ours, shared = _finger_volumes(S.cover_mesh(0.0))
    assert shared == pytest.approx(theirs, rel=0.02) and shared == pytest.approx(ours, rel=0.02)
    theirs, ours, shared = _finger_volumes(S.cover_mesh(2.5))
    assert shared != pytest.approx(ours, rel=0.02)  # the check can see the offset


def test_default_cover_is_the_chosen_spread_cover():
    """Charles chose 2.0 mm per side from the printed sweep (2026-10-15): the default of every variant that carries the fingers."""
    assert F.FINGER_SPREAD == 2.0
    assert M.cover_parts(2)["cover"].volume == pytest.approx(M.cover_parts(2, spread=F.FINGER_SPREAD)["cover"].volume, rel=1e-12)
    assert M.cover_parts(2)["cover"].volume != pytest.approx(M.cover_parts(2, spread=0.0)["cover"].volume, rel=1e-6)


def test_covers_are_valid_solids_with_the_hooks_where_the_spread_puts_them(covers):
    z_back = M._adapter_frame("socket")["z_back"]
    for spread, m in zip(SPREADS, covers):
        assert m.is_watertight and m.volume > 0
        hooks = m.vertices[m.vertices[:, 2] < z_back - F.HOOK_FROM_DEPTH]
        assert np.abs(hooks[:, 0]).max() == pytest.approx(11.009 + spread, abs=1e-3)


def test_root_of_every_cover_is_the_same_plate_and_tab(covers):
    """In front of the root plane the six covers are the same shape: the spread starts behind the panel face."""
    z_back = M._adapter_frame("socket")["z_back"]
    slabs = []
    for m in covers:
        s = m.section(plane_origin=[0, 0, z_back + 0.1], plane_normal=[0, 0, 1])
        slabs.append(sorted(map(tuple, np.round(s.vertices, 3))))
    # The label is engraved from the plate's front, at z_back + thickness, so this slice just inside the panel face is identical.
    assert all(s == slabs[0] for s in slabs)


def test_sweep_plate_is_six_separate_solids_on_the_bed(covers):
    placed = S.lay_out(covers)
    assert len(placed) == 6
    for m in placed:
        assert m.is_watertight
        assert m.bounds[0][2] == pytest.approx(0, abs=1e-6)  # the flat top rests on the bed
        assert m.bounds[0][0] >= 0 and m.bounds[0][1] >= 0 and m.bounds[1][0] <= S.BED and m.bounds[1][1] <= S.BED
    for i in range(6):
        for j in range(i + 1, 6):
            assert _overlap(placed[i], placed[j]) == pytest.approx(0, abs=1e-6)
            gap = np.maximum(placed[i].bounds[0] - placed[j].bounds[1], placed[j].bounds[0] - placed[i].bounds[1])[:2].max()
            assert gap >= S.GAP - 1e-6  # not even touching, by the layout's gap


def test_sweep_3mf_holds_six_labelled_objects(covers, tmp_path):
    out = tmp_path / "sweep.3mf"
    S.write_3mf(out, S.lay_out(covers), [f"Cover, spread {S.label_for(s)}" for s in SPREADS])
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        config = z.read("Metadata/model_settings.config").decode()
        assert len([n for n in z.namelist() if n.startswith("3D/Objects/")]) == 6
    for s in SPREADS:
        assert f"Cover, spread {S.label_for(s)}" in config
    assert config.count("<model_instance>") == 6
    assert S.label_for(0.0) == "+0.0" and config.index("+0.0") < config.index("+2.5")
