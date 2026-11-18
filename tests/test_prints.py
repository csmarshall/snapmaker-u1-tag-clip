"""Checks for the published prints: the vendored label font, byte-reproducible 3MFs and the all-chips plate.

What these prove: writing the same geometry twice gives the same bytes, every zip entry carries the fixed date, the all-chips plate holds one chip per filament inside one bed, and labels use the vendored font file.
They cannot prove the font's glyphs match Arial's exactly, that OCC's meshing is deterministic across machines or versions (only that this writer's canonical order hides run-to-run reordering), or that a slicer opens the files.
"""
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for sub in ("chip", "u1", "u1/tools", "tools"):
    sys.path.insert(0, str(ROOT / sub))

pytest.importorskip("trimesh")
import chip_clip  # noqa: E402
import chip_3mf  # noqa: E402
import print_plates as P  # noqa: E402
from build123d import Text  # noqa: E402


def _chip_3mf(path: Path) -> bytes:
    """Write the PLA chip to `path` and return its bytes."""
    body, inlay = chip_clip.chip_parts("PLA")
    chip_3mf.write_chip_3mf(path, chip_clip.chip_file_stem("PLA"), "Chip, PLA", body, inlay)
    return path.read_bytes()


def test_same_chip_gives_identical_bytes(tmp_path):
    assert _chip_3mf(tmp_path / "a.3mf") == _chip_3mf(tmp_path / "b.3mf")


def test_zip_entries_have_fixed_date(tmp_path):
    _chip_3mf(tmp_path / "a.3mf")
    with zipfile.ZipFile(tmp_path / "a.3mf") as z:
        infos = z.infolist()
        assert infos and all(i.date_time == chip_3mf.ZIP_DATE_TIME == (1980, 1, 1, 0, 0, 0) for i in infos)
        assert all(i.compress_type == zipfile.ZIP_DEFLATED for i in infos)


def test_mesh_order_does_not_change_the_file():
    import numpy as np
    import trimesh

    box = trimesh.creation.box((3, 4, 5))
    shuffled = trimesh.Trimesh(box.vertices[::-1], len(box.vertices) - 1 - box.faces[::-1])
    assert chip_3mf.mesh_xml(1, box) == chip_3mf.mesh_xml(1, shuffled)


def test_font_is_vendored():
    assert Path(chip_clip.LABEL_FONT_PATH).is_file()
    assert (ROOT / "chip" / "fonts" / "OFL.txt").is_file()


def test_label_uses_the_vendored_font():
    explicit = Text("PLA", font_size=9.0, font_path=chip_clip.LABEL_FONT_PATH, align=None).bounding_box().size
    used = chip_clip._label_text("PLA", 9.0, 0.0).bounding_box().size
    assert (used.X, used.Y) == pytest.approx((explicit.X, explicit.Y))


def test_all_chips_tables_cover_every_filament():
    assert len(P.ALL_CHIPS_PARTS) == len(chip_clip.FILAMENTS)
    assert [p[1] for p in P.ALL_CHIPS_PARTS] == [f"Chip, {m}" for m in chip_clip.FILAMENTS]


def test_all_chips_fit_on_one_plate():
    import build_prints

    if not all(f.exists() for *_, files in P.ALL_CHIPS_PARTS for f, _ in files):
        pytest.skip("run the chip build first (with --label-stl)")
    build_prints.assert_fits_one_plate(P.ALL_CHIPS_PARTS)
