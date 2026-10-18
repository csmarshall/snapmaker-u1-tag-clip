# Fallback: separately printed snap fingers (issue #6)

An independent test plate, not a replacement for the integral socket adapter. Use it if the integral adapter's snap fingers (the ones that go into the U1's spool-holder socket) turn out too stiff, too weak, or print badly in PETG. The adapter is split in two: a harness plate that stays outside the printer and carries the dock-mount slot, and a finger piece that prints on its own and joins the plate mechanically, so the fingers can be reprinted or swapped without reprinting the plate.

Build and check:

```
PYTHONPATH=coin uv run --with build123d python coin/finger_fallback.py
uv run --with build123d --with trimesh --with numpy --with matplotlib --with scipy --with networkx --with manifold3d --with rtree python tools/finger_fallback_plate.py
```

The first writes `coin/out/u1_finger_fallback_plate.stl` and `u1_finger_fallback_fingers.stl` (and STEP). The second picks each piece's print orientation, prints the overhang table, and writes `coin/out/u1_finger_fallback.3mf` (one plate, both pieces, filament 1; it carries no printer, process or filament settings, so choose the U1 0.4mm and PETG presets in Snapmaker Orca after opening). Nothing existing is touched: `coin/out/u1_test_print.3mf`, the PARTS and PLATES in `tools/print_plates.py` and the dock, adapter, cover and chip meshes build exactly as before.

## What the pieces are

The finger piece is remmulegguh's traced fingers, built by the very same `_socket_fingers` call the integral adapter uses, so it carries `FINGER_OUTLINE` and `FINGER_HEIGHT` (10mm, centred on the socket axis) unchanged, including the 0.3mm tab that his outline starts behind the panel face. On the front face of that tab it adds two dovetail tongues that reach into the plate. The tongues are 10mm long (the fingers' height), so the finger piece's top face sits flush with the plate's top edge exactly as the integral fingers do.

The harness plate is the integral adapter's plate with its outer envelope, corners and dock-mount slot untouched (the tests compare the bounding box and the front part of the section). Cut into its back face are a rebate for the tab and two dovetail grooves for the tongues. The grooves open at the plate's top edge and stop 10mm down, at the finger piece's bottom face. To assemble, slide the finger piece down the grooves from above until it stops; each tongue carries a cosine detent ridge on its front face that rides over the groove floor and drops into a dimple in it. Pulling the piece straight out (-Z) is blocked by the dovetail undercut, sideways by the flanks, down by the stop, and up by the ridges.

## Joint dimensions, and where they come from

Every dimension is derived; the constants that cannot be derived are named in `coin/finger_fallback.py` with a comment saying why.

| Dimension | Value | Derivation |
|---|---|---|
| Clearance on every sliding face | 0.30mm | `FIT_CLEARANCE`; the groove is the tongue grown by this on the floor and, square to each flank, on both flanks (45 degree flanks move sideways by 0.30 x root 2 = 0.42mm) |
| Tab rebate depth | 0.30 + 0.30mm | the trace's own tab thickness, read from `FINGER_OUTLINE`, plus the clearance |
| Tongue depth beyond the tab | 1.2mm | `ARM_WALL_THICKNESS`, as thick as the walls elsewhere on the model |
| Groove outer edge | 14.04mm from centre | plate half width less `ARM_WALL_THICKNESS` |
| Groove inner edge | 8.01mm from centre at the floor | found numerically so the groove keeps `ARM_WALL_THICKNESS` of plate from the dock mount's slot (measured square to the slot's slanting wall) |
| Tongue | 2.19mm wide at the neck, 4.59mm at the head | the groove less the clearance |
| Flank angle | 45 degrees | not derivable, see below |
| Detent ridge | 0.45mm high, 1.2mm half length, pressing 0.15mm into the floor | not derivable, see below |

Constants that could not be derived, each commented in the code: the flank angle (any lean locks the piece against pulling out; 45 degrees is a common dovetail that does not wedge in a sliding fit), the detent interference (`FIT_CLEARANCE / 2`, a stiffness guess for PETG, the one number I expect to change after the first print), the ridge's half length (a ramp gentle enough to push over; its steepest slope is 0.59, under the 45 degree print limit), and `BOOLEAN_OVERLAP` (0.1mm, only so the CAD union has no coincident faces; it adds no volume outside the part).

The dimple is the ridge's shape grown by the clearance in length and width and cut as deep as the ridge is tall, so the seated ridge has exactly the clearance of air around its tip.

## Print orientation

Chosen by the overhang check in `tools/print_orientation.py` and `tools/print_plates.py` (faces turned down more steeply than 45 degrees and not on the bed), tried for each of the six faces of the piece's bounding box. Both pieces are PETG. Area over the limit, mm2:

| Face down | Harness plate | Finger piece |
|---|---|---|
| Top edge (+Y) | 56.7 | 0.0 (chosen, 10.0 tall) |
| Bottom edge (-Y) | 32.4 (chosen, 42.9 tall) | 0.0 |
| Back face (-Z) | 796.6 | 296.8 |
| Front (+Z) | 829.3 | 409.0 |
| Side (+X) | 82.4 | 604.7 |
| Side (-X) | 81.6 | 604.7 |

The finger piece stands on the end of its extrusion, so the fingers, tongues and ridges are all straight vertical shapes with no support. The two ends tie at zero, and the 3MF uses the top edge, which is the integral adapter's orientation and so the strong in-layer direction for the fingers. The plate prints on its bottom edge, not its top edge as the integral adapter does: with the top edge down the grooves' stop faces become 10mm-high bridges, so the 56.7 mm2 includes them, while with the bottom edge down the grooves open upward and the 32.4 mm2 left is the rounded corners' first millimetre, the same kind of overhang the integral adapter shows (31.2 mm2 on its top edge). Only the six face-down orientations were tried, not tilted ones.

## What this does not fix, and what to watch

The finger piece's neck is 2.19mm wide and 10mm long, which is the weak point of the joint; the integral fingers have no such neck. That is the price of keeping the joint clear of the dock mount's slot, which occupies the middle of the plate. The same constraint is why there are two tongues rather than one wide one.

The rebate for the 0.3mm tab cuts across the full width, including behind the dock mount's slot, where the plate's back wall was 1.23mm and is now 0.63mm over a 30mm by 10mm patch. The mount's tongue does not bear on it (it keeps 0.3mm clear of the slot's back), but it is thinner than the integral adapter. If it flexes or cracks in PETG, the way out is to trim the tab where it crosses the slot, which would leave the traced fingers themselves unchanged but would be a change to the traced outline's tab, so it needs a decision.

The joint adds stack-up: the finger piece can float up to the clearance in each direction until the dovetail flanks and the ridges take up the slack.

## What the tests do and do not prove

`tests/test_finger_fallback.py` builds the pieces from the model and checks that: the finger piece's section through the fingers' mid-height equals `FINGER_OUTLINE` and matches the integral adapter's fingers, with height and centring per `FINGER_HEIGHT`; the plate keeps the integral plate's envelope and slot; the grooves keep their walls from the slot and plate edge; seated, the pieces share no volume, the top faces are flush, and the gap in cross-sections through the joint is `FIT_CLEARANCE` everywhere, ridge tip included; the finger piece seats on the stop, cannot be pulled out or moved sideways without hitting the flanks; the ridge is proud of the groove floor by the interference, is clear in its dimple, and must be pushed over when the piece slides up; and the chosen orientations have the least overhang.

These checks derive both sides of every comparison from the same constants (`FIT_CLEARANCE`, the traced outline, the adapter's dimensions), so they prove consistency, not fit. They cannot catch: PETG shrinkage or elephant's foot changing the real clearance, whether 0.3mm is a sliding fit or too loose on this printer, whether the detent's 0.15mm interference gives a usable click or is too stiff or too slack, whether the 2.19mm neck survives use, or whether the traced fingers themselves are right in the real socket (the trace is the independent evidence for that, and this split keeps it as is). The one independent check is the trace comparison: the outline comes from remmulegguh's file, not from this code.

Report the first print's results on issue #6.
