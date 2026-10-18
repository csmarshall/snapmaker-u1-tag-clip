"""Shared setup for the U1 tests: the import paths, M (the chip model, the traced fingers and the U1 parts as one namespace, as the tests always used them) and helpers that find built meshes in u1/out or chip/out."""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import trimesh

ROOT = Path(__file__).resolve().parents[2]
U1_OUT = ROOT / "u1" / "out"
CHIP_OUT = ROOT / "chip" / "out"
for sub in ("tests", "chip", "u1", "u1/tools"):
    sys.path.insert(0, str(ROOT / sub))

import chip_clip  # noqa: E402
import socket_fingers  # noqa: E402
import u1_parts  # noqa: E402
from test_fit import _overlap, _turned  # noqa: E402,F401  (the chip tests' helpers, shared)

M = SimpleNamespace(**{**vars(chip_clip), **vars(socket_fingers), **vars(u1_parts)})


def _mesh(name: str) -> trimesh.Trimesh:
    """A built mesh: the U1 parts are in u1/out, the chips and generic docks in chip/out."""
    for folder in (U1_OUT, CHIP_OUT):
        if (folder / name).exists():
            return trimesh.load(folder / name, force="mesh")
    pytest.skip(f"{name} missing from u1/out and chip/out: run the builds first")
