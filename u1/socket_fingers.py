"""Snap-in fingers for the U1's spool-holder socket, traced from remmulegguh's holder.

Source: holderrfid_short.stl from "Snapmaker U1 NFC / RFID Tag Holder" by remmulegguh, Printables 1625982, CC BY-NC-SA 4.0
(SHA-256 prefix 121cbd7a955f6532). The fingers are a straight extrusion of one outline, so one section through their middle captures them.
Coordinates are mm: depth into the socket measured from the panel face (the back face of his plate), and sideways offset from the socket axis.
The outline starts 0.3mm in front of the panel face so it fuses with the plate. Installed, the fingers lie side by side, centred on the socket axis.
This is a derivative of his file; SOURCES.md credits it.
"""

FINGER_HEIGHT = 10.0  # mm, along the socket's vertical, centred on its axis
# (depth into the socket, sideways offset), traced at the fingers' mid-height
FINGER_OUTLINE = (
    (0.006, 15.009), (0.006, 9.709), (0.478, 9.687), (0.945, 9.62), (1.175, 9.57), (1.628, 9.438),
    (1.85, 9.357), (2.28, 9.162), (2.689, 8.928), (3.075, 8.657), (3.258, 8.507), (3.601, 8.184),
    (4.162, 7.555), (4.443, 7.313), (4.751, 7.108), (4.914, 7.019), (5.256, 6.874), (5.612, 6.773),
    (5.979, 6.715), (6.164, 6.704), (6.534, 6.715), (6.901, 6.773), (7.257, 6.874), (7.43, 6.942),
    (7.599, 7.019), (7.919, 7.206), (8.215, 7.43), (8.48, 7.689), (8.912, 8.184), (9.255, 8.507),
    (9.628, 8.797), (10.026, 9.05), (10.446, 9.265), (10.885, 9.438), (11.338, 9.57), (11.568, 9.62),
    (12.035, 9.687), (12.506, 9.709), (12.742, 9.703), (12.978, 9.687), (13.445, 9.62), (13.675, 9.57),
    (14.128, 9.438), (14.567, 9.265), (14.987, 9.05), (15.189, 8.928), (15.575, 8.657), (15.933, 8.35),
    (16.101, 8.184), (16.662, 7.555), (16.943, 7.313), (17.094, 7.206), (17.414, 7.019), (17.583, 6.942),
    (17.932, 6.818), (18.295, 6.738), (18.664, 6.704), (19.034, 6.715), (19.401, 6.773), (19.757, 6.874),
    (19.93, 6.942), (20.262, 7.108), (20.57, 7.313), (20.851, 7.555), (21.412, 8.184), (21.58, 8.35),
    (21.938, 8.657), (22.324, 8.928), (22.526, 9.05), (22.946, 9.265), (23.385, 9.438), (23.838, 9.57),
    (24.068, 9.62), (24.535, 9.687), (25.006, 9.709), (27.006, 9.709), (27.006, 10.796), (28.211, 11.009),
    (30.006, 9.214), (30.006, 7.709), (25.006, 7.709), (24.649, 7.687), (24.471, 7.661), (24.123, 7.576),
    (23.953, 7.518), (23.626, 7.372), (23.318, 7.189), (23.173, 7.083), (22.903, 6.848), (22.507, 6.396),
    (22.169, 6.048), (21.8, 5.735), (21.401, 5.459), (20.978, 5.223), (20.534, 5.029), (20.074, 4.879),
    (19.838, 4.821), (19.361, 4.739), (18.878, 4.704), (18.635, 4.704), (18.152, 4.739), (17.912, 4.774),
    (17.439, 4.879), (16.979, 5.029), (16.754, 5.121), (16.32, 5.336), (15.909, 5.593), (15.713, 5.735),
    (15.344, 6.048), (15.171, 6.218), (14.61, 6.848), (14.34, 7.083), (14.044, 7.285), (13.887, 7.372),
    (13.56, 7.518), (13.217, 7.623), (12.864, 7.687), (12.506, 7.709), (12.149, 7.687), (11.971, 7.661),
    (11.623, 7.576), (11.287, 7.45), (10.969, 7.285), (10.818, 7.189), (10.534, 6.97), (10.279, 6.718),
    (10.006, 6.395), (9.667, 6.046), (9.295, 5.732), (9.098, 5.588), (8.684, 5.332), (8.248, 5.116),
    (7.792, 4.944), (7.322, 4.817), (7.083, 4.771), (6.6, 4.714), (6.113, 4.705), (5.628, 4.742),
    (5.387, 4.779), (4.912, 4.887), (4.45, 5.04), (4.053, 5.204), (3.696, 5.312), (3.513, 5.349),
    (3.143, 5.389), (2.77, 5.383), (2.401, 5.331), (2.041, 5.233), (1.696, 5.091), (1.531, 5.005),
    (1.219, 4.802), (0.934, 4.561), (0.681, 4.288), (0.464, 3.985), (0.286, 3.657), (0.15, 3.31),
    (0.058, 2.949), (0.012, 2.579), (0.006, -2.375), (0.03, -2.747), (0.099, -3.113), (0.15, -3.292),
    (0.213, -3.468), (0.37, -3.806), (0.464, -3.967), (0.681, -4.27), (0.934, -4.544), (1.073, -4.668),
    (1.372, -4.89), (1.531, -4.987), (1.867, -5.15), (2.041, -5.215), (2.401, -5.313), (2.77, -5.365),
    (2.956, -5.374), (3.328, -5.357), (3.696, -5.295), (4.053, -5.187), (4.45, -5.023), (4.912, -4.869),
    (5.387, -4.761), (5.628, -4.725), (6.113, -4.687), (6.6, -4.697), (7.083, -4.754), (7.559, -4.858),
    (7.792, -4.927), (8.248, -5.099), (8.684, -5.314), (9.098, -5.571), (9.295, -5.714), (9.667, -6.028),
    (10.006, -6.377), (10.279, -6.7), (10.534, -6.952), (10.818, -7.171), (10.969, -7.267), (11.287, -7.432),
    (11.623, -7.558), (11.796, -7.606), (12.149, -7.67), (12.506, -7.691), (12.864, -7.67), (13.217, -7.606),
    (13.56, -7.5), (13.887, -7.355), (14.044, -7.267), (14.34, -7.066), (14.61, -6.83), (15.171, -6.2),
    (15.525, -5.87), (15.713, -5.718), (16.112, -5.442), (16.535, -5.206), (16.754, -5.103), (16.979, -5.012),
    (17.439, -4.862), (17.912, -4.757), (18.152, -4.722), (18.393, -4.698), (18.878, -4.686), (19.12, -4.698),
    (19.601, -4.757), (20.074, -4.862), (20.534, -5.012), (20.978, -5.206), (21.401, -5.442), (21.8, -5.718),
    (22.169, -6.031), (22.507, -6.378), (22.903, -6.83), (23.173, -7.066), (23.469, -7.267), (23.626, -7.355),
    (23.953, -7.5), (24.123, -7.558), (24.296, -7.606), (24.649, -7.67), (25.006, -7.691), (30.006, -7.691),
    (30.006, -9.196), (28.211, -10.991), (27.006, -10.779), (27.006, -9.691), (25.006, -9.691), (24.535, -9.669),
    (24.301, -9.641), (23.838, -9.553), (23.385, -9.421), (23.163, -9.339), (22.733, -9.145), (22.324, -8.911),
    (21.938, -8.639), (21.755, -8.49), (21.412, -8.167), (20.851, -7.537), (20.57, -7.295), (20.262, -7.09),
    (19.93, -6.924), (19.581, -6.8), (19.218, -6.721), (18.849, -6.686), (18.664, -6.686), (18.295, -6.721),
    (17.932, -6.8), (17.583, -6.924), (17.251, -7.09), (17.094, -7.188), (16.943, -7.295), (16.662, -7.537),
    (16.101, -8.167), (15.758, -8.49), (15.575, -8.639), (15.189, -8.911), (14.78, -9.145), (14.567, -9.247),
    (14.35, -9.339), (13.903, -9.492), (13.675, -9.553), (13.212, -9.641), (12.978, -9.669), (12.506, -9.691),
    (12.035, -9.669), (11.801, -9.641), (11.338, -9.553), (10.885, -9.421), (10.446, -9.247), (10.026, -9.032),
    (9.628, -8.779), (9.255, -8.49), (8.912, -8.167), (8.48, -7.671), (8.215, -7.412), (7.919, -7.188),
    (7.762, -7.09), (7.43, -6.924), (7.081, -6.8), (6.718, -6.721), (6.534, -6.698), (6.164, -6.686),
    (5.795, -6.721), (5.612, -6.755), (5.432, -6.8), (5.083, -6.924), (4.751, -7.09), (4.443, -7.295),
    (4.162, -7.537), (3.601, -8.167), (3.258, -8.49), (3.075, -8.639), (2.689, -8.911), (2.28, -9.145),
    (1.85, -9.339), (1.628, -9.421), (1.175, -9.553), (0.712, -9.641), (0.478, -9.669), (0.006, -9.691),
    (0.006, -14.991), (-0.3, -14.991), (-0.3, 15.009),
)

FINGER_SPREAD = 2.0  # mm per side, the default spread of every variant that carries the fingers: Charles's choice from the printed sweep (docs/FINGER_SPREAD.md), 2026-10-15. The real bore is unmeasured (assumed 26.9 mm), so revisit it once measured. 0 gives the traced outline exactly

ROOT_DEPTH = 0.006  # the outline's points at or in front of this depth are the root (the tab and the fuse with the plate); a spread never moves them
SPREAD_RAMP = 10.0  # mm of depth over which a spread builds up from nothing at the root to its full value; past it the arms and hooks sit rigidly shifted


def spread_outline(spread: float = 0.0) -> tuple[tuple[float, float], ...]:
    """FINGER_OUTLINE with the arms and hooks moved outward by `spread` mm per side, the root fixed.

    Every point behind the root moves sideways away from the axis by spread * s(t), where t = (depth - ROOT_DEPTH) / SPREAD_RAMP clamped to 0..1 and s is the smoothstep 3t^2 - 2t^3.
    Moving the inner and outer faces together keeps the arms' thickness and the hooks' shape, and the ramp (zero slope at the root, at most about 1.5 * spread / SPREAD_RAMP afterwards)
    bends the arms out from the root instead of shearing them off it, so the corner where an arm leaves the tab is not made sharper. A spread of 0 returns the traced outline itself.
    """
    if spread == 0:
        return FINGER_OUTLINE
    moved = []
    for depth, side in FINGER_OUTLINE:
        t = min(max((depth - ROOT_DEPTH) / SPREAD_RAMP, 0.0), 1.0)
        shift = spread * t * t * (3 - 2 * t)
        moved.append((depth, side + shift if side > 0 else side - shift if side < 0 else side))
    return tuple(moved)


HOOK_FROM_DEPTH = 26.0  # the hooks are the outline's points this deep or deeper (the straight arms end at 25.006 and the hook's step starts at 27.006)


def hook_half_width(spread: float = 0.0) -> float:
    """Half-width of the hooks, the widest part of the fingers inside the socket (11.009 mm traced), at this spread."""
    return max(abs(side) for depth, side in spread_outline(spread) if depth >= HOOK_FROM_DEPTH)


FINGER_BEVEL = 0.0  # mm, leg of the 45 degree release bevel on the two hook corners that lead when the fingers are turned counter-clockwise (seen from the dock's front). Dropped by Charles 2026-10-15, so 0 = no bevel is cut anywhere; set it back to a value (1.5 was tried) to restore it. A tuned feel value, not derivable. It is clipped to the hook's retaining step (1.087 mm) and to FINGER_HEIGHT, see bevel_leg
HOOK_REAR_DEPTH = 27.006  # depth of the hooks' retaining (panel-facing) step: the outline's face from the arm's outer side out to the hook's widest point


def hook_step(spread: float = FINGER_SPREAD) -> tuple[float, float, float]:
    """Return (depth, inner side, outer side) of the +side hook's retaining step at this spread: the face the bevel's rear leg lies in."""
    sides = sorted(side for depth, side in spread_outline(spread) if depth == HOOK_REAR_DEPTH and side > 0)
    assert len(sides) == 2, "the outline no longer has a two-point retaining step at HOOK_REAR_DEPTH"
    return HOOK_REAR_DEPTH, sides[0], sides[1]


def bevel_leg(spread: float = FINGER_SPREAD) -> float:
    """The bevel's leg along the finger height and along the depth: FINGER_BEVEL, but never more than the retaining step's height or FINGER_HEIGHT."""
    _, inner, outer = hook_step(spread)
    return max(0.0, min(FINGER_BEVEL, outer - inner, FINGER_HEIGHT))
