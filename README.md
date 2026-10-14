# u1-rfid-chip-clip

A filament-clip "coin" that carries an NTAG215 sticker, plus a holder that snaps into the Snapmaker U1's side-panel spool-holder socket so the printer can read the tag without a spool holder attached. Made for feeding the U1 from an external dryer (a Creality SpacePi X4 here) with the paxx12 extended firmware and OpenRFID.

**Status: work in progress, nothing here has been printed or tested yet.** Treat every dimension as a first guess until it has been fitted on a real U1.

## The idea

Spools keep their tag with them. The tag lives on a coin that also clips the loose filament end, so there is no velcro and no separate chip to forget: to load a spool you take the coin off the spool, drop it into the holder on the printer, and feed the filament. When the print is done the coin goes back on the spool. The material name is engraved on the coin (deep enough to paint or fill) along with a copy number, and each coin's tag UID is registered in Spoolman through paxx12's OpenRFID support.

The U1 only reads a tag when the auto feeder first engages, so put the coin in the holder before feeding the filament.

## What is in the repo

| Path | What |
|---|---|
| `coin/u1_chip_clip.py` | Parametric build123d model of the chip (sticker pocket on the back, clip arms and engraved label on the front) and four numbered placeholder docks (U1 slots 1 to 4). All dimensions are named constants at the top. Run it with `uv run --with build123d python coin/u1_chip_clip.py`; output goes to `coin/out/` (not committed). |
| `fixtures/` | Test prints for finding where and through how much plastic the U1's reader still sees a sticker: a standoff strip (0.4 to 2.0mm floors) and a handled coin-finder puck. `fixtures/u1_fixtures.py` regenerates them. |
| `install_onshape_mcp.sh` | Optional helper that registers an Onshape MCP server for Claude Code (dry run by default). |
| `TOOLS-INSTALLED.md` | What was installed while working on this and how to remove it. |

## Parts and terms

| Term | What it is |
|---|---|
| chip | The clip coin: round end up, flat end down with rounded corners, sticker pocket on the back, engraved material name and copy number on the front. |
| clip arms | The three walls on the chip that hold the filament end, traced from Extrutim's clip and turned 180 degrees as one unit. |
| hook finger | The tallest clip arm (wall A, curled top and a small centre nub). Deliberately 2mm taller than the original (`WALL_A_EXTRA_HEIGHT`) so it stands proud of the dock's lower pocket and a thumb run up the pocket face catches it and lifts the chip out. |
| dock | The holder the chip drops into, one per U1 slot, numbered 1 to 4 left to right with a big engraved digit. |
| lower pocket | The wide plate and walls over the clip arms, at the flat end of the chip. Its top edge stops just past the hook finger; its side faces are closed. |
| channels | The straight side rails and lips (the tracks in the code) that guide the chip from the dock's open top. They run 7.5mm past the lower pocket's top edge (`TRACK_INTO_POCKET`) and stop; the bottom of the pocket has only its own walls. |
| back plate, bottom stop | The wall behind the chip (over the sticker) and the ledge the flat end rests on. |

With the side faces closed the filament cannot leave straight sideways; it leaves over the lower pocket's open top edge. `DOCK_FILAMENT_SLOTS` brings back narrow side slots.

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
