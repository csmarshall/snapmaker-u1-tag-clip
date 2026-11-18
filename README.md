# snapmaker-u1-tag-clip

A filament clip that carries its spool's NFC tag, and a numbered dock that snaps into the Snapmaker U1's side-panel socket so the printer reads that tag when you load the spool.

![The clip chip and the dock](docs/images/hero.png)

Each spool keeps its own **chip**: a small clip that holds the loose filament end, with an NTAG215 sticker pressed into its back and the material name printed in a second colour on the front. To load a spool, take the chip off it, drop it into the **dock** for that slot on the printer, and feed the filament. The U1 reads the tag as the feeder engages. When you unload, the chip goes back on the spool. There is no velcro, no loose card to lose, and the tag can't end up with the wrong spool.

It was made for feeding the U1 from an external dryer (a Creality SpacePi X4) with [paxx12's extended firmware](https://github.com/paxx12/SnapmakerU1-Extended-Firmware), OpenRFID and Spoolman. The chip itself isn't tied to the U1, so it works as a tagged filament clip anywhere a reader can see it.

## Just print it

Ready-to-print 3MFs are in [`prints/`](prints/). GitHub Actions rebuilds that folder from the generator whenever the model changes, so it tracks the code.

| File | What |
|---|---|
| [`prints/chips/tag-clip_<type>.3mf`](prints/chips/) | One chip for each known filament type (PLA, PLA+, PLA+ HS, PETG, ABS, TPU, nylon and more; see [`prints/README.md`](prints/README.md) for the full list). |
| [`prints/tag-clip_all-chips.3mf`](prints/tag-clip_all-chips.3mf) | One of every chip type on a single U1 plate. |
| [`prints/u1/u1_docks_fingers_set.3mf`](prints/u1/u1_docks_fingers_set.3mf) | The four U1 docks, slots 1 to 4, on one plate. |

The files open in Snapmaker Orca (or Orca Slicer / Bambu Studio). They carry geometry and filament assignments only, so pick your printer, process and filament presets after opening.

- **Chip:** prints back face down with no pause. The body is filament 1 and the name is filament 2. After printing, press a 25 mm round NTAG215 sticker into the recess in the back. It sits below the face, so a dead sticker can be swapped without reprinting. To print several, use Orca's copy count on the single-chip file.
- **Dock:** prints standing on its bottom stop. Supports under the snap fingers are already enabled in the file (build plate only). The slot digit and orientation hint are inlaid in filament 2. PETG is what's been printed so far.

### Need a type that isn't there?

```sh
cd chip
uv run python chip_clip.py "PETG-GF" "TPU 85A"
```

Each name becomes `chip/out/tag-clip_<name>.3mf` (plus `.stl` and `.step`). In file names `+` becomes `plus` and spaces become `_`. Long names shrink to fit. To make a type permanent, so that it's built into `prints/`, add it to `FILAMENTS` in [`chip/chip_clip.py`](chip/chip_clip.py) and open a pull request.

## Using it with the U1

The short version (full detail in [`docs/WORKFLOW.md`](docs/WORKFLOW.md)):

1. Install paxx12's extended firmware (v1.6.0 or later), turn on Advanced Mode, set Filament Detection to OpenRFID, and point the Spoolman integration at your Spoolman server.
2. Write each chip's tag. What has worked so far is a tag holding one NDEF record of type `application/json` in the OpenSpool format, for example `{"protocol":"openspool","version":"1.0","type":"PETG","color_hex":"16171B","brand":"Snapmaker"}`. Spoolman GO wrote one that the U1 read. Spoolman itself doesn't write tags; it only pairs UIDs.
3. Snap a dock into each spool-holder socket you feed from. The dock's fingers centre the sticker on the socket, where the U1's reader coil is.
4. Load: chip into the dock, then feed. To re-read a lane without re-feeding, run `FILAMENT_DT_UPDATE CHANNEL=<0-3>` in the Fluidd console (lane 1 is channel 0), or press "Read spool tags" in the Filament Manager.

## Status

This is a working design that's still being tuned, not a finished product.

- **Printed and fitted:** chips, and the finger docks in PETG. The dock channel was widened to 0.5 mm per side and 0.8 mm front to back after the first prints stuck.
- **Still being verified:** reading a tag reliably through the dock in every slot. One early failure turned out to be a blank tag, not distance. Whether the clip arms grip 1.75 mm filament as well as Extrutim's original.
- Every sliding fit comes from one constant, `FIT_CLEARANCE` (0.3 mm), plus the dock's `DOCK_SIDE_CLEARANCE` and `DOCK_FRONT_CLEARANCE`, all in `chip/chip_clip.py`. If your printer runs tight or loose, change those and rebuild.

Issues and photos of your prints are welcome.

## The repo

| Path | What |
|---|---|
| [`chip/`](chip/) | The generator for the printer-neutral parts. `chip_clip.py` is the parametric [build123d](https://github.com/gumyr/build123d) model of the chip (sticker recess, clip arms, name) and a generic dock. Every dimension is a named constant at the top. `chip_3mf.py` writes the two-filament 3MF. `fonts/` holds the label font (Arimo, OFL), vendored so the lettering is the same on every machine. |
| [`u1/`](u1/) | The Snapmaker U1 parts, which build on `chip/`. `u1_parts.py` holds the finger dock (the production dock), the integrated dovetail dock, the socket adapter, the dock mount and blank covers. `socket_fingers.py` holds the snap fingers. `u1_build.py` builds them, `tools/` lays out plates and writes 3MFs, and `docs/` has the design notes for each variant. `fixtures/` has test prints for finding where the reader sees a sticker. |
| [`prints/`](prints/) | Generated 3MFs. Don't edit them by hand; `tools/build_prints.py` writes them. |
| [`tools/build_prints.py`](tools/build_prints.py) | Builds everything and rewrites `prints/`. With the locked toolchain (`uv.lock`) the same model rebuilds to the same bytes on one machine; Linux and macOS builds have not been compared yet, so the first CI rebuild may refresh the files once. |
| [`tests/`](tests/), [`u1/tests/`](u1/tests/) | Fit and consistency checks on the built meshes: clearances, the clip against the original's geometry, finger positions, plate layouts and reproducible 3MFs. CI runs them on every push. |
| [`docs/`](docs/) | The day-to-day workflow (`WORKFLOW.md`) and where the U1's reader coil is likely to be (`ANTENNA.md`). |

### Build and test locally

You need [uv](https://docs.astral.sh/uv/). The dependencies are pinned in `uv.lock` and installed on first run.

```sh
uv run python tools/build_prints.py   # rebuild prints/
uv run python -m pytest -q tests u1/tests
```

The tests read the built meshes in `chip/out/` and `u1/out/`, so run a build first. Without one, most of them skip.

Slicer note: Snapmaker Orca 1.10.1's command line crashes when it loads a process preset, so nothing here slices the files automatically. Open them in the GUI.

## Parts and terms

| Term | What it is |
|---|---|
| chip | The clip: round end up, flat end down with a centre key notch, sticker in an open recess in the back, material name on the front. |
| clip arms | The three walls on the chip that grip the filament end, traced from Extrutim's clip. |
| hook finger | The tallest clip arm. It's 2 mm taller than the original so it stands proud of the dock and a thumb run up the dock's face lifts the chip out. |
| dock | The holder the chip drops into, one per U1 slot, numbered 1 to 4 left to right. |
| finger dock | The production dock: the snap fingers are on its back, so it plugs straight into a spool-holder socket with the sticker on the socket's axis. |
| channels, lower pocket | The side rails and lips that guide the chip in from the open top, and the plate over the clip arms at the bottom. |
| key post | A post on the bottom stop that fits the chip's notch. If the chip goes in upside down, it sits visibly high. |
| blank cover | Snap fingers and a round numbered plate for an unused socket. |

## Credits and licence

Licensed [CC BY-NC-SA 4.0](LICENSE), because this builds on CC BY-NC-SA work: non-commercial use only, share alike, attribution required. [`SOURCES.md`](SOURCES.md) records exactly what was taken from each source and how.

- The clip arms are a close trace of Extrutim's [Filament Clip, Grandma's Favorite](https://www.printables.com/model/24371-filament-clip-grandmas-favorite-filament-clip) (Printables 24371), with the hook finger made taller.
- The snap fingers are traced from remmulegguh's [Snapmaker U1 NFC / RFID Tag Holder](https://www.printables.com/model/1625982-snapmaker-u1-nfc-rfid-tag-holder) (Printables 1625982).
- The idea of a sticker in a coin, one per material, comes from A-Jey's [Snapmaker U1 RFID Adapter & Chip System](https://www.thingiverse.com/thing:7268905) (Thingiverse 7268905) and krokus57's [remix](https://www.thingiverse.com/thing:7324691).
- The dock mount and socket adapter take the measured slot section of 1waynger1's [Snapmaker U1 Filament Hub Replacement](https://makerworld.com/en/models/2152529-snapmaker-u1-filament-hub-replacement) (MakerWorld 2152529) so they fit his base. Only those dimensions are used; none of his files are included.
- Firmware and tag support: [paxx12's SnapmakerU1-Extended-Firmware](https://github.com/paxx12/SnapmakerU1-Extended-Firmware) and [OpenRFID](https://github.com/suchmememanyskill/OpenRFID).
- Label font: [Arimo](https://github.com/googlefonts/Arimo), SIL Open Font License 1.1 (`chip/fonts/OFL.txt`).

The original authors' files aren't redistributed here.

## How it was made

Human-designed and human-directed, AI-assisted. The design decisions, fit tuning and print testing are Charles Marshall's. The build123d geometry, checks and tooling were drafted with Claude Code under his direction, and he reviewed every change.
