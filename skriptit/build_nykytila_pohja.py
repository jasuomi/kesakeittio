"""Redraw PDF pages 16-17 (sauna floor plan 1:50 + notes) as a 1:1 DXF in millimetres.

Origin = grid G / grid B intersection. Dimensioned values are taken from the
drawing; undimensioned details are measured from the scan (approx. +-30 mm).
Layers:
  A-GRID, A-WALL (+A-WALL-FILL), A-MASONRY, A-DOOR, A-WIND, A-FIXT, A-PORCH,
  A-EAVE, A-DIM, A-TEXT, A-DETAIL, A-NOTES  - clean redraw
Outputs:
  nykytila/sauna_nykytila_pohja_1-50.dxf             - clean redraw only
  nykytila/sauna_nykytila_pohja_skannausreferenssi.dxf - same + SCAN-IMAGE (grid-corrected raster,
                                         needs sauna_nykytila_skannausalusta.png beside it)
                                         + SCAN-TRACE (auto-vectorised scan outlines)
Dimensions are plain lines/ticks/TEXT (not DIMENSION entities) so LibreCAD shows them.
"""
import math
import os
import sys

import cv2
import ezdxf
import numpy as np
import pymupdf
from ezdxf.enums import TextEntityAlignment

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # sauna_cad
PDF = os.path.join(ROOT, "..", "Leimatut rakennuslupapiirustukset.pdf")
OUT = os.path.join(ROOT, "nykytila", "sauna_nykytila_pohja_1-50.dxf")
REF = os.path.join(ROOT, "nykytila", "sauna_nykytila_pohja_skannausreferenssi.dxf")
IMG = os.path.join(ROOT, "nykytila", "sauna_nykytila_skannausalusta.png")

SCALE = 50                      # drawing scale 1:50
TH = 2.5 * SCALE                # normal text height (2.5 mm on paper)
TH_ROOM = 3.5 * SCALE
T = 130                         # log wall thickness (round log ø130)
H2 = T / 2
OH = 230                        # log-corner overhang past grid line

# Grid (mm)
GX = {"G": 0, "H": 2400, "J": 5400, "K": 6300}
GY = {"A": -700, "B": 0, "C": 1350, "D": 2850, "E": 4200}

doc = ezdxf.new("R2010", setup=True)
doc.header["$INSUNITS"] = 4          # mm
doc.header["$MEASUREMENT"] = 1
msp = doc.modelspace()

# name: (colour, linetype, lineweight in 1/100 mm) - lineweights make the 1:50 print readable
LAYERS = {
    "A-GRID": (1, "DASHDOT", 13), "A-WALL": (7, None, 50), "A-WALL-FILL": (8, None, 13),
    "A-MASONRY": (7, None, 35), "A-DOOR": (3, None, 25), "A-WIND": (4, None, 25),
    "A-FIXT": (6, None, 25), "A-PORCH": (30, None, 25), "A-EAVE": (9, "DASHDOT", 18),
    "A-DIM": (2, None, 18), "A-TEXT": (7, None, 25), "A-DETAIL": (7, None, 35),
    "A-NOTES": (7, None, 25), "A-SYMB": (5, None, 25), "A-BEAM": (8, "DASHDOT", 18),
}
for name, (color, lt, lw) in LAYERS.items():
    lay = doc.layers.add(name, color=color)
    lay.dxf.lineweight = lw
    if lt:
        lay.dxf.linetype = lt
doc.header["$LTSCALE"] = 10
doc.header["$LWDISPLAY"] = 1
# LibreCAD print setup: A3 landscape, scale 1:50 (0.02), drawing centred on the sheet
doc.header["$PLIMMIN"] = (0, 0)
doc.header["$PLIMMAX"] = (420, 297)
doc.header["$PSVPSCALE"] = 1 / SCALE
doc.header["$PINSBASE"] = (210 - 6750 / SCALE, 148.5 - 1650 / SCALE, 0)

# ---------------------------------------------------------------- helpers
def rect(x0, y0, x1, y1, layer, closed=True):
    return msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                              close=closed, dxfattribs={"layer": layer})

def line(p, q, layer):
    msp.add_line(p, q, dxfattribs={"layer": layer})

def text(s, x, y, h=TH, layer="A-TEXT", rot=0, align=TextEntityAlignment.MIDDLE_CENTER):
    msp.add_text(s, height=h, rotation=rot, dxfattribs={"layer": layer, "style": "OpenSans"}
                 ).set_placement((x, y), align=align)

def fill(x0, y0, x1, y1, layer="A-WALL-FILL"):
    h = msp.add_hatch(color=256, dxfattribs={"layer": layer})
    h.paths.add_polyline_path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], is_closed=True)

def masonry(x0, y0, x1, y1, holes=()):
    rect(x0, y0, x1, y1, "A-MASONRY")
    h = msp.add_hatch(color=256, dxfattribs={"layer": "A-MASONRY"})
    h.set_pattern_fill("ANSI31", scale=SCALE * 0.6)
    h.paths.add_polyline_path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], is_closed=True)
    for a, b, c, d in holes:
        h.paths.add_polyline_path([(a, b), (c, b), (c, d), (a, d)], is_closed=True)

def wall_h(y, x0, x1, openings=()):
    """Horizontal log wall centred on y from x0..x1 with (a, b) openings."""
    pts = [x0] + [v for o in sorted(openings) for v in o] + [x1]
    for a, b in zip(pts[0::2], pts[1::2]):
        rect(a, y - H2, b, y + H2, "A-WALL"); fill(a, y - H2, b, y + H2)

def wall_v(x, y0, y1, openings=()):
    pts = [y0] + [v for o in sorted(openings) for v in o] + [y1]
    for a, b in zip(pts[0::2], pts[1::2]):
        rect(x - H2, a, x + H2, b, "A-WALL"); fill(x - H2, a, x + H2, b)

def window_h(y, a, b, label=None, label_side=-1):
    line((a, y - H2), (b, y - H2), "A-WIND"); line((a, y + H2), (b, y + H2), "A-WIND")
    line((a, y - 15), (b, y - 15), "A-WIND"); line((a, y + 15), (b, y + 15), "A-WIND")
    if label:
        text(label, (a + b) / 2, y + label_side * 260)

def window_v(x, a, b, label=None, label_side=1):
    line((x - H2, a), (x - H2, b), "A-WIND"); line((x + H2, a), (x + H2, b), "A-WIND")
    line((x - 15, a), (x - 15, b), "A-WIND"); line((x + 15, a), (x + 15, b), "A-WIND")
    if label:
        text(label, x + label_side * 230, (a + b) / 2, rot=90)

def door(hinge, leaf_angle, closed_angle, r):
    """Door leaf from hinge at leaf_angle (deg) and 90deg swing arc to closed position."""
    hx, hy = hinge
    ex, ey = hx + r * math.cos(math.radians(leaf_angle)), hy + r * math.sin(math.radians(leaf_angle))
    line((hx, hy), (ex, ey), "A-DOOR")
    a0, a1 = sorted([leaf_angle, closed_angle])
    if a1 - a0 > 180:
        a0, a1 = a1, a0
    msp.add_arc((hx, hy), r, a0, a1, dxfattribs={"layer": "A-DOOR"})

def bubble(name, x, y):
    msp.add_circle((x, y), 4 * SCALE, dxfattribs={"layer": "A-GRID", "linetype": "CONTINUOUS"})
    msp.add_text(name, height=TH, dxfattribs={"layer": "A-GRID", "style": "OpenSans",
                 "linetype": "CONTINUOUS"}).set_placement((x, y), align=TextEntityAlignment.MIDDLE_CENTER)

# ---------------------------------------------------------------- grid
STUB = 250                                   # short tick leaving the grid bubble
for n, x in GX.items():
    bubble(n, x, -2100)
    msp.add_line((x, -2100 + 4 * SCALE), (x, -2100 + 4 * SCALE + STUB),
                 dxfattribs={"layer": "A-GRID", "linetype": "CONTINUOUS"})
for n, y in GY.items():
    bubble(n, -2000, y)
    msp.add_line((-2000 + 4 * SCALE, y), (-2000 + 4 * SCALE + STUB, y),
                 dxfattribs={"layer": "A-GRID", "linetype": "CONTINUOUS"})
# log-course marks I..IV (as on the drawing)
for s, x in (("I", 0), ("II", 2400), ("III", 3900), ("IV", 5400)):
    text(s, x, -1580, h=TH)
for s, y in (("I", 0), ("II", 1350), ("III", 2850), ("IV", 4200)):
    text(s, -400, y, h=TH, rot=90)

# ---------------------------------------------------------------- log walls
wall_h(GY["E"], -OH, 5400 + OH)                                       # E
wall_h(GY["B"], -OH, 2400 + OH, openings=[(710, 1670)])               # B (G-H)
wall_h(GY["C"], 2400 + H2, 5400 + OH, openings=[(3200, 3990), (4200, 5160)])  # C (H-J)
wall_v(0, -OH, 4200 + OH, openings=[(2900, 3450)])                    # G
wall_v(2400, -OH, 1350 + H2, openings=[(420, 1230)])                  # H lower
wall_v(2400, 3300, 4200 + OH)                                         # H upper
wall_v(5400, 1350 - OH, 4200 + OH, openings=[(2255, 3215)])          # J

window_h(0, 710, 1670, "96X96", -1)
window_h(1350, 4200, 5160, "96X96", -1)
window_v(0, 2900, 3450, "55X55", -1)
text("96X96", -230, 3175 - 620, rot=90)   # second label beside the same window, as on the original
window_v(5400, 2255, 3215, "96X96", 1)

# ---------------------------------------------------------------- masonry
masonry(850, 2035, 2195, 2165)            # S / PH partition (centre at 2100)
masonry(850, 2165, 980, 2295)             # jamb pillar
masonry(1430, 2850, 2400 - H2, 2910)           # protective wall behind stove
masonry(2400 - H2, 2600, 2400 + H2, 3300)  # masonry part of wall H
masonry(2400 - H2, 1350 + H2, 2400 + H2, 1530)   # masonry between wall C and chimney
FLUES = ((2340, 2490), (1980, 2215), (1680, 1850))
FX0, FX1 = 2400 - 88, 2400 + 88           # flues centred on wall line H
masonry(2195, 1530, 2605, 2600, holes=[(FX0, a, FX1, b) for a, b in FLUES])   # chimney block
for (y0, y1) in FLUES:
    rect(FX0, y0, FX1, y1, "A-MASONRY")
line((FX0, 1980), (FX1, 2215), "A-MASONRY")
masonry(2605, 1870, 3250, 2600)           # fireplace (takka) body
rect(2710, 2020, 3250, 2470, "A-FIXT")    # firebox, opens to saunatupa
rect(2790, 2075, 3190, 2420, "A-FIXT")    # firebrick lining (beaded border on the scan)
for k in range(9):
    for yy in (2047, 2445):
        msp.add_circle((2750 + k * 55, yy), 18, dxfattribs={"layer": "A-FIXT"})
for k in range(8):
    msp.add_circle((2750, 2075 + k * 50), 18, dxfattribs={"layer": "A-FIXT"})
for k in range(1, 5):
    y = 2020 + k * 90
    line((2760, y), (3150, y), "A-FIXT")
rect(3250, 1850, 3660, 2600, "A-FIXT")    # hearth / floor protection
text("≥230", 3540, 2220, rot=90)
text("KJ", 2690, 2760)

# ---------------------------------------------------------------- fixtures
rect(1555, 2205, 2165, 2805, "A-FIXT")    # kiuas (sauna stove)
line((1555, 2205), (2165, 2805), "A-FIXT")
PATA_C, PATA_R = (1715, 1715), 295        # pata (water heater): tangent to beam II, clear of the partition
msp.add_circle(PATA_C, PATA_R, dxfattribs={"layer": "A-FIXT"})
_d = PATA_R / math.sqrt(2)
line((PATA_C[0] - _d, PATA_C[1] - _d), (PATA_C[0] + _d, PATA_C[1] + _d), "A-FIXT")
# benches (lauteet) with slats
for (y0, y1) in ((3540, 4135), (3130, 3515)):
    rect(110, y0, 2290, y1, "A-FIXT")
    x = 110 + 95
    while x < 2290:
        line((x, y0), (x, y1), "A-FIXT"); x += 95
rect(110, 2830, 790, 3130, "A-FIXT")      # step / footstool
line((110, 2960), (790, 2960), "A-FIXT")

# ---------------------------------------------------------------- doors
door((215, 2064), 270, 0, 585)            # V07/19  PH -> S
# door frame strip between wall G and the masonry partition (as on the scan)
rect(H2, 2050, 170, 2170, "A-DOOR")                       # frame post against wall G
rect(80, 2080, 118, 2140, "A-DOOR"); rect(124, 2080, 162, 2140, "A-DOOR")
line((170, 2064), (850, 2064), "A-DOOR"); line((170, 2154), (850, 2154), "A-DOOR")
line((215, 2064), (215, 2154), "A-DOOR"); line((800, 2064), (800, 2154), "A-DOOR")
text("VO7/19", 470, 1880)
door((3950, 1350), 270, 180, 750)         # KU08/19-4 saunatupa -> kuisti
text("KU08/19-4", 3600, 1120)
door((2465, 1230), 0, 270, 750)           # KU08/19-4 PH -> kuisti
# thresholds (kynnys) of the KU08/19-4 doors: outline across the wall + frame lines
FR = 35
rect(3200, 1350 - H2, 3990, 1350 + H2, "A-DOOR")
line((3200 + FR, 1350 - H2), (3200 + FR, 1350 + H2), "A-DOOR")
line((3990 - FR, 1350 - H2), (3990 - FR, 1350 + H2), "A-DOOR")
rect(2400 - H2, 420, 2400 + H2, 1230, "A-DOOR")
line((2400 - H2, 420 + FR), (2400 + H2, 420 + FR), "A-DOOR")
line((2400 - H2, 1230 - FR), (2400 + H2, 1230 - FR), "A-DOOR")
text("KU08/19-4", 2580, 830, rot=90)

# ---------------------------------------------------------------- porch, steps, deck
line((2630, -35), (3970, -35), "A-PORCH"); line((2630, 35), (3970, 35), "A-PORCH")   # railing
line((5365, 1120), (5365, -280), "A-PORCH"); line((5435, 1120), (5435, -280), "A-PORCH")
msp.add_lwpolyline([(4105, -135, 0), (5565, -135, 1), (5565, 135, 0), (4105, 135, 1)],
                   format="xyb", close=True, dxfattribs={"layer": "A-PORCH"})   # beam
for cx in (4110, 5400):                    # kierrejalka (threaded foot) = filled dot
    msp.add_circle((cx, 0), 60, dxfattribs={"layer": "A-PORCH"})
    hh = msp.add_hatch(color=256, dxfattribs={"layer": "A-PORCH"})
    hh.paths.add_edge_path().add_arc((cx, 0), 60, 0, 360)

# ---------------------------------------------------------------- symbols from the scan legend
def bolt(p, q):
    """'pultti' symbol: stem from p to a small open circle at q"""
    r = 40
    d = math.dist(p, q); ux, uy = (q[0] - p[0]) / d, (q[1] - p[1]) / d
    line(p, (q[0] - ux * r, q[1] - uy * r), "A-SYMB")
    msp.add_circle(q, r, dxfattribs={"layer": "A-SYMB"})

bolt((H2, 4375), (280, 4375))              # log-corner bolts
bolt((2400 + H2, 4375), (2615, 4375))
bolt((5400 + H2, 4350), (5670, 4350))
bolt((H2, -165), (240, -165))
bolt((2400 + H2, -175), (2645, -175))
bolt((5400 + H2, 1530), (5605, 1530))
bolt((1250, 2850 + H2), (1250, 3065))           # bolts on ceiling beam lines
bolt((4110, 2850 + H2), (4110, 3045))
bolt((1165, 1350 + H2), (1165, 1625))
for c in ((1145, 3240), (1125, 965)):      # floor drains
    msp.add_circle(c, 45, dxfattribs={"layer": "A-SYMB"})

def arrow_left(y):                         # filled arrow at inner face of wall G
    tip, back = 110, 225
    pts = [(tip, y), (back, y + 85), (back, y - 85)]
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "A-SYMB"})
    hh = msp.add_hatch(color=256, dxfattribs={"layer": "A-SYMB"})
    hh.paths.add_polyline_path(pts, is_closed=True)
    line((back, y), (330, y), "A-SYMB")
arrow_left(3790)
arrow_left(465)
msp.add_lwpolyline([(1410, 4450), (1580, 4450), (1495, 4290)], close=True,
                   dxfattribs={"layer": "A-SYMB"})   # ▽ mark on wall E
line((1495, 4450), (1495, 4570), "A-SYMB")
# entrance steps below wall B
rect(2430, -860, 3590, -60, "A-PORCH")
line((2430, -480), (3590, -480), "A-PORCH")
line((2430, -60), (3010, -330), "A-PORCH"); line((3010, -330), (3590, -60), "A-PORCH")
# steps beside wall J
rect(5470, 1600, 6300, 2380, "A-PORCH")
line((5885, 2380), (5885, 1600), "A-PORCH")
line((5470, 1830), (5885, 1600), "A-PORCH"); line((5885, 1600), (6300, 1830), "A-PORCH")
# deck outline
msp.add_lwpolyline([(3590, -735), (6305, -735), (6305, 1600)], dxfattribs={"layer": "A-PORCH"})
msp.add_lwpolyline([(3590, -600), (6170, -600), (6170, 1600)], dxfattribs={"layer": "A-PORCH"})
# roof eave (dash-dot)
# closed loop as on the scan: down the east side through the steps, out round the deck, under the steps
msp.add_lwpolyline([(-600, -600), (-600, 4800), (6000, 4800), (6000, 1635), (6410, 1635),
                    (6410, -870), (2225, -870), (2225, -600)], close=True,
                   dxfattribs={"layer": "A-EAVE"})

# ---------------------------------------------------------------- floor/ceiling beams (dash-dot double lines)
def beam(yc, x0, x1, closed_left=True, bracket_right=True, w=T):
    ya, yb = yc - w / 2, yc + w / 2
    line((x0, ya), (x1, ya), "A-BEAM"); line((x0, yb), (x1, yb), "A-BEAM")
    if closed_left:
        line((x0, ya), (x0, yb), "A-SYMB")
    if bracket_right:                       # end bracket as on the scan
        line((x1, ya), (x1, yb), "A-SYMB")
        line((x1 - 60, ya), (x1, ya), "A-SYMB"); line((x1 - 60, yb), (x1, yb), "A-SYMB")
beam(GY["C"], -250, 6020)                  # course II, in line with wall C
beam(GY["D"], -250, 5400 + 250, bracket_right=False) # course III, same overhang past J as past G
line((5400 + 250, GY["D"] - H2), (5400 + 250, GY["D"] + H2), "A-SYMB")   # closed right end of beam III
beam(GY["B"], 2465, 6020, closed_left=False)  # course I, porch part

# ---------------------------------------------------------------- room names
text("S", 750, 2550, h=TH_ROOM)
text("PH", 1150, 900, h=TH_ROOM)
text("SAUNATUPA", 4500, 2550, h=TH_ROOM)
text("KUISTI", 4600, 750, h=TH_ROOM)

# ---------------------------------------------------------------- dimensions

def dim(p1, p2, base, angle, override=None):
    """Dimension drawn as plain lines + architectural ticks + TEXT, so every CAD
    program (LibreCAD included) shows it identically. angle 0 = horizontal."""
    g, e, tk = 1.5 * SCALE, 1.5 * SCALE, 1.2 * SCALE   # ext gap, ext overshoot, tick half-size
    if angle == 0:
        yb = base[1]; a, b = sorted((p1[0], p2[0]))
        for x, y in ((p1[0], p1[1]), (p2[0], p2[1])):
            s = 1 if yb > y else -1
            line((x, y + s * g), (x, yb + s * e), "A-DIM")
        line((a - e, yb), (b + e, yb), "A-DIM")
        for x in (a, b):
            line((x - tk, yb - tk), (x + tk, yb + tk), "A-DIM")
        val = override or f"{round(b - a)}"
        text(val, (a + b) / 2, yb + 0.8 * SCALE, layer="A-DIM", align=TextEntityAlignment.BOTTOM_CENTER)
    else:
        xb = base[0]; a, b = sorted((p1[1], p2[1]))
        for x, y in ((p1[0], p1[1]), (p2[0], p2[1])):
            s = 1 if xb > x else -1
            line((x + s * g, y), (xb + s * e, y), "A-DIM")
        line((xb, a - e), (xb, b + e), "A-DIM")
        for y in (a, b):
            line((xb - tk, y - tk), (xb + tk, y + tk), "A-DIM")
        val = override or f"{round(b - a)}"
        text(val, xb - 0.8 * SCALE, (a + b) / 2, layer="A-DIM", rot=90,
             align=TextEntityAlignment.BOTTOM_CENTER)

dim((0, 4200), (5400, 4200), (0, 5300), 0)
dim((-H2, 4200), (5400 + H2, 4200), (0, 5750), 0, "5492 [92] / 5530 ø130")
for a, b in ((0, 2400), (2400, 5400), (5400, 6300)):
    dim((a, -700), (b, -700), (0, -1300), 0)
for a, b in ((1350, 4200), (0, 1350), (-700, 0)):
    dim((5400, a), (5400, b), (6900, 0), 90)
dim((5400, 0), (5400, 4200), (7300, 0), 90)
dim((0, 0), (0, 2100), (-1000, 0), 90)
dim((0, -H2), (0, 4200 + H2), (-1400, 0), 90, "4292 [92] / 4330 ø130")
dim((3500, 4200 - H2), (3500, 2450), (3500, 0), 90, "1750")

# section A markers
# as on the scan: right-angled triangle (tip to the left), a parallel cut line beside its
# vertical side, an L-shaped leg turning back toward the building, and "A" inside the L
for yb, s in ((6140, 1), (-2120, -1)):       # s = +1 north marker (clear of the 5750 dimension), -1 south
    msp.add_lwpolyline([(4100, yb), (4550, yb), (4550, yb + s * 300)], close=True,
                       dxfattribs={"layer": "A-TEXT"})
    line((4580, yb - s * 30), (4580, yb + s * 305), "A-TEXT")
    msp.add_lwpolyline([(4580, yb), (4790, yb), (4790, yb - s * 290)],
                       dxfattribs={"layer": "A-TEXT"})
    text("A", 4675, yb - s * 145, h=TH, rot=90)

# ---------------------------------------------------------------- flue detail 1:20
DX, DY, K = 8000, 600, SCALE / 20          # drawn at 1:20 inside a 1:50 sheet
def d(x, y):
    return DX + (x - 2195) * K, DY + (y - 1530) * K
x0, y0 = d(2195, 1530); x1, y1 = d(2600, 2600)
rect(x0, y0, x1, y1, "A-DETAIL")
h = msp.add_hatch(color=256, dxfattribs={"layer": "A-DETAIL"})
h.set_pattern_fill("ANSI31", scale=SCALE * 0.6)
h.paths.add_polyline_path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], is_closed=True)
for n, (fy0, fy1) in ((1, (2340, 2490)), (2, (1980, 2215)), (3, (1680, 1850))):
    a, b = d(2300, fy0); c, e = d(2475, fy1)
    h.paths.add_polyline_path([(a, b), (c, b), (c, e), (a, e)], is_closed=True)  # flue = hole in hatch
    rect(a, b, c, e, "A-DETAIL")
    line((a, b), (c, e), "A-DETAIL")
    text(str(n), c - 60, (b + e) / 2, h=TH, layer="A-DETAIL")
text("HORMIT 1:20", DX, y1 + 500, h=TH_ROOM, layer="A-DETAIL", align=TextEntityAlignment.MIDDLE_LEFT)
for i, s in enumerate(("1 KIUAS", "2 TAKKA", "3 PATA")):
    text(s, DX, y0 - 400 - i * 250, h=TH_ROOM, layer="A-DETAIL", align=TextEntityAlignment.MIDDLE_LEFT)

# ---------------------------------------------------------------- page 17 notes
TX, TY, RH = 10500, 5450, 220            # area table as aligned text columns
rows = [("ULKOSEINÄ / TILASTOT", "", "Pyöröhirsi ø130", "Höylähirsi [92]"),
        ("RAKENNUKSEN PINTA-ALA", "m²", "20.0", "20.0"), ("KERROSALA", "m²", "20.0", "20.0"),
        ("HUONEISTOALA", "m²", "17.0", "17.0"), ("TILAVUUS", "m³", "60", "60")]
for i, r in enumerate(rows):
    y = TY - i * RH
    for s, cx in zip(r, (0, 2450, 2850, 4450)):
        text(s, TX + cx, y, layer="A-NOTES", align=TextEntityAlignment.MIDDLE_LEFT)
    line((TX - 50, y - RH / 2), (TX + 5700, y - RH / 2), "A-NOTES")
NOTES = """- Paloahidastava rakennus
- Rakennus ja siihen kiinteästi liittyvät laitteet tehdään
   Suomen rakentamismääräysten mukaan.
- Rakennuksen sijainti ja korkeusasema tarkastetaan
   virallisen mittauksen yhteydessä.
- Tulisijan suojaetäisyydet ja hormiliittymät tulee hyväksyttää
   viranomaisilla, kun tulisijan tyyppi ja malli on selvillä.
   Tiedot suojaetäisyyksistä ilmenee tulisijan valmistajalta
   tai RT-kortistosta.

#YLÄPOHJA
- Kateaine
- Raakapontti
- Tuuletustila
- Tuulensuojapaperi
- Kattotuolit + min villa  100 mm
- Muovitiivistyspaperi
- Kattopaneeli  15 mm

#ULKOSEINÄ
- Pyöröhirsi ø mm 130
- Höylähirsi [ ] mm 92

#ALAPOHJA / PILARIPERUSTUS
- Lattialauta  25 mm
- Muovitiivistyspaperi
- Lattiavasat k/k 600 mm + min villa 100 mm
- Eristyspaperi ja täytepohjalauta tai levy
- Tuuletustila

#ALAPOHJA / LAATTAPERUSTUS
- Lattialauta  25 mm
- Muovitiivistyspaperi
- Lattiavasat k/k 600 mm + min villa 100 mm
- Teräsbetonilaatta n. 60 mm
- Tiivistetty sora

#JULKISIVUMATERIAALIT JA VÄRIT
1 Betoni / Rappaus   2 Hirsi   3 Lauta
4 Ulkovuorilauta   5 Kate   6 -"""
# plain single-line TEXT entities (no MTEXT codes) - headings underlined with a line
ny = TY - len(rows) * RH - 150
for s in NOTES.split("\n"):
    if s.startswith("#"):
        text(s[1:], TX, ny, layer="A-NOTES", align=TextEntityAlignment.MIDDLE_LEFT)
        line((TX, ny - 100), (TX + 3200, ny - 100), "A-NOTES")
    elif s:
        text(s, TX, ny, layer="A-NOTES", align=TextEntityAlignment.MIDDLE_LEFT)
    ny -= 200
text("SIVU 17: TILASTOT JA RAKENNETYYPIT", 10500, 5900, h=TH_ROOM, layer="A-NOTES",
     align=TextEntityAlignment.MIDDLE_LEFT)
text("POHJA 1:50", 0, -2900, h=5 * SCALE, align=TextEntityAlignment.MIDDLE_LEFT)

# ---------------------------------------------------------------- A3 sheet with 1:50 viewport
lay = doc.layouts.new("A3 1-50")
lay.page_setup(size=(420, 297), margins=(5, 5, 5, 5), units="mm")
lay.add_viewport(center=(210, 150), size=(400, 270), view_center_point=(6450, 1500),
                 view_height=270 * SCALE)
doc.set_modelspace_vport(height=9500, center=(6450, 1500))
doc.saveas(OUT)                       # clean drawing, no scan content
print("saved", OUT)

# ---------------------------------------------------------------- scan underlay + trace
# (reference file: clean drawing + scan underlay + trace)
for name, col in (("SCAN-IMAGE", 7), ("SCAN-TRACE", 252)):
    doc.layers.add(name, color=col)
sys.path.insert(0, HERE)
X0, X1, Y0, Y1, RES = -2000, 6500, -2500, 5850, 3.0      # mm extent, mm per pixel
pdf = pymupdf.open(PDF)
pix = pdf[15].get_pixmap(dpi=300, clip=pymupdf.Rect(250, 170, 730, 640), colorspace=pymupdf.csGRAY)
src = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width)

def lin(v, xs, ys):
    """piecewise-linear with linear extrapolation, vectorised"""
    v = np.asarray(v, float); out = np.interp(v, xs, ys)
    lo = v < xs[0]; hi = v > xs[-1]
    out[lo] = ys[0] + (v[lo] - xs[0]) * (ys[1] - ys[0]) / (xs[1] - xs[0])
    out[hi] = ys[-1] + (v[hi] - xs[-1]) * (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
    return out

W = int((X1 - X0) / RES); Hh = int((Y1 - Y0) / RES)
xm = X0 + (np.arange(W) + 0.5) * RES
ym = Y1 - (np.arange(Hh) + 0.5) * RES
px = lin(xm, [0, 2400, 5400], [473, 1043, 1740])
ey = 384.5 + (px - 600) * 13 / 975
PX = np.tile(px, (Hh, 1)).astype(np.float32)
PY = np.empty((Hh, W), np.float32)
for j in range(W):   # y mapping depends on column (skew of wall E)
    PY[:, j] = lin(ym, [0, 1350, 4200], [1374, 1059.5, ey[j]])
warp = cv2.remap(src, PX, PY, cv2.INTER_LINEAR, borderValue=255)
cv2.imwrite(IMG, warp)

idef = doc.add_image_def(filename=os.path.basename(IMG), size_in_pixel=(W, Hh))
msp.add_image(idef, insert=(X0, Y0), size_in_units=(W * RES, Hh * RES),
              dxfattribs={"layer": "SCAN-IMAGE"})

ink = (warp < 140).astype(np.uint8)
cnts, _ = cv2.findContours(ink, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
n = 0
for c in cnts:
    if cv2.contourArea(c) < 3 and len(c) < 6:
        continue
    a = cv2.approxPolyDP(c, 0.8, True).reshape(-1, 2)
    if len(a) < 2:
        continue
    pts = [(X0 + (u + 0.5) * RES, Y1 - (v + 0.5) * RES) for u, v in a]
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "SCAN-TRACE"})
    n += 1
print("trace polylines:", n)
doc.saveas(REF)
print("saved", REF)

