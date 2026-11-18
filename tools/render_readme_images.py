"""Render the README's picture, docs/images/hero.png: a PLA+ chip on its own, and the same chip sitting in the slot 1 finger dock.

Reads the built meshes in chip/out and u1/out (run tools/build_prints.py first) and renders off screen with PyVista (VTK).
Run: uv run --group render python tools/render_readme_images.py
"""
from pathlib import Path

import pyvista as pv

ROOT = Path(__file__).resolve().parents[1]  # the repository root
CHIP_OUT = ROOT / "chip" / "out"
U1_OUT = ROOT / "u1" / "out"
OUT = ROOT / "docs" / "images" / "hero.png"
CHIP_STEM = "tag-clip_PLAplus"  # the chip shown
BODY_COLOUR = "#ecebe6"  # filament 1, off-white
INLAY_COLOUR = "#d9541a"  # filament 2, orange
DOCK_COLOUR = "#3a3f47"  # dock, dark grey PETG
# Chip frame: +Z is the front face (name, clip arms), +Y the round end, and the dock's fingers point to -Z. Look at the front from above and to the right.
CAMERA_DIRECTION = (0.55, -0.45, 1.0)
CAMERA_UP = (0.0, 1.0, 0.0)
PANEL_PX = (900, 820)  # each of the two panels


def _load(path: Path) -> pv.PolyData:
    """Load one STL, naming the build step if it is missing."""
    if not path.exists():
        raise SystemExit(f"missing {path}: run tools/build_prints.py first")
    return pv.read(str(path))


def _panel(plotter: pv.Plotter, parts: list[tuple[pv.PolyData, str]]) -> None:
    """Add the parts to the current panel and aim its camera at them."""
    for mesh, colour in parts:
        plotter.add_mesh(mesh, color=colour, smooth_shading=False, specular=0.15, ambient=0.25)
    plotter.camera_position = "xy"
    plotter.camera.position = tuple(c * 100 for c in CAMERA_DIRECTION)
    plotter.camera.focal_point = (0.0, 0.0, 0.0)
    plotter.camera.up = CAMERA_UP
    plotter.reset_camera()
    plotter.camera.zoom(1.15)


def main() -> None:
    """Write docs/images/hero.png."""
    chip = [(_load(CHIP_OUT / f"{CHIP_STEM}.stl"), BODY_COLOUR), (_load(CHIP_OUT / f"{CHIP_STEM}_label.stl"), INLAY_COLOUR)]
    dock = [(_load(U1_OUT / "dock_fingers_slot1.stl"), DOCK_COLOUR), (_load(U1_OUT / "dock_fingers_slot1_accent.stl"), INLAY_COLOUR)]
    plotter = pv.Plotter(shape=(1, 2), off_screen=True, window_size=(2 * PANEL_PX[0], PANEL_PX[1]), border=False)
    plotter.set_background("white")
    plotter.subplot(0, 0)
    _panel(plotter, chip)
    plotter.subplot(0, 1)
    _panel(plotter, dock + chip)  # the dock is built in the chip's frame, so the chip lands docked
    OUT.parent.mkdir(parents=True, exist_ok=True)
    plotter.screenshot(str(OUT))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
