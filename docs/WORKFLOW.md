# Workflow: tracking and loading filament with the clip coin

The day-to-day loop this design is meant to support, and what it depends on. Sources are paxx12's docs ([NFC and Spoolman setup](https://snapmakeru1-extended-firmware.pages.dev/nfc_spoolman_setup.html), [Spoolman integration](https://snapmakeru1-extended-firmware.pages.dev/spoolman.html)), read 2026-10-13. Anything not stated there is marked unverified. Nothing in this repo has been tested on a printer yet.

## The loop

1. **Library:** each spool in the library has its own coin clipped to the filament end. The coin's NTAG215 sticker is paired to that spool in Spoolman (by UID, or written by an app, see below).
2. **Load:** take the coin off the spool, drop it into the holder on the printer (sticker side toward the panel), then feed the filament. The U1 reads the tag and takes vendor, material, variant and colour from it or from Spoolman. In the Filament Manager (`http://<printer-ip>/filament/`) the "Read spool tags" button re-reads all four channels, which may save re-feeding after a swap.
3. **Print:** Moonraker tracks the active spool, so Spoolman can update remaining weight as the print runs. Slice in Snapmaker Orca with the detected filament.
4. **Unload:** remove the filament, take the coin out of the holder and clip it back onto the spool's end, then shelve the spool.

The coin's engraved material name is for humans in the library; the printer only sees the sticker's UID and any data on the tag.

## What it needs

- **Extended firmware v1.6.0 or later** (paxx12). Download the `_upgrade.bin` from the releases page. Check which version is installed before anything else.
- **Advanced Mode** on the touchscreen (Settings, Maintenance), then a restart, or the firmware-config page will not load.
- **firmware-config settings** (`http://<printer-ip>/firmware-config/`, Settings, Snapmaker Components): Filament Detection set to OpenRFID (or "OpenRFID (force generic vendor)", which shows unknown spools as Generic), AFC Lite via Fluidd/Mainsail enabled, Spoolman Integration enabled with the server URL such as `http://192.168.1.100:7912`.
- **A Spoolman server** reachable from the printer over HTTP at port 7912, with a fixed address or a router reservation. Spoolman must be running whenever you print. It does not need to run on the U1.
- **NTAG215 or NTAG216 stickers**, 25mm round.
- **A way to write or pair the tags.** The paxx12 guide uses the Android app SpoolPainter: it can create a spool in Spoolman and write a blank tag in one step, attach a tag to an existing spool, pair a second tag for the other side of the printer, and move a tag from one spool to another. Vendor tags (Bambu, Snapmaker, QIDI, Anycubic, Elegoo, Creality) are paired by UID only and nothing is written to them. Other community apps exist, for example Spool Studio. Unverified: whether any of these has an iPhone version.
- **An old Spoolman macro include can stop Klipper from starting** (a leftover `spoolman_multi_tool`-style `CHANGE_SPOOL` include). Remove or rename it before enabling the integration.

## How a spool is matched

- Spoolman can resolve a spool by ID or by RFID card UID. Running `SET_SPOOL_ID` for a lane reads that channel's card UID and binds it to the spool, after which scanning a known tag loads its filament. SpoolLink-compatible apps can link tags to spools too.
- Earlier research (forum and release notes, unverified against the docs) said the firmware reads a `card_uids` custom field in Spoolman and does not read a `spool_id` stored on an OpenSpool tag. The setup page does not describe the field, so check `/design/spoolman.html` before relying on either behaviour.
- A sticker's UID is fixed and cannot be cloned onto another tag, so a "copy" of an existing vendor tag works by pairing its UID, not by copying data.

## Open questions

- Which firmware version is installed now.
- Whether the reader sees a sticker through the holder's wall and at the holder's position. This is what the fixtures are for.
- Exactly when the U1 reads a tag. remmulegguh reports the first feeder engagement; the Filament Manager's re-read button suggests it can be forced.
- Whether per-material, reusable coins (rather than one coin per spool) are worth the re-pairing. With Spoolman, one coin per spool needs no rewriting at all.
