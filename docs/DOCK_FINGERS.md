# Dock with the socket fingers on its back

Issue #8: Charles asked whether the snap fingers could attach directly to the back of the dock, so the sticker sits where the centre of a spool normally is, with no adapter, slot, dovetail or mount. `dock_fingers_parts(slot)` in `coin/u1_chip_clip.py` is that part (`dock_fingers_slotN.stl` for N = 1 to 4, with `dock_fingers_slotN_accent.stl` for the digit and hint). It is an experiment: build and print it only once a zero-print test (a sticker taped to a blank cover, centred, in slot 1) has shown the tag reads there. The existing dock, the integrated dock, the adapters and the test-print plate are untouched.

## What it is

The dock is `dock_parts(slot, mount_grooves=False)` (full rails, as in the integrated dock) with `_socket_fingers(STICKER_CENTRE_Y, z_back)` added, using remmulegguh's traced `FINGER_OUTLINE` and `FINGER_HEIGHT` exactly as the cover and socket adapter do. `z_back` is the dock's own back face, which is the panel plane in every variant, and the fingers' axis passes through the chip frame's origin, which is the centre of the sticker recess. So the sticker is on the socket axis (x = 0, y = 0).

## Where the sticker is

The chip's back face is `DOCK_BACK_GAP + DOCK_FLOOR` = 1.5 mm from the panel plane, and the sticker sits in a 0.6 mm recess in that face, so its back is 1.5 to 1.7 mm and its centre about 1.7 to 1.9 mm from the panel plane (the sticker is assumed 0.4 mm thick). That is the same distance as in the adapter variants: there too the dock's back plate lies on the panel plane and the adapter is below it. What differs is sideways: the sticker is on the axis here, and 28.6 mm above it on our socket adapter (43.0 mm on 1waynger1's hub adapter with its near end up). The 3 to 5 mm and 10 mm figures in issue #8 were for a sticker behind a socket plate or an adapter plate; neither plate is between the sticker and the panel here.

## Does anything collide

Nothing of the dock lies behind the panel plane (the back plate's back face is at it), so no funnel, channel, lower pocket, bottom stop or key post can meet the fingers' 30 mm slab. The fingers' 0.3 mm tab, which spans 30 mm across and 10 mm tall at the panel face, is buried in the back plate: the plate is solid across the whole tab (the hint's recess is only 0.6 mm deep from the front face, so it stops short of the tab's 0.3 mm), which is what fuses the fingers to it. The outline in front of the tab reaches at most about 11 mm sideways, so with the fingers' 10 mm height it stays inside the socket's 26.9 mm bore; the tab is wider than the bore, so it sits on the panel face around it. The back plate covers the bore's whole disc (the bore's top edge reaches the start of the funnel at y = 13, where the plate is still thicker than 0.4 mm). All of this is checked in `tests/test_dock_fingers.py`.

## Print orientation

Overhang is the area of faces facing down more than 45 degrees and not on the bed, by the rule in `tools/print_orientation.py` and `tools/print_plates.py`. Slot 1; "fingers" is the part of it on the fingers behind the panel plane.

| Orientation | Overhang | Fingers | Notes |
| --- | --- | --- | --- |
| Standing on the bottom stop, fingers sticking back | 172 mm2 | 154 | 336 mm2 on the bed; the fingers' outline lies in the layer plane, so their flex direction is along the layers (strong); the fingers' flat underside, 15 mm above the bed, needs support |
| Standing on the top rim | 434 mm2 | 154 | 27 mm2 of rim on the bed; not viable |
| Lying on a side face | 794 mm2 | 580 | the fingers' flex direction is across the layers (weak) and their curves overhang |
| Lying on its front, fingers up | 1505 mm2 | 69 | the dock's own channels and lips overhang; fingers print across the layers |
| Lying on its back | 1970 mm2 | 276 | fingers would point into the bed; not viable |
| Standing on the stop, tilted 15 to 30 degrees about X | about 500 mm2 | 154 | no flat contact with the bed |
| Standing on the stop, tilted 45 degrees about X | 92 mm2 | 82 | the numbers look good but it rests on a line, not a face; not viable without a lot of support |

Recommended: standing on the bottom stop with the fingers sticking back, as the plain dock stands. The dock itself adds only 18 mm2 of overhang (the plain dock's own 22 mm2 less the grooves), and the only part that needs support is the fingers' underside, 154 mm2 of build-plate-only support under a flat face about 15 mm up. Prints in that orientation keep the fingers' outline in the layer plane, which is their strong direction for flexing in the socket; the 3MF turns on build-plate-only support for the part. PETG on a cantilever of this size is likely to want a brim: the footprint is 336 mm2 and the fingers hang 30 mm behind it. The support will leave a rougher face on the fingers' flat underside, so clean it before first fitting.

## One-plate project

`python tools/make_3mf.py --fingers` writes `coin/out/u1_dock_fingers.3mf`: slot 1, as laid out for printing, body on filament 1, digit and hint on filament 2, titled PETG, no printer, process or filament presets (pick the U1 0.4 mm PETG presets in Snapmaker Orca after opening). Without the flag the script writes the existing test print exactly as before. Run the build (`python coin/u1_chip_clip.py`) first.

## What this variant cannot check

Whether the sticker reads at the loop's centre is not known: the coil size (about 126 mm across) is estimated from a tilted photo scaled against an assumed boss diameter, and nobody has published a read at the centre (issue #8, `docs/ANTENNA.md`); the sticker's 1.5 to 1.9 mm from the panel is comfortably inside the advised 1 to 3 cm, but a read at the very centre of the loop is exactly the untested thing. The tests also derive both sides of most comparisons from the same constants, so they prove consistency with the script's own parameters, not fit: the one independent check is the fingers against remmulegguh's own holder, run only when his file is present locally. Whether the fingers snap into a real socket, how PETG layer adhesion holds the fingers when flexed, and whether the chip is reachable by hand with a spool on a neighbouring slot are for a print to show.
