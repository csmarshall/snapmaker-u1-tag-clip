# Where the U1's tag reader sees a sticker (working assumption)

Snapmaker's own coil-replacement guide (see below) shows each reader coil as one large copper loop glued to the inside of the side panel, ringed around a spool-holder socket. Its exact size and the reading range have not been measured. This page records that and what the earlier tag holders imply, so the clip-mount dock (issue #2) and the VHB dock (issue #5) can be placed sensibly before anyone measures it. Treat it as an estimate until the coin-finder puck (issue #3) confirms or corrects it.

## Evidence

| Source | Where the tag sits, relative to the socket | How we know |
|---|---|---|
| Snapmaker Wiki, [U1 RFID coil replacement guide](https://wiki.snapmaker.com/en/snapmaker_u1/troubleshooting/RFID_coil_replacement_guide) | The coils sit on the inner surface of the left and right panels; each is a single round loop around a socket's boss, several times wider than the boss | Its photos of the panel interior (viewed 2026-10-14; not reproduced here) |
| Stock spools (Snapmaker, Bambu and others) | Anywhere around the hub: the tag is on the spool's side and the spool can stop at any angle | It reads regardless of rotation, which a small antenna at one spot could not do |
| A-Jey, [Thingiverse 7268905](https://www.thingiverse.com/thing:7268905) | Chip pad centred about 40mm from the hub axis, at roughly 1 to 2 o'clock in his photo | Measured from `U1-RFID-Adapter.stl`; his install photo (`images/2026-01-09_21.50.15.jpg` in the download) |
| remmulegguh, [Printables 1625982](https://www.printables.com/model/1625982-snapmaker-u1-nfc-rfid-tag-holder) | Directly below the socket. The long holder's hook reaches about 41mm from the socket axis and the short one about 26mm | His install photo on the saved page; measured from the centre of his round 31.6mm plate (the socket axis) in `rfidholder.stl` and `holderrfid_short.stl` |
| remmulegguh's notes | "Length doesn't matter": the short and long holders both satisfy the reader | Text on the saved Printables page |

The tag hangs from the hook, so its centre is somewhat further out than the hook tip. The exact offset depends on the tag and wasn't measured.

## Working assumption

The antenna is a loop around each socket, so a sticker inside the loop and close to the panel should read. The tested positions, about 25 to 45mm from the socket axis, are all inside it. A sticker anywhere in that band, at least below the socket or up and to the right of it, should read through the side panel.

What this does not tell us:
- How far the band really extends inwards and outwards, or whether every angle works (only two have been seen).
- How much plastic and air the reader tolerates. The earlier holders put the tag almost against the panel, whereas our sticker sits behind 1.8mm of plastic plus a 0.3mm gap, and VHB tape would add more.
- Whether the two sides of the printer (slots 1 and 2 versus 3 and 4) mirror each other.

## What follows for the design

- **Clip mount (issue #2):** built. The back plate carries on up to the socket, remmulegguh's traced snap fingers go into the socket, and the sticker centre sits `SOCKET_ABOVE_STICKER` = 38mm below the socket axis. His 3mm plate is not used: it stands proud of the panel and would block the chip's path, while our 1.2mm plate lies flat on the panel.
- **Testing a read:** `FILAMENT_DT_UPDATE CHANNEL=<0-3>` in the Fluidd console re-reads a channel (channel 1 is 0), per Snapmaker's RFID troubleshooting page.
- **VHB mount (issue #5):** the same spot. Below the socket, the sticker centre is about 35 to 40mm from the socket's centre.
- **Check before trusting it:** the coin-finder puck and the standoff strip (issue #3) settle the band and the plastic thickness.

All of this is human-directed and AI-assisted. The measurements come from the community files listed in `SOURCES.md`, and nothing here has been tested on a printer.
