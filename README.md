# snapmaker-u1-tag-clip

A filament clip that carries its spool's NFC tag, and a numbered dock that snaps into the Snapmaker U1's side-panel socket. Load a spool, drop its clip in the dock, and the U1 reads the tag.

![The clip chip and the dock](docs/images/hero.png)

Every spool I own gets its own **chip**. It clips the loose filament end, has an NTAG215 sticker pressed into the back, and has the material name printed in a second colour on the front.

To load, I pull the chip off the spool, drop it into the **dock** for that slot, and feed. The U1 reads the tag when the feeder engages. When I unload, the chip goes back on the spool. So the tag lives with the spool, and I can't grab the wrong one.

I built it to feed my U1 from a Creality SpacePi X4 dryer, running [paxx12's extended firmware](https://github.com/paxx12/SnapmakerU1-Extended-Firmware) with OpenRFID and Spoolman. The chip works on its own as a tagged filament clip, too (any reader that can see it can read it).

## Just print it

Everything ready to slice is in [`prints/`](prints/). GitHub Actions rebuilds that folder from the generator whenever the model changes.

| File | What |
|---|---|
| [`prints/chips/tag-clip_<type>.3mf`](prints/chips/) | One chip per filament type: PLA, PLA+, PLA+ HS, PETG, ABS, TPU, nylon and 14 more. The full list is in [`prints/README.md`](prints/README.md). |
| [`prints/tag-clip_all-chips.3mf`](prints/tag-clip_all-chips.3mf) | All 21 chips on one U1 plate. |
| [`prints/u1/u1_docks_fingers_set.3mf`](prints/u1/u1_docks_fingers_set.3mf) | The 4 U1 docks, slots 1 to 4, on one plate. |

They open in Snapmaker Orca, Orca Slicer or Bambu Studio. There's geometry and filament assignments in them and nothing else, so pick your printer, process and filament presets after you open one.

- **Chip:** prints back face down, no pause. Body on filament 1, name on filament 2. When it's done, press a 25 mm round NTAG215 sticker into the recess in the back. It sits below the face, so a dead sticker swaps out without a reprint. Want 10? Open the single-chip file and set Orca's copy count.
- **Dock:** prints standing on its bottom stop. Supports under the snap fingers are already turned on in the file (build plate only). The slot digit and the orientation hint print in filament 2. I've only printed these in PETG so far.

### Need a type that isn't there?

```sh
cd chip
uv run python chip_clip.py "PETG-GF" "TPU 85A"
```

Each name lands in `chip/out/tag-clip_<name>.3mf`, with a `.stl` and `.step` next to it. In file names `+` becomes `plus` and spaces become `_`. Long names shrink to fit.

If it should ship with everything else, add it to `FILAMENTS` in [`chip/chip_clip.py`](chip/chip_clip.py) and send a pull request.

## Using it with the U1

The short version. The long one is in [`docs/WORKFLOW.md`](docs/WORKFLOW.md).

1. Install paxx12's extended firmware (v1.6.0 or later). Turn on Advanced Mode, set Filament Detection to OpenRFID, and point the Spoolman integration at your Spoolman server.
2. Write each chip's tag. What's worked for me: one NDEF record, type `application/json`, in the OpenSpool format, like `{"protocol":"openspool","version":"1.0","type":"PETG","color_hex":"16171B","brand":"Snapmaker"}`. Spoolman GO wrote one the U1 read fine. Spoolman itself only pairs UIDs; it doesn't write anything to the tag.
3. Snap a dock into each spool-holder socket you feed from. The fingers centre the sticker on the socket, which is where the U1's reader coil sits.
4. Chip in, then feed. To re-read a lane without re-feeding, run `FILAMENT_DT_UPDATE CHANNEL=<0-3>` in the Fluidd console (lane 1 is channel 0), or hit "Read spool tags" in the Filament Manager.

## Status

It works on my printer, and I'm still tuning it.

- **Printed and fitted:** chips, and the finger docks in PETG. My first docks were too tight, so I opened the channel up to 0.5 mm per side and 0.8 mm front to back.
- **Still checking:** that a tag reads every time, in every slot. One early miss turned out to be a blank tag (the app never actually wrote it). I also want to know if the clip arms hold 1.75 mm filament as well as Extrutim's original. I think they do.
- If your printer runs tight or loose, every sliding fit comes from `FIT_CLEARANCE` (0.3 mm) plus the dock's `DOCK_SIDE_CLEARANCE` and `DOCK_FRONT_CLEARANCE`, all in `chip/chip_clip.py`. Change them and rebuild.

Issues and photos of your prints are welcome.

## The repo

| Path | What |
|---|---|
| [`chip/`](chip/) | The generator for the parts that aren't U1-specific. `chip_clip.py` is the [build123d](https://github.com/gumyr/build123d) model of the chip (sticker recess, clip arms, name) and a generic dock, with every dimension as a named constant at the top. `chip_3mf.py` writes the two-filament 3MF. `fonts/` holds the label font (Arimo, OFL), checked in so the lettering comes out the same on every machine. |
| [`u1/`](u1/) | The Snapmaker U1 parts, built on top of `chip/`. `u1_parts.py` has the finger dock (the one I use), plus an integrated dovetail dock, a socket adapter, a dock mount and blank covers. `socket_fingers.py` has the snap fingers. `u1_build.py` builds them, `tools/` lays out plates and writes 3MFs, and `docs/` has my design notes for each variant. `fixtures/` has test prints for finding where the reader can see a sticker. |
| [`prints/`](prints/) | Generated 3MFs. `tools/build_prints.py` writes them, so don't hand-edit. |
| [`tools/build_prints.py`](tools/build_prints.py) | Builds everything and rewrites `prints/`. With the locked toolchain (`uv.lock`) the same model rebuilds to the same bytes on the same OS. Linux and macOS cut curves into slightly different triangles (I measured it: same bounds, volume within 0.0003 mm³), so their bytes differ. Only the GitHub Actions job writes `prints/`. Build locally to preview, and leave the `prints/` changes out of your commit. |
| [`tests/`](tests/), [`u1/tests/`](u1/tests/) | Fit and consistency checks on the built meshes: clearances, the clip against the original's geometry, finger positions, plate layouts, reproducible 3MFs. CI runs them on every push. |
| [`docs/`](docs/) | The day-to-day loop (`WORKFLOW.md`) and my best guess at where the U1's reader coil is (`ANTENNA.md`). |

### Build and test locally

You need [uv](https://docs.astral.sh/uv/). Dependencies are pinned in `uv.lock` and install on first run.

```sh
uv run python tools/build_prints.py   # rebuild prints/
uv run python -m pytest -q tests u1/tests
```

The tests read the built meshes in `chip/out/` and `u1/out/`, so build first. Without a build, most of them skip.

One slicer gotcha: Snapmaker Orca 1.10.1's command line crashes when it loads a process preset, so nothing here slices automatically. Open the files in the GUI.

## Parts and terms

| Term | What it is |
|---|---|
| chip | The clip: round end up, flat end down with a centre key notch, sticker in an open recess in the back, material name on the front. |
| clip arms | The 3 walls on the chip that grip the filament end, traced from Extrutim's clip. |
| hook finger | The tallest clip arm. I made it 2 mm taller than the original so it sticks up past the dock, and a thumb run up the dock's face pops the chip out. |
| dock | What the chip drops into. One per U1 slot, numbered 1 to 4 left to right. |
| finger dock | The dock I actually use. The snap fingers are on its back, so it plugs straight into a spool-holder socket with the sticker on the socket's axis. |
| channels, lower pocket | The side rails and lips that guide the chip in from the open top, and the plate over the clip arms at the bottom. |
| key post | A post on the bottom stop that fits the chip's notch. Put a chip in upside down and it sits visibly high. |
| blank cover | Snap fingers and a round numbered plate for a socket you're not using. |

## Credits and licence

CC BY-NC-SA 4.0 ([LICENSE](LICENSE)), because I built on CC BY-NC-SA work. Non-commercial, share alike, credit the authors. [`SOURCES.md`](SOURCES.md) says exactly what came from where.

- The clip arms are a close trace of Extrutim's [Filament Clip, Grandma's Favorite](https://www.printables.com/model/24371-filament-clip-grandmas-favorite-filament-clip) (Printables 24371). I made the hook finger taller.
- The snap fingers are traced from remmulegguh's [Snapmaker U1 NFC / RFID Tag Holder](https://www.printables.com/model/1625982-snapmaker-u1-nfc-rfid-tag-holder) (Printables 1625982).
- A sticker in a coin, one per material, is A-Jey's idea: [Snapmaker U1 RFID Adapter & Chip System](https://www.thingiverse.com/thing:7268905) (Thingiverse 7268905), plus krokus57's [remix](https://www.thingiverse.com/thing:7324691).
- The dock mount and socket adapter use the measured slot section of 1waynger1's [Snapmaker U1 Filament Hub Replacement](https://makerworld.com/en/models/2152529-snapmaker-u1-filament-hub-replacement) (MakerWorld 2152529), so they fit his base. I used those dimensions and nothing else; none of his files are here.
- Firmware and tag support: [paxx12's SnapmakerU1-Extended-Firmware](https://github.com/paxx12/SnapmakerU1-Extended-Firmware) and [OpenRFID](https://github.com/suchmememanyskill/OpenRFID).
- Label font: [Arimo](https://github.com/googlefonts/Arimo), SIL Open Font License 1.1 (`chip/fonts/OFL.txt`).

None of the original authors' files are redistributed here.

## How it was made

I designed it, tuned the fits and did the test prints. Claude Code drafted most of the build123d code, the checks and the tooling, working under my direction.
