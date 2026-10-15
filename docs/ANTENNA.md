# Where the U1's tag reader sees a sticker (working assumption)

Snapmaker's own coil-replacement guide (see below) shows each reader coil as one large copper loop glued to the inside of the side panel, ringed around a spool-holder socket. Its exact size and the reading range have not been measured. This page records that and what the earlier tag holders imply, so the clip-mount dock (issue #2) and the VHB dock (issue #5) can be placed sensibly before anyone measures it. Treat it as an estimate until the coil-finder puck (issue #3) confirms or corrects it.

## Evidence

| Source | Where the tag sits, relative to the socket | How we know |
|---|---|---|
| Snapmaker Wiki, [U1 RFID coil replacement guide](https://wiki.snapmaker.com/en/snapmaker_u1/troubleshooting/RFID_coil_replacement_guide) | The coils sit on the inner surface of the left and right panels; each is a single round loop around a socket's boss, several times wider than the boss | Its photos of the panel interior (viewed 2026-10-14; not reproduced here) |
| Stock spools (Snapmaker, Bambu and others) | Anywhere around the hub: the tag is on the spool's side and the spool can stop at any angle | It reads regardless of rotation, which a small antenna at one spot could not do |
| A-Jey, [Thingiverse 7268905](https://www.thingiverse.com/thing:7268905) | Chip pad centred about 40mm from the hub axis, at roughly 1 to 2 o'clock in his photo | Measured from `U1-RFID-Adapter.stl`; his install photo (`images/2026-01-09_21.50.15.jpg` in the download) |
| remmulegguh, [Printables 1625982](https://www.printables.com/model/1625982-snapmaker-u1-nfc-rfid-tag-holder) | Directly below the socket. The long holder's hook reaches about 41mm from the socket axis and the short one about 26mm | His install photo on the saved page; measured from the centre of his round 31.6mm plate (the socket axis) in `rfidholder.stl` and `holderrfid_short.stl` |
| bdwilson, [MakerWorld 2195878](https://makerworld.com/en/models/2195878-snapmaker-u1-rfid-holder) | Below the socket, a bare tag in a pocket about 15mm below 1waynger1's hub base, so roughly 35 to 50mm from the axis depending on which end of the base is up | Measured from his 3mf and install photo; four reviews and no read complaints, but no stated read tests |
| remmulegguh's notes | "Length doesn't matter": the short and long holders both satisfy the reader | Text on the saved Printables page |

The tag hangs from the hook, so its centre is somewhat further out than the hook tip. The exact offset depends on the tag and wasn't measured.

## The reader hardware (online research, 2026-10-15)

Nobody has published a measured read range, coil size or inductance for the U1. What is known:

| Fact | Source |
|---|---|
| Reader IC is an FM175XX (FM17550 named in the forum), close to the MFRC522; 13.56 MHz, ISO 14443 A/B only | [SnapmakerResearchGroup/RFID](https://github.com/SnapmakerResearchGroup/RFID); [forum: U1 and RFID standard](https://forum.snapmaker.com/t/u1-and-rfid-standard/39948) |
| Coils are large, with thick wire and few turns; JST-GH 2-pin, ~20cm unshielded leads; left reader on the mainboard, right on an extension board; the antenna is a tuned LC circuit, so extending the leads past ~+40cm stops it working | [forum: how to extend RFID coils](https://forum.snapmaker.com/t/how-to-extend-rfid-coils/41020) |
| Stock spools read at any rotation | [forum: extended RFID sensor](https://forum.snapmaker.com/t/how-to-make-an-extended-rfid-sensor/42333) |
| Tag "within 1-3cm of reader antenna" (practical advice, not a spec) | [paxx12 firmware docs](https://snapmakeru1-extended-firmware.pages.dev/rfid_support) |
| Best results when the tag touches the side panel | [MakerWorld 3094579 (SpoolBox RFID mod)](https://makerworld.com/en/models/3094579) |
| RGB LED strips nearby caused misses; metal dry boxes need shielding | [forum: spool detection hardly ever works](https://forum.snapmaker.com/t/spool-detection-hardly-ever-works/41480) |

What this implies: plastic is transparent at 13.56 MHz, so only the distance from the sticker to the coil counts. Our 1.8mm of plastic plus the panel is well inside the 1 to 3cm advice, so the standoff strip is probably a formality. The open question is the coil's outline: a small tag reads well anywhere inside a large loop, but poorly where it straddles the wire. The coil-finder puck answers that, or the coil's diameter could be measured from the photos in Snapmaker's coil-replacement guide (its wiki blocks automated fetching, so read it in a browser).

## Working assumption

The antenna is a loop around each socket, so a sticker inside the loop and close to the panel should read. The tested positions, about 25 to 45mm from the socket axis, are all inside it. A sticker anywhere in that band, at least below the socket or up and to the right of it, should read through the side panel.

What this does not tell us:
- How far the band really extends inwards and outwards, or whether every angle works (only two have been seen).
- How much plastic and air the reader tolerates. The earlier holders put the tag almost against the panel, whereas our sticker sits behind 1.8mm of plastic plus a 0.3mm gap, and VHB tape would add more.
- Whether the two sides of the printer (slots 1 and 2 versus 3 and 4) mirror each other.

## What follows for the design

- **Mounts (issue #2):** the dock mount holds the dock above an adapter's top edge. On our socket adapter the sticker centre is 28.6mm above the socket axis, inside the tested band; on 1waynger1's hub adapter 43.0mm (47.2mm the other way up), at or just past its top. Both are above the socket, where only A-Jey's 1 to 2 o'clock position is a data point. The plates and crossbar lie in front of the panel below the dock, never behind it, so the sticker's distance to the antenna is the dock's own.
- **First read test:** check the sticker reads on both adapters before printing a set.
- **Testing a read:** `FILAMENT_DT_UPDATE CHANNEL=<0-3>` in the Fluidd console re-reads a channel (channel 1 is 0), per Snapmaker's RFID troubleshooting page.
- **VHB mount (issue #5):** the same spot. Below the socket, the sticker centre is about 35 to 40mm from the socket's centre.
- **Check before trusting it:** the coil-finder puck and the standoff strip (issue #3) settle the band and the plastic thickness.

All of this is human-directed and AI-assisted. The measurements come from the community files listed in `SOURCES.md`, and nothing here has been tested on a printer.

## Coil size from Snapmaker's photos (2026-10-15)

The coil-replacement guide's photos (`u1_rfid_coil_right_tape.jpg`, `u1_rfid_coil_left_tape.jpg`) show each coil as a single round loop of a few turns, centred on its socket boss and taped inside a moulded ring. Scaled against the boss (its outside diameter assumed 31mm, since it surrounds the 26.9mm bore), the loop is about 126mm across: 110 to 143mm if the boss is 27 to 35mm. That puts the wire roughly 55 to 72mm from the socket axis. A 25mm sticker centred 28.6mm above the axis (our socket adapter) lies wholly inside the loop with room to spare; at 43 to 47mm (1waynger1's hub adapter) its far edge comes within a few mm of the wire at the small end of that range. This is an estimate from a tilted photo, not a measurement.
