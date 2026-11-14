"""Luonnoskuva v2: kesäkeittiö saunan päätyyn (linja J). Tuottaa SVG:n suunnitelman tarkentamiseen.
Koordinaatit kuten build_dxf.py: origo G/B, x rakennuksen pituussuunta, y poikittain (B=0, E=4200),
korot kuten build_elev_dxf.py (0.000 = pohjalaatan yläpinta / alimman hirren alapinta)."""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "kesakeittio_luonnos.svg")

# ---------------------------------------------------------------- mitoitus (mm)
SLAB_X1 = 6302                  # pohjalaatan pääty
KX1 = SLAB_X1 + 4000            # keittiön ulkoreuna (4 m laatan päädystä)
TERR_Y = -735                   # nykyisen terassin etureuna
BOARD, GAP = 120, 5             # kansilauta 28x120, rako
STRIP = 5 * (BOARD + GAP)       # porraskaista: 5 lautaa + raot = 625
FY0, FY1 = TERR_Y - STRIP, 4265  # lattian etureuna .. laatan oikea reuna
STRIP_X0 = 2430                 # kaista alkaa puretun etuportaan länsireunasta (kysymys A)
DECK = 28
JOIST = 123
P = 115
FACE_B = -65                    # rakennuksen etuseinän (B) ulkopinta = keittiön etuseinän linja
PF, PR = FACE_B + P / 2, FY1 - P / 2
YC = 2100                       # harja samassa linjassa nykyisen kanssa
PU1, PU2 = (PF + YC) / 2, (PR + YC) / 2            # välipalkit
PY_END = [PF, PU1, YC, PU2, PR]
X_IN = SLAB_X1 + P / 2          # sisäpään pilarilinja
X_OUT = KX1 - P / 2
PX = [X_IN + i * (X_OUT - X_IN) / 3 for i in range(4)]

TAN = math.tan(math.radians(22.5))
MAIN_RIDGE, MAIN_T = 3300, 130
GAP_ROOF = 40                   # rako nykyisen katon alapintaan
K_RIDGE = MAIN_RIDGE - MAIN_T - GAP_ROOF            # keittiökaton yläpinta harjalla = 3130
ROOF_BUILD = 50 + 98 / math.cos(math.radians(22.5))  # kate + ruoteet + vasa (pystymitta)
NOTCH = 30                      # vasan lovi palkin päällä
EDGE_B, PURL_B, RIDGE_B = 135, 225, 225
EAVE_Y0, EAVE_Y1 = -600, 4800   # räystäslinjat kuten päärakennuksessa
RX0, RX1 = 5800, KX1 + 500      # katon alku (nykyisen katon alla) .. päätyräystäs
HALF_WALL = 1000


def ktop(y):
    return K_RIDGE - abs(y - YC) * TAN


def mtop(y):
    return MAIN_RIDGE - abs(y - YC) * TAN


def beam_top(y):
    return ktop(y) - ROOF_BUILD + NOTCH


EDGE_BOT = beam_top(PF) - EDGE_B
PURL_BOT = beam_top(PU1) - PURL_B
RIDGE_BOT = beam_top(YC) - RIDGE_B

# lattiarunko: pituussuuntaiset palkit (y-linjat) ja poikittaiset väliin (x-linjat)
N_LONG = 6
LONG_Y = [FY0 + 24 + i * (FY1 - 24 - FY0 - 24) / (N_LONG - 1) for i in range(N_LONG)]
CROSS_CC = 500
CROSS_X = [SLAB_X1 + 24 + i * CROSS_CC for i in range(int((KX1 - SLAB_X1) / CROSS_CC) + 1)]
CROSS_X[-1] = KX1 - 24
FOOT_X = PX[1:]                                    # anturarivit pilarilinjoissa
STRIP_FOOT_X = [STRIP_X0 + 24 + i * (SLAB_X1 - STRIP_X0 - 24) / 3 for i in range(3)]
RAFT_X = []
x = RX1 - 24
while x > RX0 + 100:
    RAFT_X.append(x)
    x -= 900

svg = []
C = {"exist": "#555", "new": "#0a6e56", "del": "#c0392b", "dim": "#8a6d00", "roof": "#3c3489",
     "fill": "#e1f5ee", "strip": "#faeeda", "deck": "#eeeeee", "frame": "#993c1d", "q": "#d4537e"}


class V:
    def __init__(self, ox, oy, s, x0, y1):
        self.ox, self.oy, self.s, self.x0, self.y1 = ox, oy, s, x0, y1

    def p(self, x, y):
        return self.ox + (x - self.x0) * self.s, self.oy + (self.y1 - y) * self.s

    def poly(self, pts, col, w=1.0, fill="none", dash=None, close=False):
        d = " ".join(f"{a:.1f},{b:.1f}" for a, b in (self.p(*q) for q in pts))
        tag = "polygon" if close else "polyline"
        da = f' stroke-dasharray="{dash}"' if dash else ""
        svg.append(f'<{tag} points="{d}" fill="{fill}" stroke="{col}" stroke-width="{w}"{da}/>')

    def rect(self, x0, y0, x1, y1, col, w=1.0, fill="none", dash=None):
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], col, w, fill, dash, close=True)

    def line(self, a, b, col, w=1.0, dash=None):
        self.poly([a, b], col, w, dash=dash)

    def circle(self, x, y, r, col, fill="none"):
        a, b = self.p(x, y)
        svg.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="{r}" fill="{fill}" stroke="{col}"/>')

    def text(self, s, x, y, size=12, col="#222", anchor="middle", bold=False):
        a, b = self.p(x, y)
        fw = ' font-weight="600"' if bold else ""
        svg.append(f'<text x="{a:.1f}" y="{b:.1f}" font-size="{size}" fill="{col}" '
                   f'text-anchor="{anchor}"{fw}>{s}</text>')

    def dimh(self, x0, x1, y, off, label=None):
        yy = y + off
        self.line((x0, yy), (x1, yy), C["dim"], 0.7)
        for x in (x0, x1):
            self.line((x, y), (x, yy), C["dim"], 0.4)
            self.line((x - 60, yy - 60), (x + 60, yy + 60), C["dim"], 0.9)
        self.text(label or f"{round(x1 - x0)}", (x0 + x1) / 2, yy + 60, 11, C["dim"])

    def dimv(self, x, y0, y1, off, label=None):
        xx = x + off
        self.line((xx, y0), (xx, y1), C["dim"], 0.7)
        for y in (y0, y1):
            self.line((x, y), (xx, y), C["dim"], 0.4)
            self.line((xx - 60, y - 60), (xx + 60, y + 60), C["dim"], 0.9)
        a, b = self.p(xx - 80, (y0 + y1) / 2)
        svg.append(f'<text x="{a:.1f}" y="{b:.1f}" font-size="11" fill="{C["dim"]}" text-anchor="middle" '
                   f'transform="rotate(-90 {a:.1f} {b:.1f})">{label or round(y1 - y0)}</text>')

    def level(self, x, z, label, col):
        self.line((x - 300, z), (x + 300, z), col, 0.6)
        self.text(label, x + 350, z - 30, 10, col, anchor="start")


W, H = 1600, 2020
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {W} {H}" '
           f'font-family="Segoe UI, Arial, sans-serif">')
svg.append(f'<rect width="{W}" height="{H}" fill="white"/>')

# ================================================================ POHJA (katto + seinät)
v = V(40, 60, 0.105, -700, 5300)
v.text("1  POHJA – kattorakenne ja pilarit (luonnos v2)", -700, 5450, 16, anchor="start", bold=True)
v.rect(SLAB_X1, FY0, KX1, FY1, C["new"], 1.5, C["fill"])
v.rect(STRIP_X0, FY0, SLAB_X1, TERR_Y, C["dim"], 1.0, C["strip"])
v.rect(5465, 1600, SLAB_X1, FY1, C["new"], 0.8, C["fill"], dash="6 3")
v.text("laatta ±0.000", 5880, 3000, 10, C["new"])
v.poly([(2630, 0), (2630, TERR_Y), (6305, TERR_Y), (6305, 1600), (5465, 1600), (5465, 0)],
       C["exist"], 1.0, C["deck"], close=True)
v.text("terassi +0.165 (kaide pois)", 4400, -450, 10, C["exist"])
v.rect(STRIP_X0, -860, 3590, -60, C["q"], 1.0, dash="4 3")
v.text("etuportaat pois – tilalle? (A)", 3010, -400, 10, C["q"])
v.rect(5470, 1600, 6300, 2380, C["del"], 0.8, dash="4 3")
v.text("päätyportaat pois", 5885, 2450, 9, C["del"])
v.text("porraskaista ±0.000, 5 lautaa = 625", 4400, FY0 + 200, 10, C["dim"])
# rakennus
v.rect(-65, -65, 5465, 4265, C["exist"], 2.2)
v.rect(65, 65, 5335, 4135, C["exist"], 0.6)
v.line((2400, 65), (2400, 4135), C["exist"], 0.6)
v.line((2465, 1350), (5335, 1350), C["exist"], 0.6)
v.text("SAUNA", 2700, 2500, 14, C["exist"], bold=True)
v.poly([(-600, -600), (-600, 4800), (6000, 4800), (6000, 1635), (6410, 1635), (6410, -870),
        (2225, -870), (2225, -600)], C["exist"], 0.6, dash="10 4 2 4", close=True)
v.text("nyk. räystäs / kuistin katto säilyy", 6450, -1000, 9, C["exist"], anchor="start")
# keittiön katto
v.rect(RX0, EAVE_Y0, RX1, EAVE_Y1, C["roof"], 0.9, dash="10 4 2 4")
for y, lab in ((PF, "reunapalkki 115×135"), (PU1, "välipalkki 115×225"), (YC, "harjapalkki 115×225"),
               (PU2, "välipalkki 115×225"), (PR, "reunapalkki 115×135")):
    v.line((RX0, y), (KX1 + 100, y), C["roof"], 1.8, dash="8 4")
    v.text(lab, 8300, y + 80, 9, C["roof"])
for x in RAFT_X:
    v.line((x, EAVE_Y0), (x, EAVE_Y1), C["roof"], 0.5, dash="3 3")
v.text("vasat 48×98 k900", RAFT_X[1] - 450, EAVE_Y1 + 90, 9, C["roof"])
# pilarit
for x in PX:
    for y in (PF, PR):
        v.rect(x - P / 2, y - P / 2, x + P / 2, y + P / 2, C["new"], 1, C["new"])
for y in PY_END[1:-1]:
    v.rect(X_OUT - P / 2, y - P / 2, X_OUT + P / 2, y + P / 2, C["new"], 1, C["new"])
    v.rect(X_IN - P / 2, y - P / 2, X_IN + P / 2, y + P / 2, C["q"], 1.2, "white")
v.text("sisäpään välipilarit? (B)", X_IN + 120, 1500, 9, C["q"], anchor="start")
v.poly([(X_IN, PR + 75), (KX1 + 20, PR + 75), (KX1 + 20, PF)], C["new"], 3.0)
v.text("taka + pääty: alaosa umpi, yläosa avoin", 8300, FY1 + 650, 10, C["new"])
v.text("etusivu avoin", 8300, -380, 10, C["new"])
v.text("KESÄKEITTIÖ ±0.000", 8300, 2500, 13, C["new"], bold=True)
v.line((FACE_B, -1500), (FACE_B, -1300), C["new"], 0.6)
v.line((-200, FACE_B), (KX1 + 900, FACE_B), C["new"], 0.4, dash="2 4")
v.text("etuseinälinja = seinän B ulkopinta", KX1 + 950, FACE_B - 40, 9, C["new"], anchor="start")
# mitat
v.dimh(SLAB_X1, KX1, FY1, 1150, "4000")
for a, b in zip(PX, PX[1:]):
    v.dimh(a, b, FY1, 750, f"{round(b - a)}")
v.dimv(KX1, FY0, FY1, 1350, f"{round(FY1 - FY0)}")
v.dimv(KX1, PF, PR, 900, f"{round(PR - PF)} k/k")
for a, b in zip(PY_END, PY_END[1:]):
    v.dimv(KX1, a, b, 450, f"{round(b - a)}")
v.dimv(KX1, FY0, TERR_Y, 450, f"{STRIP}")
for n, x in (("G", 0), ("J", 5400)):
    v.text(n, x, -1700, 11, "#b00")

# ================================================================ LATTIARUNKO
v = V(40, 820, 0.105, -700, 4700)
v.text("2  LATTIARUNKO (kansilaudoitus 28×120 kyll. pituussuuntaan)", -700, 4850, 16, anchor="start", bold=True)
v.rect(-65, -65, 5465, 4265, C["exist"], 1.2, "#f6f6f6")
v.rect(-65, -65, SLAB_X1, 4265, C["exist"], 0.6, dash="6 3")
v.text("pohjalaatta", 3000, 2000, 12, C["exist"])
v.rect(STRIP_X0, FY0, KX1, TERR_Y, C["dim"], 0.6, C["strip"])
v.rect(SLAB_X1, TERR_Y, KX1, FY1, C["new"], 0.6, C["fill"])
for y in LONG_Y:
    v.rect(SLAB_X1, y - 48, KX1, y + 48, C["frame"], 0.8, "#f5c4b3")
for y in (FY0 + 24, TERR_Y - 24):
    v.rect(STRIP_X0, y - 24, SLAB_X1, y + 24, C["frame"], 0.8, "#f5c4b3")
for i in range(len(LONG_Y) - 1):
    for x in CROSS_X:
        v.rect(x - 24, LONG_Y[i] + 48, x + 24, LONG_Y[i + 1] - 48, C["frame"], 0.6, "#faece7")
x = STRIP_X0 + 24
while x < SLAB_X1:
    v.rect(x - 24, FY0 + 48, x + 24, TERR_Y - 48, C["frame"], 0.6, "#faece7")
    x += CROSS_CC
for fx in FOOT_X:
    for y in LONG_Y:
        v.circle(fx, y, 7, C["frame"], "white")
for fx in STRIP_FOOT_X[1:] + [SLAB_X1 - 150]:
    for y in (FY0 + 24, TERR_Y - 24):
        v.circle(fx, y, 7, C["frame"], "white")
v.text("pituuspalkit 2×48×123 (6 linjaa) – laatan päätyyn palkkikengillä/kulmateräksillä", 8300, FY1 + 250, 10, C["frame"])
v.text(f"poikkipalkit 48×123 pituuspalkkien väliin, k{CROSS_CC}, palkkikengät", 8300, FY0 - 300, 10, C["frame"])
v.text("○ = pilarianturat (3 riviä × 6 + kaistan anturat)", 8300, FY0 - 550, 10, C["frame"])
v.line((7200, 3900), (8200, 3900), C["new"], 1.2)
v.poly([(8100, 3960), (8200, 3900), (8100, 3840)], C["new"], 1.2)
v.text("lautojen suunta", 7700, 3990, 10, C["new"])
for a, b in zip([SLAB_X1] + FOOT_X[:-1], FOOT_X):
    v.dimh(a, b, FY1, 700, f"{round(b - a)}")

# ================================================================ PÄÄTYNÄKYMÄ
s = 0.085
v = V(40, 1620, s, -1700, 3500)
v.text("3  PÄÄTYNÄKYMÄ keittiön päästä rakennusta kohti", -1700, 3650, 15, anchor="start", bold=True)
v.line((-1700, -300), (5300, -300), C["exist"], 1.2)
v.poly([(-65, 0), (-65, mtop(-65) - 220), (YC, MAIN_RIDGE - 220), (4265, mtop(4265) - 220), (4265, 0)],
       C["exist"], 0.6, "#f6f6f6", close=True)
for off in (0, MAIN_T):
    v.poly([(-870, mtop(-870) - off), (YC, MAIN_RIDGE - off), (4800, mtop(4800) - off)], C["exist"], 1.0)
v.rect(TERR_Y, 0, 1600, 165, C["exist"], 0.6, C["deck"])
v.rect(FY0, -DECK - JOIST, TERR_Y, 0, C["dim"], 0.8, C["strip"])
v.rect(TERR_Y, -DECK - JOIST, FY1, 0, C["new"], 1.0, C["fill"])
for off in (0, ROOF_BUILD):
    v.poly([(EAVE_Y0, ktop(EAVE_Y0) - off), (YC, K_RIDGE - off), (EAVE_Y1, ktop(EAVE_Y1) - off)],
           C["roof"], 1.4)
for y, h in ((PF, EDGE_B), (PU1, PURL_B), (YC, RIDGE_B), (PU2, PURL_B), (PR, EDGE_B)):
    t = beam_top(y)
    v.rect(y - P / 2, t - h, y + P / 2, t, C["roof"], 1.0, "#cecbf6")
    v.rect(y - P / 2, 0, y + P / 2, t - h, C["new"], 1.0, "#9fe1cb")
v.rect(PF, 0, PR, HALF_WALL, C["new"], 0.8)
for k in range(1, 8):
    v.line((PF, k * HALF_WALL / 8), (PR, k * HALF_WALL / 8), C["new"], 0.3)
v.text("alaosa umpi ~1000", YC, HALF_WALL + 120, 10, C["new"])
v.text("terassi +0.165", 400, 230, 9, C["exist"])
v.level(-1350, 0, "±0.000", C["new"])
v.text(f"keittiökaton yläpinta harjalla +{K_RIDGE} (rako 40 nyk. katon alapintaan)", YC, MAIN_RIDGE + 90, 10, C["roof"])
v.text(f"vapaa korkeus reunapalkin alla ≈ {round(EDGE_BOT)}", PF + 120, EDGE_BOT - 180, 10, C["roof"], anchor="start")
v.dimv(EAVE_Y1, 0, K_RIDGE, 500, f"+{K_RIDGE}")
v.dimh(FY0, FY1, 0, -700, f"{FY1 - FY0}")

# ================================================================ SIVUNÄKYMÄ
s = 0.062
v = V(670, 1620, s, -700, 3500)
v.text("4  SIVUNÄKYMÄ etusivulta (SIVU 2 -suunta)", -700, 3650, 15, anchor="start", bold=True)
v.line((-700, -300), (11200, -300), C["exist"], 1.2)
v.rect(-230, 0, 5630, 2010, C["exist"], 1.0, "#f6f6f6")
v.rect(-600, 2010, 6000, 2150, C["exist"], 1.0)
v.poly([(-600, 2150), (-600, MAIN_RIDGE), (6000, MAIN_RIDGE), (6000, 2150)], C["exist"], 1.0)
v.poly([(6000, 3110), (6410, 3110), (6410, 1900), (2225, 1900)], C["exist"], 0.8)
v.rect(2630, 0, SLAB_X1, 165, C["exist"], 0.8, C["deck"])
v.rect(STRIP_X0, -DECK - JOIST, KX1, 0, C["dim"], 0.8, C["strip"])
eave = ktop(EAVE_Y0)
v.poly([(6410, eave), (RX1, eave), (RX1, K_RIDGE), (6410, K_RIDGE)], C["roof"], 1.4)
v.line((6410, eave + 0), (6410, K_RIDGE), C["roof"], 0.6, dash="4 3")
v.rect(RX0, EDGE_BOT, KX1 + 100, beam_top(PF), C["roof"], 1.0, "#cecbf6")
for x in PX:
    v.rect(x - P / 2, 0, x + P / 2, EDGE_BOT, C["new"], 1.0, "#9fe1cb")
v.rect(PX[0] + P / 2, 0, PX[-1] - P / 2, HALF_WALL, C["new"], 0.6, dash="5 3")
v.text("takaseinän umpiosa taustalla", 8300, HALF_WALL + 120, 9, C["new"])
v.text("kuistin katto säilyy", 6450, 3250, 9, C["exist"], anchor="start")
v.text("SAUNA", 2700, 1000, 14, C["exist"], bold=True)
v.dimh(SLAB_X1, KX1, 0, -650, "4000")
v.text(f"räystäs +{round(eave)}", RX1 + 80, eave - 40, 9, C["roof"], anchor="start")

# ================================================================ selite
lx, ly = 1360, 900
for col, fill, lab in ((C["new"], C["fill"], "uusi kesäkeittiö"), (C["dim"], C["strip"], "porraskaista ±0.000"),
                       (C["exist"], C["deck"], "nykyinen, säilyy"), (C["del"], "none", "puretaan"),
                       (C["roof"], "#cecbf6", "kattorakenne"), (C["frame"], "#f5c4b3", "lattiarunko"),
                       (C["q"], "white", "avoin kysymys")):
    svg.append(f'<rect x="{lx}" y="{ly - 11}" width="22" height="13" fill="{fill}" stroke="{col}"/>')
    svg.append(f'<text x="{lx + 30}" y="{ly}" font-size="12" fill="#222">{lab}</text>')
    ly += 22
svg.append("</svg>")
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))
print("saved", OUT)
print("edge beam bottom", round(EDGE_BOT), "purlin bottom", round(PURL_BOT), "ridge bottom", round(RIDGE_BOT),
      "eave top", round(eave), "posts x", [round(x) for x in PX], "posts y", [round(y) for y in PY_END],
      "long y", [round(y) for y in LONG_Y], "rafters", len(RAFT_X), "floor w", FY1 - FY0)
