"""Check that every tracked file matches exactly one [[annotations]] table in REUSE.toml.

`reuse lint` already fails when a file has no licence, but when two tables match the same file REUSE quietly uses the last one, so an overlap could
change a file's licence without anyone noticing. This check fails on both: no match, or more than one.

Globs follow REUSE spec 3.3: `*` matches anything except `/`, `**` matches anything including `/`. Files REUSE ignores itself (LICENSE*, COPYING*,
LICENSES/, REUSE.toml) are skipped.

Run: uv run python tools/check_reuse_coverage.py
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
log = logging.getLogger("check_reuse_coverage")

IGNORED = re.compile(r"^(LICENSES/.*|REUSE\.toml|(.*/)?(LICENSE|COPYING)(\..*)?)$")


def glob_to_regex(glob: str) -> re.Pattern[str]:
    """Translate one REUSE 3.3 path glob into an anchored regex."""
    out: list[str] = []
    i = 0
    while i < len(glob):
        if glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append("[^/]*")
            i += 1
        elif glob[i] == "\\" and i + 1 < len(glob):
            out.append(re.escape(glob[i + 1]))
            i += 2
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def main() -> int:
    """Return 0 when every tracked file matches exactly one annotation table, 1 otherwise (and log each offender)."""
    logging.basicConfig(level=os.environ.get("TAG_CLIP_LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s %(message)s")
    tables = tomllib.loads((REPO / "REUSE.toml").read_text())["annotations"]
    patterns: list[list[re.Pattern[str]]] = []
    for table in tables:
        paths = table["path"] if isinstance(table["path"], list) else [table["path"]]
        patterns.append([glob_to_regex(p) for p in paths])
    tracked = subprocess.run(["git", "ls-files"], cwd=REPO, check=True, capture_output=True, text=True).stdout.splitlines()
    bad = 0
    checked = 0
    for path in tracked:
        if IGNORED.match(path):
            continue
        checked += 1
        hits = [i for i, table in enumerate(patterns) if any(p.match(path) for p in table)]
        if len(hits) != 1:
            bad += 1
            log.error("%s matches %d annotation tables %s (needs exactly one)", path, len(hits), hits)
    log.info("checked %d tracked files against %d annotation tables: %d problems", checked, len(tables), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
