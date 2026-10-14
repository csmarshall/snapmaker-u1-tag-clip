# Sources and remix provenance

Everything this project builds on, kept so the lineage is never lost. Retrieved 2026-10-13. The original files sit in a local, gitignored `thingiverse/` folder and are not redistributed in this repo; the hashes (first 16 hex digits of SHA-256) identify the exact files that were used so they can be re-fetched and checked.

## Used in the design

| Source | Author | Licence | What we took | How |
|---|---|---|---|---|
| [Filament Clip, Grandma's Favorite](https://www.printables.com/model/24371-filament-clip-grandmas-favorite-filament-clip) (Printables 24371) | Extrutim | CC BY-NC-SA 4.0 (page asks remixes to keep the same licence; selling files or prints is prohibited) | The clip mechanism for 1.75mm filament, unchanged, turned 180 degrees and moved as one unit onto the coin (verified against the original before the one deliberate change below: only a rotation and a shift remained). The one deliberate change: wall A, the hook finger, is 2mm taller (`WALL_A_EXTRA_HEIGHT`) so it stands proud of the dock's pocket, at Charles's request: three walls 3.0mm high with the channel gaps (about 1.9 and 3.0mm), the smooth S-bend of walls B and C, wall A's curled-over top and its small centre nub, and the catch on wall C's inner face at each end | Traced from `Clip-Classic.stl` (`5cb545de106921d3`) by slicing at many x and z positions: S-bend table at 0.3mm steps, wall A lip curve, nub and end-catch bands are measured values in `coin/u1_chip_clip.py`. Compared against the original after building: edges agree within about 0.08mm except the ramp into the end catch (up to 0.4mm). No mesh is copied, but the shape is a close trace, so treat it as a derivative of Extrutim's clip. |
| [Snapmaker U1 NFC / RFID Tag Holder](https://www.printables.com/model/1625982-snapmaker-u1-nfc-rfid-tag-holder) (Printables 1625982) | remmulegguh | CC BY-NC-SA 4.0 | The snap-in interface for the panel's spool-holder socket: curved plate (about 20mm tall, arc radius about 25.7mm) and two springy fingers (10mm tall, 27mm long) | Analysed from `rfidholder.stl` (`0273e2de039adc9e`) and `holderrfid_short_no1.stl` (`779cac871b7ba18e`). The hanger and the blank cover use his snap fingers, traced from `holderrfid_short.stl` into `coin/socket_fingers.py` (one section: the fingers are a straight 10mm extrusion). His plate is replaced by our own back plate extension so the chip's path stays clear. A test checks that the traced fingers match his within 2% by volume. This makes the hanger and cover derivatives of his file. |
| [Snapmaker U1 RFID Adapter & Chip System](https://www.thingiverse.com/thing:7268905) (Thingiverse 7268905) | A-Jey | CC BY-NC-SA | The sticker-in-a-coin concept, 25mm NTAG215 stickers, per-material coins, and the tag position (a 30mm pad centred 40mm from the hub axis) | Measured from `U1-RFID-Adapter.stl` (`f1d52964b71a38d4`) and `U1-RFID-Adapter_Chip.stl` (`e13ba9e3d01e8aa0`): chip 26.98 x 26.99 x 1.2mm. Concept only; no geometry copied. |

Antenna-position evidence from these files (install photos, the 31.6mm socket bore and the hook reach in remmulegguh's holders, and A-Jey's 40mm pad) is collected in `docs/ANTENNA.md`.

## Reviewed, informed the design, nothing taken

| Source | Author | Licence | Note |
|---|---|---|---|
| [Thingiverse 7324691](https://www.thingiverse.com/thing:7324691), a remix of A-Jey's chip | krokus57 | CC BY-SA | Adds a label spot, storage hole and a slot for a filament snippet showing the colour. The colour-slot idea is a candidate for later. `nfc_tag_with_filament_insert.stl` (`81192d53c1eaa168`). |
| [MakerWorld 2390956](https://makerworld.com/en/models/2390956), Snapmaker U1 Side Spool Holder | not recorded (page blocked fetchers) | unverified | A 38mm-flange, 30mm-shaft holder stub that plugs into the U1 hub. No socket detail visible in the STL (`70mmHolder1.stl`, `990d86cea8fabd4b`). |
| [MakerWorld 3094579](https://makerworld.com/en/models/3094579), RFID Mod for CC3DProjects SpoolBox | not recorded | unverified | A spool-core wrapper and SpoolBox mount negative; not U1 panel data. |
| paxx12 [SnapmakerU1-Extended-Firmware](https://github.com/paxx12/SnapmakerU1-Extended-Firmware) and [RFID docs](https://snapmakeru1-extended-firmware.pages.dev/design/rfid.html) | paxx12 | see repo | Needed for custom tags. UID to Spoolman mapping, and the "1-3cm" external-reader figure (not measured for the built-in coil). |
| [OpenRFID](https://github.com/suchmememanyskill/OpenRFID) | suchmememanyskill | see repo | The tag format and reader integration the firmware uses. |

## Official reference

- Snapmaker Wiki, [U1 RFID coil replacement guide](https://wiki.snapmaker.com/en/snapmaker_u1/troubleshooting/RFID_coil_replacement_guide) and [U1 RFID information cannot be updated](https://wiki.snapmaker.com/en/snapmaker_u1/troubleshooting/RFID_information_cannot_be_updated), read 2026-10-14: the reader coils are large single copper loops glued to the inside of the left and right panels, ringed around each spool-holder socket; `FILAMENT_DT_UPDATE CHANNEL=<0-3>` re-reads a channel's tag from the console. Facts only; no images or text are reproduced.

## Not found

No public CAD, drawing or teardown gives the U1's socket dimensions or its coil position. Those have to be measured on the printer (see `fixtures/`).
