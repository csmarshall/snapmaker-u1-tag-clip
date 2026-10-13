# u1-rfid-chip-clip

A filament-clip "coin" that carries an NTAG215 sticker, plus a holder that snaps into the Snapmaker U1's side-panel spool-holder socket so the printer can read the tag without a spool holder attached. Made for feeding the U1 from an external dryer (a Creality SpacePi X4 here) with the paxx12 extended firmware and OpenRFID.

**Status: work in progress, nothing here has been printed or tested yet.** Treat every dimension as a first guess until it has been fitted on a real U1.

## The idea

Spools keep their tag with them. The tag lives on a coin that also clips the loose filament end, so there is no velcro and no separate chip to forget: to load a spool you take the coin off the spool, drop it into the holder on the printer, and feed the filament. When the print is done the coin goes back on the spool. The material name is engraved on the coin (deep enough to paint or fill) along with a copy number, and each coin's tag UID is registered in Spoolman through paxx12's OpenRFID support.

The U1 only reads a tag when the auto feeder first engages, so put the coin in the holder before feeding the filament.

## What is in the repo

| Path | What |
|---|---|
| `coin/u1_chip_clip.py` | Parametric build123d model of the clip coin (sticker pocket on the back, clip arms and engraved label on the front) and a placeholder dock. All dimensions are named constants at the top. |
| `fixtures/` | Test prints for finding where and through how much plastic the U1's reader still sees a sticker: a standoff strip (0.4 to 2.0mm floors) and a handled coin-finder puck. `fixtures/u1_fixtures.py` regenerates them. |
| `install_onshape_mcp.sh` | Optional helper that registers an Onshape MCP server for Claude Code (dry run by default). |
| `TOOLS-INSTALLED.md` | What was installed while working on this and how to remove it. |

## Open questions

- How remmulegguh's holder is oriented when mounted, which decides where the coin dock attaches to his snap fingers and plate.
- The real tag position and the plastic thickness the reader tolerates (the fixtures exist to answer this).
- Whether the clip arms grip 1.75mm filament as well as the original clip.

## Credits and licence

This project is licensed CC BY-NC-SA 4.0 (see `LICENSE`) because it builds on CC BY-NC-SA work. Non-commercial use only, share alike, attribution required.

- Clip arm proportions are measured from Extrutim's [Filament Clip, Grandma's Favorite](https://www.printables.com/model/24371-filament-clip-grandmas-favorite-filament-clip) (Printables 24371).
- The snap-in holder follows remmulegguh's [Snapmaker U1 NFC / RFID Tag Holder](https://www.printables.com/model/1625982-snapmaker-u1-nfc-rfid-tag-holder) (Printables 1625982).
- The sticker-coin and per-material chip idea follows A-Jey's [Snapmaker U1 RFID Adapter & Chip System](https://www.thingiverse.com/thing:7268905) (Thingiverse 7268905), and krokus57's [remix](https://www.thingiverse.com/thing:7324691).
- Firmware: [paxx12's SnapmakerU1-Extended-Firmware](https://github.com/paxx12/SnapmakerU1-Extended-Firmware) and [OpenRFID](https://github.com/suchmememanyskill/OpenRFID).

The original authors' files are not redistributed here.

## How it was made

Human-crafted and AI-assisted, human-directed: the design decisions are Charles's, and the geometry and scripts were drafted with Claude Code and reviewed along the way.
