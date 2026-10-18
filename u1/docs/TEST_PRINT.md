# Test print plan

One plate, in PETG: `coin/out/u1_test_print.3mf` (built by `tools/make_3mf.py`). Bodies use filament 1 and inlays (label, digit, hint) filament 2. The blank cover has supports turned on, and nothing needs a pause. The file carries no printer settings: pick the Snapmaker U1 (0.4 nozzle) presets after opening.

There is no separate reader-range round. The coil is a loop about 126mm across around each socket (estimated from Snapmaker's photos, see `docs/ANTENNA.md`), and the sticker sits 28.6mm above the socket axis on the socket adapter, well inside it. The sticker is only the dock's 1.2mm back plate away from the panel, and the advice online is to keep the tag within 1 to 3cm. So the first read of a docked chip is the test. If it fails, the coil-finder puck and standoff strip in `fixtures/` are there to find out why.

| Print | File | Orientation and notes |
|---|---|---|
| Chip | `coin/out/chip_PETG.stl` (+ `_label`) | Back face down, no pause. Press the sticker into the recess in its back afterwards. |
| Dock | `coin/out/dock_slot1.stl` (+ `_accent`) | Standing on its bottom stop. |
| Dock mount | `coin/out/dock_mount.stl` | Upside down, on its arm ends. The crossbar bridges about 39mm. |
| Socket adapter | `coin/out/socket_adapter.stl` | Standing on its flat top. |
| Blank cover | `coin/out/cover_slot2.stl` (+ `_accent`) | Standing on its flat top, with slicer supports under the fingers. |

| Check | Pass | If not |
|---|---|---|
| **Read test:** chip docked on the socket adapter, `FILAMENT_DT_UPDATE CHANNEL=<0-3>` | Reads every time, 5 of 5 | map the coil with `fixtures/u1_coil_finder_puck.stl`; check plastic thickness with `fixtures/u1_standoff_strip.stl` (`DOCK_FLOOR`) |
| Sticker presses into the recess and stays below the back face | Flush or below, chip slides into the dock without catching | `POCKET_DEPTH`, `STICKER_CLEARANCE` |
| Chip slides into the dock from the top and seats on the key post; upside down it sits about 3mm high | Slides freely, no rattle | `FIT_CLEARANCE` |
| Hook finger catches a thumb and lifts the chip out | Comes out one-handed | `WALL_A_EXTRA_HEIGHT` |
| Dock mount slides down the socket adapter's slot | Slides in, no side play | `FIT_CLEARANCE` (slot) |
| Dock snaps into the mount's L clamps; tongues engage the grooves | Holds when the printer is bumped, comes out by hand | `MOUNT_JAW_REACH`, `MOUNT_TONGUE_TIP`, `MOUNT_ARM_WIDTH` |
| Socket adapter and blank cover snap into a socket | Like remmulegguh's original | finger geometry (traced, so this is unlikely) |
| Blank cover hides the bore | No gap visible from the front | `SOCKET_COVER_FLAT` (measure the real bore at the panel face: `SOCKET_BORE_DIAMETER`, 26.9mm assumed) |
| Cover's finger supports come off cleanly | Fingers undamaged | switch to designed-in breakaway ribs |

Report the results on issue #3 (the read) and a new fit-test issue.
