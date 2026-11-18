"""The licence notice inside the built files (chip/out): 3MF core metadata, the STEP header and the STL header.

Run the build first (`cd chip && python chip_clip.py`); without it these skip. The expected licence comes from REUSE.toml, read here with tomllib and
not through chip/licence_notice.py, so a broken lookup in that module would fail these. They can't tell whether REUSE.toml itself names the right
licence; `reuse lint` and review cover that.
"""

from __future__ import annotations

import tomllib
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "chip" / "out"
REPO_URL = "github.com/csmarshall/snapmaker-u1-tag-clip"
CORE_NS = "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}"


def _prints_licence() -> str:
    """The SPDX id REUSE.toml gives the print files."""
    for table in tomllib.loads((ROOT / "REUSE.toml").read_text())["annotations"]:
        paths = table["path"] if isinstance(table["path"], list) else [table["path"]]
        if "prints/**" in paths:
            return table["SPDX-License-Identifier"]
    raise AssertionError("REUSE.toml has no prints/** table")


def _human(spdx: str) -> str:
    """CC-BY-NC-SA-4.0 -> CC BY-NC-SA 4.0, by the SPDX naming pattern."""
    assert spdx.startswith("CC-"), spdx
    *parts, version = spdx.split("-")
    return f"CC {'-'.join(parts[1:])} {version}"


def _built(pattern: str) -> list[Path]:
    """Built files matching `pattern`, or skip when the build hasn't run."""
    files = sorted(OUT.glob(pattern))
    if not files:
        pytest.skip(f"no {pattern} in chip/out; run the build first")
    return files


def test_3mf_core_metadata() -> None:
    """Every chip 3MF names its designer, copyright and licence terms in the core-spec metadata fields."""
    licence = _human(_prints_licence())
    for path in _built("*.3mf"):
        with zipfile.ZipFile(path) as z:
            model = ElementTree.fromstring(z.read("3D/3dmodel.model"))
        meta = {m.get("name"): (m.text or "") for m in model.findall(f"{CORE_NS}metadata")}
        assert meta.get("Title"), path
        assert meta.get("Designer") == "Charles Marshall", path
        assert "Charles Marshall" in meta.get("Copyright", ""), path
        terms = meta.get("LicenseTerms", "")
        assert licence in terms and "not for resale" in terms.lower() and REPO_URL in terms, (path, terms)


def test_stl_header() -> None:
    """Every binary STL's 80-byte header carries the licence and the repo, and doesn't start with 'solid' (ASCII STL marker)."""
    licence = _human(_prints_licence())
    for path in _built("*.stl"):
        header = path.read_bytes()[:80]
        assert not header.startswith(b"solid"), path
        text = header.decode("ascii", "replace")
        assert licence in text and "NOT FOR RESALE" in text and REPO_URL in text, (path, text)


def test_step_header() -> None:
    """Every STEP file's header names the author and the licence."""
    licence = _human(_prints_licence())
    for path in _built("*.step"):
        head = path.read_text(errors="replace").split("ENDSEC;", 1)[0]
        assert "('Charles Marshall')" in head, path
        assert licence in head and "not for resale" in head.lower() and REPO_URL in head, path
