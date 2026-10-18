# Integrated dock (dovetail built in)

The first PETG test print showed the Y-shaped dock mount is the hard part: it prints upside down on its arm ends with a 39 mm crossbar bridge that strung, its arms only just hold the dock when it faces up, and the dock falls out when it faces down. The integrated dock drops the mount. It is the existing dock, unchanged, with the adapter's dovetail built onto its bottom end, so it slides straight down into the slot on either adapter (1waynger1's hub adapter or our socket adapter; the slot is the same). It is an extra variant (`dock_integrated_slotN.stl`, N = 1 to 4, with `dock_integrated_slotN_accent.stl` for the digit and hint) until a print proves it; the dock, mount, adapters and test-print plate are untouched. Issue #7 has the reasons.

## What was added

`dock_integrated_parts(slot)` in `u1/u1_parts.py` returns `dock_parts(slot, mount_grooves=False)` plus a stem. The grooves are the dock mount's grip in each side face of the back plate and channels; with no mount they are dropped, so the integrated dock keeps its full 3 mm rails (the shoulder, which is the same 3 mm, lines up with them). `dock_parts(slot)` itself still cuts them by default, and every existing output is byte-identical. Otherwise the body, channels, funnel, pocket, slot digit, hint and sticker position are the existing ones (the tests check that the integrated part above the dock's bottom end is the groove-free dock, volume and overlap, for all four slots, and that the existing dock lies wholly inside it). The stem has two sections. A shoulder spans the `FIT_CLEARANCE + MOUNT_RISER` gap the mount's crossbar fills, from the dock's bottom end down to the adapter's top edge: the slot's section grown by `INTEGRATED_SHOULDER` and clipped to the adapter plate's outline (so nothing reaches behind the panel plane or in front of the plate's front face). Below it, the tongue is `_slot_section(FIT_CLEARANCE)`, the slot's own section less the fit clearance all round, for `MOUNT_TONGUE_LENGTH`, exactly as the mount's tongue is built.

## Does it rest or hang

It rests. The shoulder is wider than the slot, so its underside sits on the adapter's top edge, in the same place the mount's crossbar does, with the dock's bottom end `FIT_CLEARANCE + MOUNT_RISER` above it. The adapter frame is unchanged, so the sticker stays 28.6 mm above the socket axis on our adapter (43.0 mm on the hub adapter, with its near end up), and the back plate keeps its 1.2 mm (`DOCK_FLOOR`) in the same place, its back face on the panel plane and the chip 0.3 mm (`DOCK_BACK_GAP`) in front of it; the stem is clipped at that plane and the test checks the whole part's back is unchanged. Gravity seats it and the dovetail stops sideways and outward movement; it lifts straight out. There is no detent: nothing in the existing constants says how much interference a snap should have, and a made-up bump would be a tuned number to re-measure, so it was left out. If a print shows the dock rattling or lifting, a detent is the next step, with its depth taken from that print.

`INTEGRATED_SHOULDER` (3 mm, the dock's own rail width) is the one number that is not derived: it only has to leave a ring of bearing on the plate's top edge, and it is kept narrow so that ring is a short bridge when printing.

## Print orientation

Overhang is the area of faces facing down more steeply than 45 degrees and not on the bed, by the rule in `u1/tools/print_orientation.py` and `u1/tools/print_plates.py`. Measured on slot 1; "stem" is the part of that area on the stem and tongue, "dock" the rest (the dock's own features, which the old dock avoided by standing on its bottom stop).

| Orientation | Overhang | of which stem | Notes |
| --- | --- | --- | --- |
| Standing on the tongue's end | 275 mm2 | 257 | 70.6 mm tall on a 79 mm2 footprint; the section is in the layer plane (best dovetail accuracy) but it is tippy; the shelf is the dock's bottom face outside the shoulder |
| Standing on the dock's top rim | 280 mm2 | | 27 mm2 of rim on the bed; not viable |
| Lying on its back | 1137 mm2 | 583 | stable (1497 mm2 on the bed) but the dovetail's back-side flank is 30 degrees from flat and the dock's funnel overhangs |
| Lying on its front | 1836 mm2 | | worst |
| Lying on a side face (either) | 222 mm2 | 8 | 252 mm2 of side face on the bed, 38.6 mm tall |
| Lying on its back, tilted 10 to 45 degrees about either axis | about 790 to 2650 mm2 (measured with the grooves still in) | | never better than side |

Recommended: lying on a side face (`ON_SIDE` in `u1/tools/print_plates.py`). The stem and tongue add 8 mm2 of overhang; the remaining 214 mm2 is the dock's own detail (the largest piece is the roof of each channel, about 6 by 31 mm, a 6 mm span) and is what the old dock avoided by standing on its stop. The cost is a thin tall part (8.7 mm wide, 38.6 mm tall, 70.6 mm long), so use a brim; the dovetail's flanks are stair-stepped rather than in the layer plane, so if the fit is tight in PETG, tongue-end-down (with a brim, a tall part on a small footprint) is the alternative that prints the section most accurately. The integrated dock has no mount grooves, so its whole side face (252 mm2 of it, the rest being the open channel) is on the bed.

## One-plate project

`uv run ... python u1/tools/make_3mf.py --integrated` writes `u1/out/u1_dock_integrated.3mf`: slot 1, laid out as printed on its side, body on filament 1 and the digit and hint on filament 2, titled PETG, with no printer, process or filament presets (pick the U1 0.4 mm PETG presets in Snapmaker Orca after opening). Without the flag the script writes the existing test-print project exactly as before. Run the build (`python u1/u1_parts.py`) first.

## What the checks cannot catch

The tests in `u1/tests/test_integrated_dock.py` derive both sides from the same constants (the stem from `_slot_section`, the adapters from the same profile), so they show the part agrees with its own parameters: no interference lowering into either adapter, the dock cannot drop or move sideways, the added geometry is only below the dock, and the tongue is the slot less `FIT_CLEARANCE`. The one independent check is the hub adapter test against 1waynger1's real mesh when it is present locally (it is not redistributed). None of it shows how PETG shrinkage, first-layer squash on a tall thin part, or the hub adapter's real tolerances change the fit: that needs a print.
