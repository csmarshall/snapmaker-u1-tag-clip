"""Checks for the two production plates: the four docks with fingers (u1_docks_fingers_set.3mf) and the 25-chip sheet (u1_chip_sheet.3mf).

Run the build first. What these prove: the right parts in the right counts, each on the bed, none touching another by at least the layout gap, and the 3MF listing them. They cannot prove the slicer
will arrange supports, brims or colour changes as hoped (the file carries no settings), or that any of it prints well in PETG.
"""
import re
import zipfile
from collections import Counter

import numpy as np
import pytest

from u1_model import M, ROOT  # noqa: F401

import make_3mf  # noqa: E402
import print_plates as P  # noqa: E402


def _placed(table):
    pytest.importorskip("trimesh")
    if not all(f.exists() for *_, files in table for f, _ in files):
        pytest.skip("run the build first")
    return P.lay_out(table)[1]


def _footprints(parts):
    return [np.array([np.min([m.bounds[0] for _, _, m in p["files"]], axis=0), np.max([m.bounds[1] for _, _, m in p["files"]], axis=0)]) for p in parts]


def _check_layout(parts):
    boxes = _footprints(parts)
    lo, hi = np.min([b[0] for b in boxes], axis=0), np.max([b[1] for b in boxes], axis=0)
    assert (hi - lo)[0] <= P.BED and (hi - lo)[1] <= P.BED, "the set does not fit one bed"
    for p in parts:
        body = p["files"][0][2]
        assert body.bounds[0][2] == pytest.approx(0, abs=1e-6)  # the body rests on the bed
        for _, _, m in p["files"][1:]:
            assert m.bounds[0][2] >= -1e-6
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            gap = np.maximum(boxes[i][0] - boxes[j][1], boxes[j][0] - boxes[i][1])[:2].max()
            assert gap >= P.GAP - 1e-6, f"{parts[i]['name']} and {parts[j]['name']} are closer than the layout gap"
    return hi - lo


def test_docks_set_is_slots_one_to_four_once_each():
    parts = _placed(P.DOCKS_SET_PARTS)
    assert [p["name"] for p in parts] == [f"Dock with fingers, slot {s}" for s in M.U1_SLOTS]
    assert all(p["name"] in make_3mf.SUPPORTED for p in parts)  # build-plate-only support under every dock's fingers
    assert all(np.allclose(rot, P.ON_BOTTOM_STOP) for _, _, _, rot, _ in P.DOCKS_SET_PARTS)
    assert all([role for _, role in files] == ["dock", "label"] for *_, files in P.DOCKS_SET_PARTS)


def test_docks_set_fits_the_bed_with_the_layout_gap():
    extent = _check_layout(_placed(P.DOCKS_SET_PARTS))
    assert extent[0] > 100  # four docks really are side by side, not stacked in one spot


def test_chip_sheet_counts_per_label():
    counts = Counter(p["name"] for p in _placed(P.CHIP_SHEET_PARTS))
    assert counts == {"Chip, PETG label": 16, "Chip, PLA label": 7, "Chip, PVA label": 1, "Chip, PCTG label": 1}
    assert sum(counts.values()) == 25


def test_chip_sheet_fits_one_bed_without_overlap():
    extent = _check_layout(_placed(P.CHIP_SHEET_PARTS))
    print(f"chip sheet footprint {extent[0]:.1f} x {extent[1]:.1f} mm on a {P.BED:g} mm bed")
    assert extent[0] <= P.BED and extent[1] <= P.BED


def test_each_chip_carries_its_own_label():
    for p in _placed(P.CHIP_SHEET_PARTS):
        material = p["name"].split(", ")[1].split(" ")[0]
        (body_file, _, body), (label_file, _, label) = p["files"]
        assert body_file.stem == f"chip_{material}" and label_file.stem == f"chip_{material}_label"
        assert label.bounds[0][:2] == pytest.approx(label.bounds[0][:2])
        assert (label.bounds[0][:2] >= body.bounds[0][:2] - 1e-6).all() and (label.bounds[1][:2] <= body.bounds[1][:2] + 1e-6).all()  # the label sits inside its chip


def test_the_3mfs_list_the_same_parts(tmp_path):
    for table, plates, title, expected in (
        (P.DOCKS_SET_PARTS, P.DOCKS_SET_PLATES, "docks", Counter(f"Dock with fingers, slot {s}" for s in M.U1_SLOTS)),
        (P.CHIP_SHEET_PARTS, P.CHIP_SHEET_PLATES, "chips", Counter({"Chip, PETG label": 16, "Chip, PLA label": 7, "Chip, PVA label": 1, "Chip, PCTG label": 1})),
    ):
        if not all(f.exists() for *_, files in table for f, _ in files):
            pytest.skip("run the build first")
        out = tmp_path / f"{title}.3mf"
        names = make_3mf.write_skeleton(out, table, plates, title)
        assert Counter(names) == expected
        with zipfile.ZipFile(out) as z:
            config = z.read("Metadata/model_settings.config").decode()
        objects = re.findall(r'<object id="\d+"><metadata key="name" value="([^"]*)"/>', config)
        assert Counter(objects) == expected
        assert config.count("<model_instance>") == len(names)
        assert config.count('enable_support" value="1"') == (4 if title == "docks" else 0)
