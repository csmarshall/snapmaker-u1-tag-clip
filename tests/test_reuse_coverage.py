"""The REUSE glob translation in tools/check_reuse_coverage.py, against cases where reuse 6.3.0's own matcher was checked by hand (PR #19 review)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_reuse_coverage", ROOT / "tools" / "check_reuse_coverage.py")
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

CASES = [
    ("*.md", "README.md", True),
    ("*.md", "docs/WORKFLOW.md", False),
    ("docs/**", "docs/images/hero.png", True),
    ("tools/*.py", "tools/build_prints.py", True),
    ("tools/*.py", "tools/fonts/x.py", False),
    ("**", "a/b/c", True),
    ("**/foo.py", "foo.py", True),
    ("**/foo.py", "a/b/foo.py", True),
    ("**/*.py", "x.py", True),
    ("a/**/b", "a/b", True),
    ("a/**/b", "a/x/y/b", True),
    ("a/**/b", "ab", False),
]


@pytest.mark.parametrize(("glob", "path", "expected"), CASES)
def test_glob_matches_like_reuse(glob: str, path: str, expected: bool) -> None:
    """Each case matches (or not) the way reuse 6.3.0 does."""
    assert bool(checker.glob_to_regex(glob).match(path)) is expected
