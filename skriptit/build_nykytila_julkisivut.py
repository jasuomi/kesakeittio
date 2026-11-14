"""Redraw PDF page 15 (sauna elevations SIVU 1/2, PAATY 1/2 and section A-A, 1:50) as a
1:1 DXF in millimetres.

Each view is drawn in its own local system (u = horizontal position in mm along the facade,
using the floor-plan grid values; z = height in mm, 0.000 = underside of the bottom log)
and placed on the sheet exactly where it sits on the A3 page, so the model space is the
page at 1:50 (21 000 x 14 840 mm).

Values are taken from the levels on the drawing (N+3.300 ridge, +2.800, +2.400, +2.240
wall top, +0.190, +0.165, 0.000), the floor plan (grid, openings, chimney, eaves) and,
for undimensioned details, measured from the 300 dpi scan (approx. +-30 mm).

Output: nykytila/sauna_nykytila_julkisivut_1-50.dxf
"""
import math
import os

import ezdxf
from ezdxf.enums import TextEntityAlignment

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "nykytila", "sauna_nykytila_julkisivut_1-50.dxf")

SCALE = 50
PX = 25.4 / 300 * SCALE          # one 300-dpi scan pixel on the 1:50 page, in model mm
PAGE_H = 3506 * PX               # page height in model mm
TH = 2.5 * SCALE
TH_TITLE = 3.5 * SCALE

COURSE = 112                     # log course height (20 courses = 2240 = N+2.240)
R_LOG = COURSE / 2
RIDGE = 3300                     # N+3.300
GROUND = -300
TERRACE_EDGE = 6302             # outer edge of the east terrace (slab runs to here)
H2 = 65                          # half log (outer wall face from the grid line)
TAN = math.tan(math.radians(22.5))
UC = 2100                        # ridge line in plan y (gable views)
ROOF_T = 130                     # roof band thickness (vertical)
TRIM = 220                       # gable logs stop this far below the roof surface
CHIM_TOP = 4030

doc = ezdxf.new("R2010", setup=True)
doc.header["$INSUNITS"] = 4
doc.header["$MEASUREMENT"] = 1
doc.header["$LTSCALE"] = 10
doc.header["$LWDISPLAY"] = 1
doc.header["$PLIMMIN"] = (0, 0)
doc.header["$PLIMMAX"] = (420, 297)
doc.header["$PSVPSCALE"] = 1 / SCALE
msp = doc.modelspace()

LAYERS = {   # name: (colour, linetype, lineweight 1/100 mm)
    "E-GROUND": (7, None, 50), "E-WALL": (7, None, 35), "E-LOG": (8, None, 18),
    "E-ROOF": (7, None, 35), "E-OPEN": (4, None, 25), "E-PORCH": (30, None, 25),
    "E-CHIM": (7, None, 35), "E-MASONRY": (8, None, 18), "E-INSUL": (6, None, 18),
    "E-CUT": (7, None, 50), "E-FOUND": (7, None, 25), "E-HIDDEN": (9, None, 18),
    "E-LEVEL": (2, None, 18), "E-TEXT": (7, None, 25),
}
for name, (color, lt, lw) in LAYERS.items():
    lay = doc.layers.add(name, color=color)
    lay.dxf.lineweight = lw
    if lt:
        lay.dxf.linetype = lt


# ---------------------------------------------------------------- geometry helpers
def clip_seg(p, q, box):
    """Liang-Barsky clip of segment p-q to box (u0, z0, u1, z1); None if outside."""
    (x0, y0), (x1, y1) = p, q
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for pp, qq in ((-dx, x0 - box[0]), (dx, box[2] - x0), (-dy, y0 - box[1]), (dy, box[3] - y0)):
        if pp == 0:
            if qq < 0:
                return None
        else:
            t = qq / pp
            if pp < 0:
                t0 = max(t0, t)
            else:
                t1 = min(t1, t)
    if t0 >= t1:
        return None
    return (x0 + t0 * dx, y0 + t0 * dy), (x0 + t1 * dx, y0 + t1 * dy)


def poly_span(poly, z, horizontal=True):
    """Interval where a horizontal (or vertical) line at z crosses a convex polygon."""
    hits = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        if not horizontal:
            a, b = (a[1], a[0]), (b[1], b[0])
        if (a[1] - z) * (b[1] - z) <= 0 and a[1] != b[1]:
            t = (z - a[1]) / (b[1] - a[1])
            hits.append(a[0] + t * (b[0] - a[0]))
    return (min(hits), max(hits)) if len(hits) >= 2 else None


def _inward(poly):
    cx = sum(p[0] for p in poly) / len(poly); cy = sum(p[1] for p in poly) / len(poly)
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        nx, ny = -(b[1] - a[1]), b[0] - a[0]
        if nx * (cx - a[0]) + ny * (cy - a[1]) < 0:
            nx, ny = -nx, -ny
        out.append((a, nx, ny))
    return out


def seg_in_poly(p, q, poly):
    """Cyrus-Beck: parameter interval of p-q inside a convex polygon (strict interior)"""
    t0, t1 = 0.0, 1.0
    d = (q[0] - p[0], q[1] - p[1])
    for a, nx, ny in _inward(poly):
        num = nx * (p[0] - a[0]) + ny * (p[1] - a[1]) - 0.5
        den = nx * d[0] + ny * d[1]
        if abs(den) < 1e-12:
            if num < 0:
                return None
            continue
        t = -num / den
        if den > 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 >= t1:
            return None
    return (t0, t1)


def point_in_poly(u, z, poly):
    return all(nx * (u - a[0]) + ny * (z - a[1]) > 0.5 for a, nx, ny in _inward(poly))


def subtract(intervals, cut):
    out = []
    for a, b in intervals:
        if cut[1] <= a or cut[0] >= b:
            out.append((a, b))
        else:
            if cut[0] > a:
                out.append((a, cut[0]))
            if cut[1] < b:
                out.append((cut[1], b))
    return out


class View:
    """Local (u, z) mm -> model space. Placement from the scan crop: crop origin on the
    page (cx, cy), the pixel column px_ref that shows u_ref, u direction (+1 / -1) and
    the pixel row py0 that shows z = 0."""

    def __init__(self, cx, cy, px_ref, u_ref, sx, direction, py0, sy=4.24):
        self.X0 = (cx + px_ref) * PX
        self.Y0 = PAGE_H - (cy + py0) * PX
        self.u_ref, self.d = u_ref, direction
        self.px_ref, self.sx, self.py0, self.sy = px_ref, sx, py0, sy
        self.occ = []                      # convex polygons hiding background lines

    def M(self, u, z):
        return (self.X0 + self.d * (u - self.u_ref), self.Y0 + z)

    def P(self, px, py):
        """scan crop pixel -> local (u, z), rounded to 5 mm"""
        u = self.u_ref + self.d * (px - self.px_ref) * self.sx
        z = (self.py0 - py) * self.sy
        return (round(u / 5) * 5, round(z / 5) * 5)

    # ---- primitives
    def line(self, p, q, layer, occl=False):
        """segment p-q; with occl=True the parts behind occluder polygons are left out"""
        segs = [(0.0, 1.0)]
        if occl:
            for poly in self.occ:
                iv = seg_in_poly(p, q, poly)
                if iv:
                    segs = subtract(segs, iv)
        L = math.dist(p, q)
        for a, b in segs:
            if (b - a) * L > 2:
                pa = (p[0] + a * (q[0] - p[0]), p[1] + a * (q[1] - p[1]))
                pb = (p[0] + b * (q[0] - p[0]), p[1] + b * (q[1] - p[1]))
                msp.add_line(self.M(*pa), self.M(*pb), dxfattribs={"layer": layer})

    def hidden_pt(self, u, z):
        return any(point_in_poly(u, z, poly) for poly in self.occ)

    def pl(self, pts, layer, closed=False):
        msp.add_lwpolyline([self.M(*p) for p in pts], close=closed, dxfattribs={"layer": layer})

    def rect(self, u0, z0, u1, z1, layer, occlude=False):
        pts = [(u0, z0), (u1, z0), (u1, z1), (u0, z1)]
        if self.occ:
            for i in range(4):
                self.line(pts[i], pts[(i + 1) % 4], layer, occl=True)
        else:
            self.pl(pts, layer, closed=True)
        if occlude:
            self.hide_rect(u0, z0, u1, z1)

    def hide_rect(self, u0, z0, u1, z1):
        a, b = sorted((u0, u1)); c, d = sorted((z0, z1))
        self.occ.append([(a, c), (b, c), (b, d), (a, d)])

    def circle(self, u, z, r, layer, ztop=None):
        c = self.M(u, z)
        if ztop is None or z + r <= ztop:
            msp.add_circle(c, r, dxfattribs={"layer": layer})
        elif z - r < ztop:                         # keep only the part below ztop
            th = math.degrees(math.asin((ztop - z) / r))
            a0, a1 = 180 - th, th
            if self.d < 0:
                a0, a1 = a0, a1                    # symmetric about the vertical axis
            msp.add_arc(c, r, a0, a1, dxfattribs={"layer": layer})

    def text(self, s, u, z, h=TH, layer="E-TEXT", rot=0, align=TextEntityAlignment.BOTTOM_LEFT):
        msp.add_text(s, height=h, rotation=rot, dxfattribs={"layer": layer, "style": "OpenSans"}
                     ).set_placement(self.M(u, z), align=align)

    def tpl(self, pix, layer, closed=False):
        """polyline traced in scan pixels"""
        self.pl([self.P(*p) for p in pix], layer, closed)

    # ---- building parts
    def logs(self, u0, u1, z0, z1, phase, ztop_fn=None, edges=(True, True)):
        """horizontal log-course lines every COURSE from phase, clipped below ztop_fn(u)"""
        k = math.ceil((z0 - phase) / COURSE)
        while True:
            z = phase + k * COURSE
            if z >= z1:
                break
            if z > z0:
                a, b = u0, u1
                if ztop_fn:
                    a, b = ztop_fn(z, u0, u1)
                if b > a:
                    self.line((a, z), (b, z), "E-LOG", occl=True)
            k += 1
        self.line((u0, z0), (u1, z0), "E-WALL", occl=True)
        if edges is True or edges is False:
            edges = (edges, edges)
        for u, on in zip((u0, u1), edges):
            if on:
                top = z1
                if ztop_fn:
                    top = min(gable_top(u, TRIM), z1)
                self.line((u, z0), (u, top), "E-WALL", occl=True)

    def stack(self, u, z0, z1, ztop=None):
        """log ends of the crossing wall: circles centred 56 + 112k (call before logs)"""
        k = 0
        col = []
        while True:
            zc = R_LOG + k * COURSE
            if zc - R_LOG >= z1 - 1:
                break
            if zc >= z0:
                hidden = any(self.hidden_pt(u, zc + dz) for dz in (-R_LOG + 5, 0, R_LOG - 5))
                if not hidden:
                    self.circle(u, zc, R_LOG, "E-WALL", ztop=ztop)
                    col.append(zc)
            k += 1
        if col:
            self.hide_rect(u - R_LOG, min(col) - R_LOG, u + R_LOG, max(col) + R_LOG)

    def slab(self, u0, u1, cut=False):
        """continuous floor slab under the building, ground level to 0.000;
        in the section the cut slab is hatched"""
        self.rect(u0, GROUND, u1, 0, "E-FOUND")
        if cut:
            h = msp.add_hatch(color=256, dxfattribs={"layer": "E-FOUND"})
            h.set_pattern_fill("ANSI31", scale=SCALE * 0.6)
            h.paths.add_polyline_path([self.M(u0, GROUND), self.M(u1, GROUND), self.M(u1, 0),
                                       self.M(u0, 0)], is_closed=True)

    def pier(self, u, w=200, top=0):
        self.rect(u - w / 2, GROUND, u + w / 2, top, "E-FOUND")

    def ground(self, u0, u1):
        self.line((u0, GROUND), (u1, GROUND), "E-GROUND")

    def chimney(self, u0, u1, zbot0, zbot1=None, top=CHIM_TOP, closed=False):
        """closed=True draws the line where the chimney meets the roof (long-side views)"""
        zbot1 = zbot0 if zbot1 is None else zbot1
        self.pl([(u0, zbot0), (u0, top), (u1, top), (u1, zbot1)], "E-CHIM", closed=closed)

    def window(self, o0, o1, frame_z0, frame_z1, casing, casing_z0, casing_z1,
               mull_u=None, mull_z=None, header=None, brackets=None, sill=False):
        """casings (vertical boards) + frame + glass with mullions; occludes the logs"""
        c0, c1 = o0 - casing, o1 + casing
        for a, b in ((c0, o0), (o1, c1)):
            self.rect(a, casing_z0, b, casing_z1, "E-OPEN")
        self.rect(o0, frame_z0, o1, frame_z1, "E-OPEN")
        g = 40
        self.rect(o0 + g, frame_z0 + g, o1 - g, frame_z1 - g, "E-OPEN")
        if mull_u is not None:
            self.rect(mull_u - 18, frame_z0 + g, mull_u + 18, frame_z1 - g, "E-OPEN")
        if mull_z is not None:
            self.rect(o0 + g, mull_z - 15, o1 - g, mull_z + 15, "E-OPEN")
        if sill:
            self.line((o0, frame_z0 - 10), (o1, frame_z0 - 10), "E-OPEN")
        if header:
            hu0, hz0, hu1, hz1 = header
            self.rect(hu0, hz0, hu1, hz1, "E-OPEN")
            self.rect(hu0 + 25, hz1, hu1 - 25, hz1 + 20, "E-OPEN")
        self.hide_rect(c0, casing_z0, o0, casing_z1); self.hide_rect(o1, casing_z0, c1, casing_z1)
        self.hide_rect(o0, frame_z0, o1, frame_z1)
        if header:
            self.hide_rect(*header)
        if brackets:
            for bu in brackets[0]:
                self.rect(bu - 12, brackets[1], bu + 12, brackets[2], "E-OPEN")
                h = msp.add_hatch(color=256, dxfattribs={"layer": "E-OPEN"})
                h.paths.add_polyline_path([self.M(bu - 12, brackets[1]), self.M(bu + 12, brackets[1]),
                                           self.M(bu + 12, brackets[2]), self.M(bu - 12, brackets[2])],
                                          is_closed=True)

    def herringbone(self, u0, z0, u1, z1, step=70):
        """lower door panel: concentric diamonds clipped to the panel (chevrons + centre)"""
        self.rect(u0, z0, u1, z1, "E-OPEN")
        cu, cz = (u0 + u1) / 2, (z0 + z1) / 2
        r = step * 0.6
        while r < (u1 - u0) / 2 + (z1 - z0) / 2:
            pts = [(cu - r, cz), (cu, cz + r), (cu + r, cz), (cu, cz - r)]
            for i in range(4):
                s = clip_seg(pts[i], pts[(i + 1) % 4], (u0, z0, u1, z1))
                if s:
                    self.line(s[0], s[1], "E-OPEN", occl=True)
            r += step

    def door(self, f0, f1, z0, z1, glass, mull_u, mull_z, panel, casing=None, header=None,
             brackets=None):
        for a, b in (casing or ()):
            self.rect(a, z0, b, z1, "E-OPEN")
        self.rect(f0, z0, f1, z1, "E-OPEN")
        gu0, gz0, gu1, gz1 = glass
        self.rect(gu0, gz0, gu1, gz1, "E-OPEN")
        self.rect(mull_u - 15, gz0, mull_u + 15, gz1, "E-OPEN")
        self.rect(gu0, mull_z - 15, gu1, mull_z + 15, "E-OPEN")
        self.herringbone(*panel)
        if header:
            self.rect(*header, "E-OPEN")
        if brackets:
            for bu in brackets[0]:
                self.rect(bu - 12, brackets[1], bu + 12, brackets[2], "E-OPEN")
        for a, b in (casing or ()):
            self.hide_rect(a, z0, b, z1)
        self.hide_rect(f0, z0, f1, z1)
        if header:
            self.hide_rect(*header)

    def x_bay(self, u0, u1, z0, z1, w=45):
        """railing bay with an X brace made of two boards"""
        for (a, b) in (((u0, z1), (u1, z0)), ((u0, z0), (u1, z1))):
            dx, dz = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dz)
            nx, nz = -dz / L * w / 2, dx / L * w / 2
            for s in (1, -1):
                p = (a[0] + s * nx, a[1] + s * nz); q = (b[0] + s * nx, b[1] + s * nz)
                c = clip_seg(p, q, (u0, z0, u1, z1))
                if c:
                    self.line(c[0], c[1], "E-PORCH", occl=True)
            self.occ.append([(a[0] + nx, a[1] + nz), (b[0] + nx, b[1] + nz),
                             (b[0] - nx, b[1] - nz), (a[0] - nx, a[1] - nz)])

    def level(self, z, u0, u1, label, tu, tz=None):
        self.line((u0, z), (u1, z), "E-LEVEL")
        tip = (u1 - 0.22 * (u1 - u0), z)
        self.pl([tip, (tip[0] - 50, z + 110), (tip[0] + 50, z + 110)], "E-LEVEL", closed=True)
        self.text(label, tu, z + 230 if tz is None else tz, layer="E-LEVEL")


def gable_top(u, below=0):
    return RIDGE - abs(u - UC) * TAN - below


def gable_clip(below):
    def fn(z, u0, u1):
        span = (RIDGE - below - z) / TAN
        if span <= 0:
            return (0, 0)
        return (max(u0, UC - span), min(u1, UC + span))
    return fn


def gable_roof(v, u_left, u_right, extra_marks=()):
    """roof band of a gable view: top surface, covering line, underside, end cuts, trim"""
    def zt(u):
        return gable_top(u)
    for off, lay in ((0, "E-ROOF"), (35, "E-ROOF"), (ROOF_T, "E-ROOF")):
        v.pl([(u_left, zt(u_left) - off), (UC, RIDGE - off), (u_right, zt(u_right) - off)], lay)
    # perpendicular end cuts
    c, s = math.cos(math.radians(22.5)), math.sin(math.radians(22.5))
    for ue, sign in ((u_left, -1), (u_right, 1)):
        t = ROOF_T * c
        v.line((ue, zt(ue)), (ue - sign * t * s, zt(ue) - t * c), "E-ROOF")
    for um in extra_marks:
        v.line((um, zt(um)), (um, zt(um) - ROOF_T), "E-ROOF")
    # roof band hides what is behind it
    for ue in (u_left, u_right):
        a, b = sorted((ue, UC))
        v.occ.append([(a, zt(a)), (b, zt(b)), (b, zt(b) - ROOF_T), (a, zt(a) - ROOF_T)])


def gable_trim(v, u0, u1):
    """line where the gable logs stop under the roof boards"""
    pts = [(u0, gable_top(u0, TRIM))]
    if u0 < UC < u1:
        pts.append((UC, RIDGE - TRIM))
    pts.append((u1, gable_top(u1, TRIM)))
    v.pl(pts, "E-WALL")


def purlin(v, u, occl=True):
    for zc in (2632, 2744):
        v.circle(u, zc, R_LOG, "E-WALL")
    v.hide_rect(u - R_LOG, 2632 - R_LOG, u + R_LOG, 2744 + R_LOG)


# ================================================================ SIVU 1 (north, wall E)
v = View(500, 100, 271, 5400, 4.196, -1, 981, 4.25)
v.ground(6550, -1100)
# east steps and their railing (in front of the wall)
v.rect(6222, 918, 6370, 960, "E-PORCH", occlude=True)              # post cap
v.rect(6235, 153, 6330, 918, "E-PORCH", occlude=True)              # post
v.rect(5465, 790, 6235, 952, "E-PORCH", occlude=True)              # handrail board
v.line((6222, 790), (5669, 450), "E-PORCH"); v.line((6201, 153), (5719, 472), "E-PORCH")
v.line((5669, 450), (5465, 450), "E-PORCH")
for z0, z1 in ((-17, 153), (-166, -17), (GROUND, -166)):
    v.rect(5455, z0, 6327, z1, "E-PORCH", occlude=True)
# roof (fascia hides the top of the wall)
v.rect(-600, 2010, 6000, 2150, "E-ROOF", occlude=True)
v.line((-600, 2125), (6000, 2125), "E-ROOF")
v.pl([(-600, 2150), (-600, RIDGE), (2195, RIDGE)], "E-ROOF")          # ridge hidden by the chimney
v.pl([(2605, RIDGE), (6000, RIDGE), (6000, 2150)], "E-ROOF")
v.rect(-600, 2150, -450, 3285, "E-ROOF"); v.rect(5850, 2150, 6000, 3285, "E-ROOF")   # verge boards
v.rect(6000, 1890, 6410, 3110, "E-ROOF")                           # roof over the east steps
v.hide_rect(-600, 2010, 6000, RIDGE)
v.chimney(2195, 2605, RIDGE - (2600 - UC) * TAN, closed=True)
# wall
for u in (0, 2400, 5400):
    v.stack(u, 0, 2010, ztop=2010)
v.logs(-230, 5630, 0, 2010, 0)
v.slab(-H2, TERRACE_EDGE)                                         # floor slab, under the terrace too

# ================================================================ SIVU 2 (south)
v = View(400, 1220, 186, 0, 4.19, 1, 997)
v.ground(-780, 7000)
# porch railing, deck and steps (front-most)
for a, b in ((3662, 3779), (4923, 5028), (6189, 6293)):
    v.rect(a, 178, b, 814, "E-PORCH", occlude=True)
v.rect(3599, 814, 6302, 962, "E-PORCH", occlude=True)               # top rail
v.rect(3599, 136, 6302, 178, "E-PORCH", occlude=True)               # bottom rail
v.rect(3599, 0, 6302, 136, "E-PORCH", occlude=True)                 # deck rim (N+0.165)
v.x_bay(3779, 4923, 178, 814); v.x_bay(5028, 6189, 178, 814)
v.rect(2510, 136, 3600, 170, "E-PORCH", occlude=True)              # entrance steps
for z0, z1 in ((-17, 136), (-170, -17), (GROUND, -170)):
    v.rect(2510, z0, 3600, z1, "E-PORCH", occlude=True)
v.line((2510, 8), (3600, 8), "E-PORCH"); v.line((2510, -140), (3600, -140), "E-PORCH")
# roof
v.rect(-600, 2010, 2225, 2140, "E-ROOF", occlude=True)              # fascia, west part
v.line((-600, 2125), (2225, 2125), "E-ROOF")
v.rect(2225, 1900, 6410, 2030, "E-ROOF", occlude=True)              # fascia over the porch (lower)
v.line((2225, 2015), (6410, 2015), "E-ROOF")
v.pl([(-600, 2140), (-600, RIDGE), (2195, RIDGE)], "E-ROOF")
v.line((2605, RIDGE), (5850, RIDGE), "E-ROOF")
v.pl([(5850, RIDGE), (6000, RIDGE), (6000, 3110), (6410, 3110), (6410, 2030)], "E-ROOF")
v.rect(5850, 3110, 6000, RIDGE, "E-ROOF")                           # east verge (main roof)
v.line((2225, 2030), (2225, 2140), "E-ROOF")
v.rect(-600, 2140, -450, 3280, "E-ROOF")                            # west verge
v.rect(6235, 2030, 6385, 3100, "E-ROOF")                            # verge of the steps roof
v.hide_rect(-600, 2010, 2225, RIDGE); v.hide_rect(2225, 1900, 6410, RIDGE)
v.chimney(2195, 2605, RIDGE - (UC - 1530) * TAN, closed=True)
# window in wall B (96X96)
v.window(771, 1626, 1050, 1980, 162, 929, 2010, mull_u=1200, mull_z=1560,
         brackets=((657, 1735), 1853, 1980), sill=True)
# door KU08/19-4 in wall C, seen through the porch
v.door(3226, 3905, 220, 1895, glass=(3327, 1196, 3809, 1887), mull_u=3570, mull_z=1550,
       panel=(3250, 220, 3880, 1175), casing=[(3060, 3226), (3905, 4077)])
v.rect(4077, 178, 4161, 1900, "E-PORCH", occlude=True)              # porch post (kierrejalka)
# window in wall C (96X96)
v.window(4240, 5112, 903, 1887, 80, 971, 1900, mull_u=4636, mull_z=1550)
v.rect(5321, 165, 5447, 1900, "E-PORCH", occlude=True)              # porch post at grid J
# walls
for u in (0, 2400):
    v.stack(u, 0, 2010, ztop=2010)
v.logs(-230, 2630, 0, 2010, 0)
v.logs(2630, 3060, 170, 1900, 0, edges=False)                       # wall C behind the porch
v.logs(5447, 5630, 170, 1900, 0)
v.rect(5229, 165, 5321, 1900, "E-WALL")                             # log ends of wall J
for k in range(2, 17):
    v.line((5229, R_LOG + k * COURSE), (5321, R_LOG + k * COURSE), "E-LOG")
v.line((2630, 0), (2630, 1900), "E-WALL")
v.slab(-H2, TERRACE_EDGE)                                         # slab continues under the terrace

# ================================================================ PAATY 1 (west, wall G)
v = View(2470, 100, 429, 4200, 4.13, -1, 979)
v.ground(5765, -1170)
# south porch end (right)
v.rect(-740, 920, -595, 961, "E-PORCH", occlude=True)               # post cap
v.rect(-637, 38, -595, 920, "E-PORCH", occlude=True)                # post
v.rect(-244, 801, -595, 961, "E-PORCH", occlude=True)               # rail
v.line((-264, 598), (-595, 801), "E-PORCH"); v.line((-264, 399), (-580, 187), "E-PORCH")
v.rect(-244, 123, -616, 165, "E-PORCH", occlude=True)               # deck
v.pl([(-244, 131), (-398, 131), (-398, 4), (-637, 4), (-637, -140), (-926, -140), (-926, GROUND)],
     "E-PORCH")
# roof, chimney
gable_roof(v, 4800, -870, extra_marks=(-600,))
v.chimney(1530, 2600, gable_top(1530), gable_top(2600))
# window 55X55 in wall G
v.window(2845, 3391, 1090, 2010, 110, 907, 2073, mull_z=1530,
         header=(2668, 2082, 3576, 2171), brackets=((2783, 3465), 1844, 2070))
# wall + gable
for u in (0, 4200):
    v.stack(u, 0, 2240)
for u in (1350, 2850):
    purlin(v, u)
v.logs(-230, 4430, 0, RIDGE, R_LOG, ztop_fn=gable_clip(TRIM))
gable_trim(v, -230, 4430)
v.slab(-H2, 4200 + H2)

# ================================================================ PAATY 2 (east, wall J)
v = View(2470, 1220, 913, 1350, 4.137, 1, 994)
v.ground(-2260, 5475)
# south porch (front-most): posts, rails, X braces, deck, steps
for a, b in ((-698, -586), (407, 518), (1511, 1615)):
    v.rect(a, 165, b, 801, "E-PORCH", occlude=True)
v.rect(-698, 801, 1689, 950, "E-PORCH", occlude=True)
v.rect(-698, 123, 1615, 165, "E-PORCH", occlude=True)
v.rect(-698, 0, 1615, 123, "E-PORCH", occlude=True)
v.x_bay(-586, 407, 165, 801); v.x_bay(518, 1511, 165, 801)
v.pl([(-586, -4), (-586, -153), (-863, -153), (-863, GROUND)], "E-PORCH")
# east steps (side profile)
v.pl([(1606, 165), (1875, 165), (1875, -4), (2165, -4), (2165, -153), (2475, -153), (2475, GROUND)],
     "E-PORCH")
v.hide_rect(1606, GROUND, 1875, 165); v.hide_rect(1875, GROUND, 2165, -4)
v.hide_rect(2165, GROUND, 2475, -153)
# material callouts 1-5
for n, px, py, a, b in (("5", 1535, 345, 1415, 1550), ("3", 1825, 497, 1740, 1835),
                        ("4", 1820, 633, 1400, 1830), ("2", 1825, 868, 1650, 1845),
                        ("1", 1815, 1040, 1615, 1830)):
    pa, pb = v.P(a, py), v.P(b, py)
    v.line(pa, pb, "E-TEXT")
    v.text(n, v.P(px, py)[0], pa[1] + 30, align=TextEntityAlignment.BOTTOM_CENTER)
# roof, chimney
gable_roof(v, -870, 4800, extra_marks=(-600,))
v.chimney(1530, 2600, gable_top(1530), gable_top(2600))
# window 96X96 in wall J
v.window(2310, 3260, 1068, 1980, 120, 907, 2094, mull_u=2790, mull_z=1528,
         header=(2124, 2094, 3448, 2166), brackets=((2256, 3311), 1840, 2082))
# door KU08/19-4 (PH) in wall H behind the porch
v.door(427, 1118, 165, 2052, glass=(518, 1204, 1027, 1925), mull_u=773, mull_z=1560,
       panel=(445, 165, 1100, 1170), casing=[(254, 410)],
       header=(230, 2137, 1130, 2166), brackets=((290,), 1900, 2137))
# corner board at B with the top log end
v.rect(-50, 165, 55, 2130, "E-WALL", occlude=True)
v.circle(0, 2185, 55, "E-WALL")
# walls
v.stack(1350, 0, 2800)
v.stack(4200, 0, 2240)
purlin(v, 2850)
v.logs(-230, 1350, 165, RIDGE, R_LOG, ztop_fn=gable_clip(TRIM), edges=(True, False))  # wall H face
v.logs(1350, 4430, 0, RIDGE, R_LOG, ztop_fn=gable_clip(TRIM), edges=(False, True))   # wall J
gable_trim(v, -230, 4430)
v.slab(-H2, 4200 + H2)

# ================================================================ LEIKKAUS A-A (x = 4530, looking west)
v = View(2470, 2270, 921, 1350, 4.148, 1, 925)
v.ground(-1600, 5790)
# porch (front-most)
v.rect(-730, 900, -590, 940, "E-PORCH", occlude=True)
v.rect(-720, 165, -600, 900, "E-PORCH", occlude=True)
v.rect(-707, 0, 1290, 165, "E-PORCH", occlude=True)
v.line((-707, 125), (1290, 125), "E-PORCH")
v.rect(-60, 165, 60, 2133, "E-WALL", occlude=True)                  # corner board at B
v.circle(-5, 2190, 56, "E-WALL")
# door KU08/19-4 (PH) in wall H
v.door(375, 1160, 225, 2050, glass=(508, 1179, 1006, 1921), mull_u=757, mull_z=1550,
       panel=(413, 225, 1114, 1158), casing=[(284, 375), (1160, 1250)],
       header=(170, 2120, 1265, 2205), brackets=((284, 1192), 1895, 2120))
# cut walls: C (with the window) and E - log sections as circles
CUT_C = [z for z in (R_LOG + k * COURSE for k in range(9))] + [2240, 2352, 2464, 2576, 2688]
for zc in CUT_C:
    v.circle(1350, zc, R_LOG, "E-CUT")
v.rect(1290, 1120, 1410, 2184, "E-CUT")                             # window 96X96 in the cut
v.line((1325, 1120), (1325, 2184), "E-OPEN"); v.line((1375, 1120), (1375, 2184), "E-OPEN")
v.stack(4200, 0, 2240)
v.hide_rect(1294, 0, 1406, 2800); v.hide_rect(4144, 0, 4256, 2240)
for k in range(1, 20):                                               # wall E overhang beyond
    v.line((4256, k * COURSE), (4430, k * COURSE), "E-LOG")
v.line((4430, 0), (4430, 2240), "E-WALL"); v.line((4256, 2240), (4430, 2240), "E-WALL")
# floor (insulation symbol) and ceiling


def insulation(v, u0, u1, z0, z1, along=None):
    """'rope' insulation symbol: band outline + row of loops"""
    v.rect(u0, z0, u1, z1, "E-INSUL")
    n = int((u1 - u0) // 40)
    r = (z1 - z0) / 2 - 8
    w = (u1 - u0) / n
    for i in range(n):
        cu = u0 + (i + 0.5) * w
        msp.add_arc(v.M(cu, (z0 + z1) / 2), w / 2, 0, 180, dxfattribs={"layer": "E-INSUL"})
        v.line((cu - w / 2, z0 + 8), (cu - w / 2, (z0 + z1) / 2), "E-INSUL")
        v.line((cu + w / 2, z0 + 8), (cu + w / 2, (z0 + z1) / 2), "E-INSUL")


insulation(v, 1410, 4140, 15, 150)
insulation(v, 1410, 2850, 2790, 2921)
# sloped insulation under the roof between purlin III and wall E
ua, ub = 2900, 4250
for off in (ROOF_T, ROOF_T + 130):
    v.line((ua, gable_top(ua) - off), (ub, gable_top(ub) - off), "E-INSUL")
k = ua + 40
while k < ub - 20:
    z = gable_top(k) - ROOF_T - 65
    msp.add_circle(v.M(k, z), 30, dxfattribs={"layer": "E-INSUL"})
    k += 75
purlin(v, 2850)
# masonry (chimney / fireplace wall face) between C and 3316
v.rect(1410, 150, 3316, 2790, "E-MASONRY")
z = 150 + 70
while z < 2790:
    v.line((1410, z), (3316, z), "E-MASONRY"); z += 70
for u in (1680, 1945, 2227, 2492, 2766, 3036):
    v.line((u, 150), (u, 2790), "E-MASONRY")
# log wall H inside saunatupa and above its ceiling
v.logs(3316, 4144, 150, 2061, R_LOG, edges=False)
v.line((3316, 150), (3316, 2061), "E-WALL")
v.line((2686, 2061), (4144, 2061), "E-WALL")
v.logs(2686, 4144, 2061, 2730, R_LOG, ztop_fn=gable_clip(ROOF_T + 140), edges=False)
v.line((2686, 2061), (2686, 2730), "E-WALL")
# wall H face above the porch (gable logs)
v.logs(-230, 1290, 165, RIDGE, R_LOG, ztop_fn=gable_clip(TRIM), edges=(True, False))
# roof
gable_roof(v, -870, 4800)
gable_trim(v, -230, 1290)
v.pl([(1730, 2921), (UC, RIDGE - TRIM - 10), (2450, 2921)], "E-WALL")   # attic triangle at the ridge
v.text("22,5°", 516, 2803, rot=22.5)
v.slab(-H2, 4200 + H2, cut=True)
# levels
v.level(3300, 2312, 2640, "N.+3.300", 2340)
v.level(2800, 3503, 3690, "N.+2.800", 3340)
v.level(2400, 4390, 4693, "N.+2.400", 4320)
v.level(2240, 5440, 5788, "N.+2.240", 5415)
v.level(178, -1699, -1234, "N.+0.165", -1795)
v.level(0, 4693, 5137, "0.000", 4740)
v.level(190, 2880, 3010, "+0.190", 2710)

# ================================================================ titles (page positions)
def title(s, px, py):
    msp.add_text(s, height=TH_TITLE, dxfattribs={"layer": "E-TEXT", "style": "OpenSans"}
                 ).set_placement((px * PX, PAGE_H - py * PX), align=TextEntityAlignment.BOTTOM_LEFT)


title("SIVU 1", 175, 1110)
title("PÄÄTY 1", 2515, 1110)
title("SIVU 2", 175, 2225)
title("PÄÄTY 2", 2505, 2235)
title("LEIKKAUS A-A", 2678, 3328)
title("JULKISIVUT JA LEIKKAUS A-A 1:50", 175, 3328)

# ---------------------------------------------------------------- A3 sheet with 1:50 viewport
CX, CY = 4960 * PX / 2, PAGE_H / 2
doc.header["$PINSBASE"] = (210 - CX / SCALE, 148.5 - CY / SCALE, 0)
lay = doc.layouts.new("A3 1-50")
lay.page_setup(size=(420, 297), margins=(5, 5, 5, 5), units="mm")
lay.add_viewport(center=(210, 148.5), size=(410, 287), view_center_point=(CX, CY),
                 view_height=287 * SCALE)
doc.set_modelspace_vport(height=PAGE_H * 1.05, center=(CX, CY))
doc.audit()
doc.saveas(OUT)
print("saved", OUT)
