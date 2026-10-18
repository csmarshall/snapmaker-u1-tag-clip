# Finger spread sweep

The snap fingers on the blank cover (traced from remmulegguh's holder, `coin/socket_fingers.py`) printed loose in the socket in PETG. This sweep is how we find out how much wider they need to be, without guessing one number: six blank covers, identical except that the fingers' arms and hooks are moved outward by 0, 0.5, 1.0, 1.5, 2.0 and 2.5 mm per side. Each is engraved with its value (`+0.0` is the control, the traced fingers exactly), so you can push them into the socket one after another and feel which one holds. Issue 9 has the background.

`coin/out/u1_finger_spread.3mf` is built by `tools/make_spread_3mf.py` (the command is in the README) and writes nothing else. It is one PETG plate with no printer, process or filament settings, so pick the Snapmaker U1 0.4 nozzle presets after opening it. The covers are laid out as printed, flat top down on the bed with the fingers on slicer supports (the file turns supports on), in two rows of three with the control first. Print them all in one go so they share a spool and a bed.

## What the spread does

A spread of `s` moves every point of the finger outline that lies behind the root outward by `s * smoothstep(depth / 10 mm)`, so the arms are untouched at the root and fully shifted from 10 mm deep onward, with the hooks (depth about 27 to 30 mm) moved by exactly `s` per side. Points at the root (the 15 mm wide tab at depth 0.006 and the 0.3 mm that fuses with the plate) never move. Inner and outer faces of an arm move together, so the arm keeps its 2 mm thickness where it is fully shifted and the hook keeps its shape; only the gap between the arms and the overall width grow. The ramp is there so the arms bend out from the root instead of being sheared off it; its steepest slope is about 1.5 * s / 10, so 0.3 at the largest spread (about 17 degrees). The two constants are `ROOT_DEPTH` and `SPREAD_RAMP` in `coin/socket_fingers.py`, and the sweep values are `SPREADS` in `tools/make_spread_3mf.py`. `FINGER_OUTLINE` and `FINGER_HEIGHT` are not edited. In code, `cover_parts(slot, spread=FINGER_SPREAD, label=None)`, `dock_fingers_parts(slot, spread=FINGER_SPREAD)` and `_socket_fingers(axis_y, z_back, spread=FINGER_SPREAD)` take the spread, and passing 0 gives the traced fingers exactly. The sweep tool passes its values explicitly.

## Where interference starts, on paper

The socket bore is only known as 26.9 mm (1waynger1's plug width, assumed, not measured on the printer), so radius 13.45 mm. The fingers are 10 mm tall, so their top and bottom edges sit 5 mm off the axis, where the bore is only 12.49 mm from the axis (the chord). The hook's half-width and how it compares:

| spread (mm per side) | hook half-width | minus bore radius 13.45 | minus chord 12.49 at the finger edges |
| --- | --- | --- | --- |
| +0.0 | 11.009 | -2.44 | -1.48 |
| +0.5 | 11.509 | -1.94 | -0.98 |
| +1.0 | 12.009 | -1.44 | -0.48 |
| +1.5 | 12.509 | -0.94 | +0.02 |
| +2.0 | 13.009 | -0.44 | +0.52 |
| +2.5 | 13.509 | +0.06 | +1.02 |

Negative means the hook stays inside the bore. Read the last column as the first place the hook's corners would touch a perfectly round, 26.9 mm bore: from about +1.5 mm, and by +2.5 mm the hooks would reach past the bore's wall even on the axis. That interference is the point of the exercise, since the arms are meant to be squeezed inward by the wall, but the numbers say where the squeeze begins on paper, and the real bore decides where it does in practice. The script prints the same table when it runs.

## How to read it

Push each cover in, pull it out, and note which gives a grip you like: holds the panel up against a knock, but comes out without a fight. Start with the control to confirm it is loose, then go up. Pick the smallest spread that holds, not the largest that fits: more force also means harder removal and more load on the arm roots, and PETG that is flexed hard and often at a thin root can crack there. Watch the roots of the arms (about 5 mm in from the tab) on the tighter covers after a few insertions. If the tight ones crack or feel too strong, more walls and 100% infill make the arms stronger without changing the fit.

If none of the six is right, the answer is outside the range: the loosest that still feels loose says go further, the tightest that still feels slack says the same, and a cover that needs a tool to remove says a value in between. 

## The choice: +2.0 mm per side

Charles printed the sweep in PETG and chose +2.0 mm per side (2026-10-15). It is now `FINGER_SPREAD` in `coin/socket_fingers.py` and the default for every variant that carries the fingers: the socket adapter, the blank cover, the dock with fingers and the fallback finger piece (the integrated dock has no fingers). On paper +2.0 puts the hooks' corners 0.52 mm past the chord of an assumed 26.9 mm bore at the finger edges, so the wall squeezes the arms inward by roughly that much; the bore has still not been measured, so if it is, this is the number to revisit. Setting `FINGER_SPREAD = 0` brings back the traced fingers.

## The release bevel (dropped)

Charles tried the idea and dropped it on 2026-10-15: `FINGER_BEVEL` is 0, so nothing is cut, and the code and its tests stay so it can be set back to a value (1.5 was tried). What follows describes the machinery as built.

Charles also wanted the fingers to pop out of the socket when the part is turned left. Seen from the dock's front, looking into the printer, counter-clockwise is the positive rotation about the socket axis in the model's frame. That frame has X to the right, Y up and Z toward the viewer (X cross Y is +Z), the fingers reach back along -Z, so a viewer on +Z is the one at the front. A point at (x, y) turning counter-clockwise moves along (-y, x): the +X hook goes toward +Y and the -X hook toward -Y. So the corners that lead are the +X hook's top end (+Y) and the -X hook's bottom end (-Y), the pair a half turn about the axis exchanges. The test computes this from the mesh's own bevel faces (it checks the motion has a positive component along each face's outward normal, and a negative one on the mirror corners) rather than from a picture.

On those two corners only, a 45 degree wedge is cut where each hook's retaining step (the panel-facing face at depth 27.006, from the arm's outer side out to the hook's widest point, 1.087 mm tall in the trace) meets the end face. A hook turned left rides the bevelled face against the socket wall and is cammed inward. The leg is `FINGER_BEVEL` in `coin/socket_fingers.py` (1.5 mm, a tuned feel value, not derivable, set it to 0 to remove the bevel), but it is clipped to the step's height and to the finger height, so it is 1.087 mm today and raising `FINGER_BEVEL` does nothing until the step is taller. The wedge starts at the step's inner side, so the arms and the hooks' inner half are untouched, and the section at the fingers' mid-height is exactly the spread outline, which is why the trace check still holds. The wedge removes about 1.3 mm3 in all. The bevel faces sit at exactly 45 degrees, which the overhang rule (steeper than 45 degrees) does not count. As laid out for printing the supported overhang area changes by 0 mm2 on the socket adapter, by about -1.3 mm2 on the cover and by about -1.3 mm2 on the dock with fingers (the bevel replaces a flat overhang), so it adds no support. With the bevel dropped, the sweep covers and every other part carry none.

## What the checks cannot catch

`tests/test_finger_spread.py` checks that spread 0 reproduces the traced outline exactly (and, through the existing trace check in `tests/test_fit.py`, remmulegguh's own fingers within 2% by volume, which also fails for a +2.5 cover, so that check can see the offset), that the root points are identical for every spread, that the hooks widen by exactly the spread per side and no point moves by more than the spread, and that the six covers are valid solids that do not touch each other and sit on the bed. `tests/test_finger_bevel.py` checks the bevel's position, handedness, symmetry, mid-height section, removed volume and overhang the same way. All of that proves consistency with the outline and with itself. It does not prove fit: it knows nothing about the real socket width (the 26.9 mm is an assumption), how stiff PETG arms of this thickness are on your printer, how much the part shrinks as it cools (which changes the hook width by a few tenths of a millimetre either way), or how the supports leave the underside of the fingers. Only the printed sweep answers those. The "interference" figures above are geometry of a round bore, not a prediction of force. The bevel adds its own unknowns: nothing here shows that it makes a real hook release more easily from a real socket (the wall's shape and friction, and how the PETG hook flexes, decide that), and a hook that releases on a left turn may also release when it is not wanted to.
