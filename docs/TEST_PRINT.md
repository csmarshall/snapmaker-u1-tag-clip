# Test print plan

Two rounds. Round 1 answers where the reader sees a sticker, and through how much plastic (issue #3). Round 2 depends on those answers, so print it after round 1. Each check names the constant its result changes.

## Round 1: reader range (issue #3)

Print both in PLA. They need no supports or pauses: the sticker drops in from the top.

Both rounds are in one project, `coin/out/u1_test_print.3mf` (`tools/make_3mf.py`): plate 1 is round 1, plate 2 is round 2. Inlays use filament 2, the blank cover has supports turned on, and the chip has the sticker pause. It carries no printer settings: pick the U1 0.4mm presets after opening, with a 0.2mm first layer so a layer starts exactly at 1.20mm.

| Print | File | Notes |
|---|---|---|
| Standoff strip | `fixtures/u1_standoff_strip.stl` | Five pockets with floors of 0.4, 0.8, 1.2, 1.6 and 2.0mm. |
| Coil-finder puck | `fixtures/u1_coil_finder_puck.stl` | A 0.6mm floor, a handle, and a mark hole at the sticker centre. |

For each check, write a tag with the app, put it in the fixture, hold the fixture floor-down against the outside of the side panel, and run `FILAMENT_DT_UPDATE CHANNEL=<0-3>`.

1. **Coil map:** slide the puck around the socket. Mark each spot where it reads through the hole with a pencil. Note the highest and lowest reading spots above the socket axis, and whether the axis itself (0mm) reads. The axis result decides whether the chip-in-cover variant is worth building.
2. **Standoff:** at the best spot from step 1, try each strip pocket. Note the thickest floor that still reads. Then try 20 to 30mm above the axis as well, since our socket adapter puts the sticker at 28.6mm.
3. **Bore:** measure the socket bore at the panel face with calipers, both across and up and down. The model uses 26.9mm (1waynger1's plug, a lower bound).

| Result | Sets |
|---|---|
| Read band above the axis | `sticker_above_axis` placement; whether 43 to 47mm (his hub adapter) reads at all |
| Thickest floor that reads | `DOCK_FLOOR`, `BACK_SKIN` |
| Axis reads at 0mm? | chip-in-cover variant: build it or drop it |
| Real bore | `SOCKET_BORE_DIAMETER` |

## Round 2: fit set

Print these after round 1 has set `DOCK_FLOOR`, and rebuild first: `uv run --with build123d python coin/u1_chip_clip.py`.

| Print | File | Orientation and notes |
|---|---|---|
| Chip | `coin/out/chip_PETG.stl` (+ `_label`) | Back face down. Pause at 1.20mm to drop in the sticker. |
| Dock | `coin/out/dock_slot1.stl` (+ `_accent`) | Standing on its bottom stop. |
| Dock mount | `coin/out/dock_mount.stl` | Upside down, on its arm ends. The crossbar bridges about 39mm. |
| Socket adapter | `coin/out/socket_adapter.stl` | Standing on its flat top. |
| Blank cover | `coin/out/cover_slot2.stl` (+ `_accent`) | Standing on its flat top, with slicer supports under the fingers. |

| Check | Pass | If not |
|---|---|---|
| Chip slides into the dock from the top and seats on the key post; upside down it sits about 3mm high | Slides freely, no rattle | `FIT_CLEARANCE` |
| Hook finger catches a thumb and lifts the chip out | Comes out one-handed | `WALL_A_EXTRA_HEIGHT` |
| Dock mount slides down the socket adapter's slot | Slides in, no side play | `FIT_CLEARANCE` (slot) |
| Dock snaps into the mount's L clamps; tongues engage the grooves | Holds when the printer is bumped, comes out by hand | `MOUNT_JAW_REACH`, `MOUNT_TONGUE_TIP`, `MOUNT_ARM_WIDTH` |
| Socket adapter and blank cover snap into a socket | Like remmulegguh's original | finger geometry (traced, so this is unlikely) |
| Blank cover hides the bore | No gap visible from the front | `SOCKET_COVER_FLAT` |
| Cover's finger supports come off cleanly | Fingers undamaged | switch to designed-in breakaway ribs |
| **Read test:** docked chip, `FILAMENT_DT_UPDATE` on that channel | Reads every time, 5 of 5 | sticker placement or `DOCK_FLOOR` |

Report the results on issue #3 (round 1) and on a new fit-test issue (round 2).
