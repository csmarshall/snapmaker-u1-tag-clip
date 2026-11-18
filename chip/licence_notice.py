"""The licence notice written into every exported file: 3MF core metadata, the STEP header and the STL header.

REUSE.toml is the source of truth. The notice reads the licence and the copyright lines from its `prints/**` table (the generated print files),
so changing the licence there changes every file the next build writes. Nothing here is typed twice.

A notice in a file states who made it and on what terms, and survives a re-upload of the file as is. It does not stop anyone from stripping it.
"""

from __future__ import annotations

import logging
import re
import tomllib
from functools import cache
from pathlib import Path
from xml.sax.saxutils import escape

from build123d import export_step, export_stl

log = logging.getLogger("licence_notice")

REPO = Path(__file__).resolve().parent.parent
REUSE_TOML = REPO / "REUSE.toml"
PRINTS_TABLE_PATH = "prints/**"  # the REUSE.toml table whose terms the exported files carry
REPO_URL = "https://github.com/csmarshall/snapmaker-u1-tag-clip"
SHORT_REPO = "github.com/csmarshall/snapmaker-u1-tag-clip"
LICENCE_NAMES = {"CC-BY-NC-SA-4.0": "CC BY-NC-SA 4.0"}  # SPDX id to the name people recognise
LICENCE_URLS = {"CC-BY-NC-SA-4.0": "https://creativecommons.org/licenses/by-nc-sa/4.0/"}
STL_HEADER_BYTES = 80


@cache
def _prints_table() -> dict[str, object]:
    """The REUSE.toml annotation table for the generated print files."""
    for table in tomllib.loads(REUSE_TOML.read_text())["annotations"]:
        paths = table["path"] if isinstance(table["path"], list) else [table["path"]]
        if PRINTS_TABLE_PATH in paths:
            return table
    raise LookupError(f"REUSE.toml has no table for {PRINTS_TABLE_PATH!r}")


def spdx_id() -> str:
    """The SPDX licence id of the print files, e.g. CC-BY-NC-SA-4.0."""
    return str(_prints_table()["SPDX-License-Identifier"])


def copyright_lines() -> list[str]:
    """The copyright lines of the print files, ours first."""
    value = _prints_table()["SPDX-FileCopyrightText"]
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]


def designer() -> str:
    """Our name, from the first copyright line with its leading year(s) dropped."""
    return re.sub(r"^[\d\s,\-–]+", "", copyright_lines()[0]).strip()


def licence_name() -> str:
    """The licence as people write it, e.g. CC BY-NC-SA 4.0."""
    return LICENCE_NAMES.get(spdx_id(), spdx_id())


def copyright_text() -> str:
    """One-line copyright: ours, then the authors whose work is traced in, without their URLs."""
    ours, *others = copyright_lines()
    text = f"© {ours}"
    if others:
        text += ". Includes work by " + ", ".join(re.sub(r"\s*<[^>]*>", "", o) for o in others)
    return text + "."


def licence_terms() -> str:
    """The licence terms sentence for metadata fields."""
    url = LICENCE_URLS.get(spdx_id(), "")
    return f"{licence_name()} ({url}). Non-commercial: not for resale, in any form, printed or as files. To ask about selling, open an issue at {REPO_URL}."


def model_metadata_xml(title: str) -> str:
    """3MF core-spec metadata elements: Title, Designer, Copyright, LicenseTerms (and Description pointing at the repo)."""
    fields = {
        "Title": title,
        "Designer": designer(),
        "Copyright": copyright_text(),
        "LicenseTerms": licence_terms(),
        "Description": f"{title}. Source and licence: {REPO_URL}",
    }
    return "".join(f'<metadata name="{k}">{escape(v)}</metadata>' for k, v in fields.items())


def stl_header() -> bytes:
    """The 80-byte binary STL header: licence, not for resale, repo (the names don't fit; the 3MF and STEP carry them). Never starts with 'solid', which some readers take for an ASCII STL."""
    text = f"{licence_name()} NOT FOR RESALE {SHORT_REPO}"
    data = text.encode("ascii", "replace")[:STL_HEADER_BYTES]
    return data.ljust(STL_HEADER_BYTES, b"\0")


def export_stl_with_notice(shape: object, path: str | Path) -> None:
    """export_stl (binary), then overwrite the 80-byte header with the licence notice. The header is free text in binary STL; the triangles are untouched."""
    export_stl(shape, str(path))  # type: ignore[arg-type]
    with open(path, "r+b") as f:
        if f.read(5) == b"solid":
            log.warning("%s is ASCII STL; header notice skipped", path)
            return
        f.seek(0)
        f.write(stl_header())


def _step_string(text: str) -> str:
    """A STEP string literal: apostrophes doubled, ASCII only (© becomes (c))."""
    return "'" + text.replace("©", "(c)").encode("ascii", "replace").decode().replace("'", "''") + "'"


def export_step_with_notice(shape: object, path: str | Path, name: str | None = None) -> None:
    """export_step, then rewrite the header's FILE_DESCRIPTION (licence) and FILE_NAME (part name, author, organisation)."""
    export_step(shape, str(path))  # type: ignore[arg-type]
    name = name or Path(path).stem
    text = Path(path).read_text()
    description = f"FILE_DESCRIPTION(({_step_string(f'{name}. {licence_name()}, not for resale. {REPO_URL}')}),'2;1');"
    text, n_desc = re.subn(r"FILE_DESCRIPTION\(.*?\);", lambda _: description, text, count=1, flags=re.S)
    file_name = re.search(r"FILE_NAME\((.*?)\);", text, flags=re.S)
    if file_name is None or n_desc != 1:
        raise ValueError(f"{path}: STEP header not in the expected form, notice not written")
    timestamp = re.search(r"'\d{4}-\d\d-\d\dT[\d:]+'", file_name.group(1))
    fields = [
        _step_string(name),
        timestamp.group(0) if timestamp else "''",
        f"({_step_string(designer())})",
        f"({_step_string(copyright_text())})",
        "'Open CASCADE STEP processor'",
        "'build123d'",
        _step_string(licence_terms()),
    ]
    text = text[: file_name.start()] + "FILE_NAME(" + ",".join(fields) + ");" + text[file_name.end() :]
    Path(path).write_text(text)
