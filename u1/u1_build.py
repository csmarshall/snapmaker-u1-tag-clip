"""Build the U1-specific parts into u1/out: blank covers, the integrated dock, the dock with socket fingers, the dock mount, the socket adapter and the hub-adapter stand-in.

Needs the chip and generic dock built too (python chip/chip_clip.py) for the checks and print sheets, but does not read them. Run: python u1/u1_build.py
"""
import sys
from pathlib import Path

from OCP.BRepTools import BRepTools

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "chip"))  # the generic chip and dock live beside this folder
from build123d import export_step, export_stl  # noqa: E402
from chip_clip import U1_SLOTS  # noqa: E402
from u1_parts import (  # noqa: E402
    HUB_NEAR_END_UP,
    cover_parts,
    dock_fingers_parts,
    dock_integrated_parts,
    dock_mount_parts,
    hub_adapter_standin,
    socket_adapter_parts,
    sticker_above_axis,
)


def main() -> None:
    """Write every U1-specific STL (and STEP where the old build wrote one) into u1/out, then print the printing notes."""
    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)
    for slot in U1_SLOTS:
        cover = cover_parts(slot)
        for name, shape in cover.items():
            BRepTools.Clean_s(shape.wrapped)  # OCC keeps a triangulation on each face; clear it so every export meshes its own faces
            export_stl(shape, str(out / (f"cover_slot{slot}.stl" if name == "cover" else f"cover_slot{slot}_{name}.stl")))
    for slot in U1_SLOTS:
        integrated = dock_integrated_parts(slot)
        for name in ("dock", "accent"):
            BRepTools.Clean_s(integrated[name].wrapped)
            export_stl(integrated[name], str(out / (f"dock_integrated_slot{slot}.stl" if name == "dock" else f"dock_integrated_slot{slot}_{name}.stl")))
        export_step(integrated["dock"], str(out / f"dock_integrated_slot{slot}.step"))
    for slot in U1_SLOTS:
        with_fingers = dock_fingers_parts(slot)
        for name in ("dock", "accent"):
            BRepTools.Clean_s(with_fingers[name].wrapped)
            export_stl(with_fingers[name], str(out / (f"dock_fingers_slot{slot}.stl" if name == "dock" else f"dock_fingers_slot{slot}_{name}.stl")))
        export_step(with_fingers["dock"], str(out / f"dock_fingers_slot{slot}.step"))
    for name, shape in (("dock_mount", dock_mount_parts()["dock_mount"]), ("socket_adapter", socket_adapter_parts()["socket_adapter"])):
        export_stl(shape, str(out / f"{name}.stl"))
        export_step(shape, str(out / f"{name}.step"))
    export_stl(hub_adapter_standin()["hub_adapter"], str(out / "hub_adapter_standin.stl"))  # viewer and checks only
    print("integrated dock (dovetail built in, no mount): print lying on its side face, see u1/docs/INTEGRATED_DOCK.md")
    print("dock with socket fingers (no adapter): print standing on its bottom stop with supports under the fingers, see u1/docs/DOCK_FINGERS.md")
    print("dock mount: print upside down, standing on the ends of its arms; socket adapter: print standing on the plate's flat top and the fingers' top face; cover: print standing on the plate's flat top, with supports under the fingers")
    print(f"dock mount: the sticker sits {sticker_above_axis('socket'):.1f} mm above the socket axis on our socket adapter, {sticker_above_axis('hub'):.1f} mm on 1waynger1's hub adapter ({'near' if HUB_NEAR_END_UP else 'far'} end up)")


if __name__ == "__main__":
    main()
