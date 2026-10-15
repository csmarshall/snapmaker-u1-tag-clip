# u1-rfid-chip-clip

A filament-clip "coin" that carries an NTAG215 sticker, plus a holder that snaps into the Snapmaker U1's side-panel spool-holder socket so the printer can read the tag without a spool holder attached. Made for feeding the U1 from an external dryer (a Creality SpacePi X4 here) with the paxx12 extended firmware and OpenRFID.

**Status: work in progress, nothing here has been printed or tested yet.** Treat every dimension as a first guess until it has been fitted on a real U1.

## The idea

Spools keep their tag with them. The tag lives on a coin that also clips the loose filament end, so there is no velcro and no separate chip to forget: to load a spool you take the coin off the spool, drop it into the holder on the printer, and feed the filament. When the print is done the coin goes back on the spool. The material name is engraved on the coin (deep enough to paint or fill) and nothing else (chips travel with spools and can end up in any position, so no copy numbers), and each coin's tag UID is registered in Spoolman through paxx12's OpenRFID support.

The U1 only reads a tag when the auto feeder first engages, so put the coin in the holder before feeding the filament.

## What is in the repo

| Path | What |
|---|---|
| `coin/u1_chip_clip.py` | Parametric build123d model of the chip (sealed sticker pocket, clip arms and engraved label) and four numbered docks (U1 slots 1 to 4), each exported whole and as named parts. All dimensions are named constants at the top. Output goes to `coin/out/` (not committed). |
| `tests/test_fit.py` | Fit and consistency checks on the built files, plus a comparison of the clip with Extrutim's original (skipped when that file is absent). |
| `tools/build_preview.py`, `tools/preview/` | Stages the rotatable 3D review page and its meshes in `coin/out/preview/` for publishing as an artifact. |
| `docs/ANTENNA.md` | Where the U1's reader probably sees a sticker, worked out from earlier tag holders (an estimate until measured). |
| `fixtures/` | Test prints for finding where and through how much plastic the U1's reader still sees a sticker: a standoff strip (0.4 to 2.0mm floors) and a handled coin-finder puck. `fixtures/u1_fixtures.py` regenerates them. |
| `install_onshape_mcp.sh` | Optional helper that registers an Onshape MCP server for Claude Code (dry run by default). |
| `TOOLS-INSTALLED.md` | What was installed while working on this and how to remove it. |

## Build, check, preview

```sh
uv run --with build123d python coin/u1_chip_clip.py
uv run --with build123d --with trimesh --with manifold3d --with pytest --with rtree --with shapely --with networkx --with scipy python -m pytest -q tests
uv run python tools/build_preview.py
uv run --with build123d --with trimesh --with numpy --with matplotlib --with scipy --with networkx python tools/print_plates.py  # test-print plates, see docs/TEST_PRINT.md
```

## Printing

- **Chip:** back face down. Pause at the layer that starts at 1.20mm (`PAUSE_HEIGHT`), drop the sticker into its pocket, resume. For two colours, load `chip_<material>.stl` and `chip_<material>_label.stl` together as one object.
- **Dock:** stand it on its bottom stop (flat end down) so nothing bridges. The same `dock_slot<n>` either tapes to the panel over the antenna with VHB, or pushes into the dock mount. For two colours, load `dock_slot<n>.stl` (body) with `dock_slot<n>_accent.stl` (the slot digit and the orientation hint, inlaid flush).
- **Dock mount** (`dock_mount.stl`): print upside down, standing on the ends of its arms; the crossbar bridges about 39mm between them.
- **Socket adapter** (`socket_adapter.stl`): print standing on the plate's flat top and the fingers' top face. **Blank cover** (`cover_slot<n>.stl` plus `_accent` for the digit): print standing on the plate's flat top, with supports under the fingers; its plate is round almost to the top so it hides the whole socket bore. Both snap into a spool-holder socket with remmulegguh's fingers. `hub_adapter_standin.stl` only stands in for 1waynger1's base in the viewer and checks; it is not a print.
- Every sliding gap derives from `FIT_CLEARANCE` (0.3mm). Change that one number after a fit test.

## Parts and terms

| Term | What it is |
|---|---|
| chip | The clip coin: round end up, flat end down with rounded corners and a centre key notch, sticker sealed inside, engraved material name only on the front. |
| clip arms | The three walls on the chip that hold the filament end, traced from Extrutim's clip and turned 180 degrees as one unit. |
| hook finger | The tallest clip arm (wall A, curled top and a small centre nub). Deliberately 2mm taller than the original (`WALL_A_EXTRA_HEIGHT`) so it stands proud of the dock's lower pocket and a thumb run up the pocket face catches it and lifts the chip out. |
| dock | The holder the chip drops into, one per U1 slot, numbered 1 to 4 left to right with a big engraved digit. |
| lower pocket | The wide plate and walls over the clip arms, at the flat end of the chip. Its top edge stops just past the hook finger; its side faces are closed. |
| channels | The straight side rails and lips (the tracks in the code) that guide the chip from the dock's open top. They run 7.5mm past the lower pocket's top edge (`TRACK_INTO_POCKET`) and stop; the bottom of the pocket has only its own walls. |
| back plate, bottom stop | The wall behind the chip (over the sticker) and the full-depth ledge the flat end rests on, which closes the lower pocket at the bottom. |
| dock mount | Slides down into an adapter's slot from above. A crossbar rests on the adapter's top edge and the dock stands on it, held by L clamps (side wall, front jaw, tongue in the side groove) on its middle band. Fits our socket adapter and 1waynger1's hub adapter alike. |
| socket adapter | Ours: remmulegguh's snap fingers behind a plate carrying a copy of 1waynger1's slot, so the dock mount fits it. Sticker 28.6mm above the socket axis. |
| hub adapter | 1waynger1's base (MakerWorld 2152529), for owners who already run it in place of his spool arm. Sticker 43.0mm above the axis (47.2mm if fitted the other way up). |
| grip band, grooves | The middle of the dock's sides: what is left of its length once the lower pocket's height is taken off both ends (6.64mm), centred on the dock. A groove in each side there takes the hanger's tongue. |
| blank cover | The snap fingers and a round plate with the slot number, for an unused socket. |
| key post | A 3mm post on the bottom stop that fits the notch between the chip's 4mm feet. Put in upside down, the chip's round end lands on it and sits about 3mm high. |
| funnel | The flared mouth on top of the channels. All walls end on one flat top rim. |

The clip is empty while the chip is docked (the filament end has gone into the feeder), so the lower pocket's sides are closed.

## Open questions

- How remmulegguh's holder is oriented when mounted, which decides where the coin dock attaches to his snap fingers and plate.
- The real tag position and the plastic thickness the reader tolerates (the fixtures exist to answer this).
- Whether the clip arms grip 1.75mm filament as well as the original clip.

## Credits and licence

This project is licensed CC BY-NC-SA 4.0 (see `LICENSE`) because it builds on CC BY-NC-SA work. Non-commercial use only, share alike, attribution required.

- The clip arms are a close trace of Extrutim's [Filament Clip, Grandma's Favorite](https://www.printables.com/model/24371-filament-clip-grandmas-favorite-filament-clip) (Printables 24371), with the hook finger made 2mm taller. See `SOURCES.md` for how.
- The snap-in holder follows remmulegguh's [Snapmaker U1 NFC / RFID Tag Holder](https://www.printables.com/model/1625982-snapmaker-u1-nfc-rfid-tag-holder) (Printables 1625982).
- The sticker-coin and per-material chip idea follows A-Jey's [Snapmaker U1 RFID Adapter & Chip System](https://www.thingiverse.com/thing:7268905) (Thingiverse 7268905), and krokus57's [remix](https://www.thingiverse.com/thing:7324691).
- Firmware: [paxx12's SnapmakerU1-Extended-Firmware](https://github.com/paxx12/SnapmakerU1-Extended-Firmware) and [OpenRFID](https://github.com/suchmememanyskill/OpenRFID).

The original authors' files are not redistributed here.

## How it was made

Human-crafted and AI-assisted, human-directed: the design decisions are Charles's, and the geometry and scripts were drafted with Claude Code and reviewed along the way.
