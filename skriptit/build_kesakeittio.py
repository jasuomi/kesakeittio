"""Kesäkeittiö saunan päätyyn (linja J) - suunnitelmapiirros 1:50, A3-arkit, 1:1 DXF millimetreinä.

Vaihtoehdot (python build_kesakeittio.py --ve 1|2A|2B|all, oletus all):
  VE1  lasitettu etusivu pilarilinjassa, liukuovi etusivulla
  VE2A lasiseinä välipalkin linjassa (y 1046), edessä avoin katos, terassi katkaistu lasiseinän kohdalta
  VE2B kuten VE2A, mutta terassi säilyy entisellään (sisäpuolelle korotettu taso)

Koordinaatit kuten build_nykytila_pohja.py (origo G/B, x rakennuksen pituussuunta, y poikittain B=0 .. E=4200)
ja korot kuten build_elev_dxf.py (0.000 = pohjalaatan yläpinta). Olemassa oleva rakennus on
piirretty yksinkertaistettuna taustaksi; tarkat julkisivut: nykytila/sauna_nykytila_julkisivut_1-50.dxf.

Näkymät: 1 kattorakenne ja pilarit, 2 lattiarunko ja perustukset, 3 päätyjulkisivu,
4 julkisivu etusivulta, 5 julkisivu takasivulta.

Output: kesakeittio_VE*/kesakeittio_VE*_arkki1..3_*.dxf (A3, mallitila = arkki 1:50)
  arkki 1: kattorakenne ja pilarit + rakennetyypit
  arkki 2: lattiarunko ja perustukset + päätyjulkisivu
  arkki 3: julkisivut etu- ja takasivulta
"""
import math
import os
import subprocess
import sys

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                  # sauna_cad
ARGS = sys.argv[1:]
VE = ARGS[ARGS.index("--ve") + 1].upper() if "--ve" in ARGS else "ALL"
if VE == "ALL":                                               # aja jokainen vaihtoehto omana prosessinaan
    for ve in ("1", "2A", "2B"):
        subprocess.run([sys.executable, os.path.abspath(__file__), "--ve", ve], check=True)
    sys.exit(0)
assert VE in ("1", "2A", "2B"), "--ve 1 | 2A | 2B | all"
VE2 = VE.startswith("2")
TER_CUT = VE == "2A"
VE_DESC = {"1": "lasitettu etusivu, liukuovi etusivulla",
           "2A": "lasiseinä välipalkin linjassa, terassi katkaistu",
           "2B": "lasiseinä välipalkin linjassa, terassi säilyy"}[VE]
OUT_DIR = os.path.join(ROOT, "kesakeittio_VE1" if VE == "1" else "kesakeittio_VE2")
os.makedirs(OUT_DIR, exist_ok=True)
SHEET_NAMES = {1: "kattorakenne", 2: "lattiarunko_paaty", 3: "julkisivut"}
OUT = os.path.join(OUT_DIR, "kesakeittio_VE" + VE + "_arkki{}_{}_1-50.dxf")
N_SHEETS = 3
SCALE = 50
TH, TH_T, TH_SHEET = 2.5 * SCALE, 3.5 * SCALE, 5 * SCALE
PAGE_W, PAGE_H = 420 * SCALE, 297 * SCALE          # A3

# ================================================================ mitoitus (mm)
# olemassa oleva
SLAB_X1 = 6302                  # terassilaatan pääty
TSLAB_Y1 = 1600                 # terassilaatan takareuna; sen takana laatta päättyy seinälinjaan J
WALL_J = 5465                   # päätyseinän J ulkopinta
LOG_END = 5630                  # hirsien nurkkaulokkeet
FACE_B, FACE_E = -65, 4265      # pitkien seinien ulkopinnat
TERR_Y = -735                   # terassin etureuna
MAIN_RIDGE, MAIN_T = 3300, 130
TAN = math.tan(math.radians(22.5))
COS = math.cos(math.radians(22.5))
YC = 2100                       # harjalinja (sama kuin nykyinen)
GROUND = -300

# kesäkeittiö
KX1 = 5465 + 4000               # 9465: 4 m päätyseinän J ulkopinnasta (laatan pääty seinälinjassa)
BOARD, GAP, DECK = 120, 5, 28   # kansilauta 28x120 kyll., rako 5
STRIP = 5 * (BOARD + GAP)       # porraskaista 625
FY0, FY1 = TERR_Y - STRIP, FACE_E
STRIP_X0 = 2430
JOIST = 123
FLOOR_BOT = -DECK - JOIST       # -151
P = 115                         # liimapuupilari 115x115
PF, PR = FACE_B + P / 2, FACE_E - P / 2
PU1, PU2 = (PF + YC) / 2, (PR + YC) / 2
PY_END = [PF, PU1, YC, PU2, PR]
X_IN, X_OUT = SLAB_X1 + P / 2, KX1 - P / 2
PX = [X_IN + i * (X_OUT - X_IN) / 3 for i in range(4)]
PXR = PX                                                       # takareunan pilarit (4 kpl)
PXF = PX if not VE2 else [X_IN, (X_IN + X_OUT) / 2, X_OUT]     # etureuna: VE2 3 kpl, jako 1524
GLASS_F = 45                    # lasituksen karmi/puite (näkyvä leveys)
DOOR_BAY = 0                    # liukuovi etusivun 1. välissä (terassin puolella)
DOOR_OFF = 70                   # ovilehti ulkopuolisella kiskolla, etäisyys lasilinjasta
GAP_X0 = LOG_END + 50           # kiinteä lasi rakennuksen nurkan ja 1. pilarin välissä

GAP_ROOF = 40
K_RIDGE = MAIN_RIDGE - MAIN_T - GAP_ROOF              # 3130 keittiökaton yläpinta harjalla
RAFTER_H, BATTEN, SHEET = 98, 25, 25                   # vasa 48x98, rima 25x50, valokate ~25
ROOF_BUILD = BATTEN + SHEET + RAFTER_H / COS           # pystymitta katon pinnasta vasan alapintaan
NOTCH = 30
EDGE_B, PURL_B, RIDGE_B = 123, 198, 198     # sahatavara C24
EAVE_Y0, EAVE_Y1 = -600, 4800
RX0, RX1 = 5650, KX1 + 500      # katon alku hirsien päiden jälkeen .. päätyräystäs
BEAM_X0 = WALL_J                # harja- ja välipalkit alkavat hirsipäädystä (teräskannake)
EDGE_X0 = 5700                  # reunapalkit alkavat nurkkaulokkeiden jälkeen


def ktop(y):
    return K_RIDGE - abs(y - YC) * TAN


def mtop(y):
    return MAIN_RIDGE - abs(y - YC) * TAN


def beam_top(y):
    return ktop(y) - ROOF_BUILD + NOTCH


EDGE_W, PURL_W = 48, 96         # reunapalkki 48x123, väli- ja harjapalkki 2x48x198 (pilarien keskilinjalla)
BW_OF = {EDGE_B: EDGE_W, PURL_B: PURL_W}
BEAMS = [(PF, EDGE_B, "reunapalkki 48x123"), (PU1, PURL_B, "välipalkki 2x48x198"),
         (YC, RIDGE_B, "harjapalkki 2x48x198"), (PU2, PURL_B, "välipalkki 2x48x198"),
         (PR, EDGE_B, "reunapalkki 48x123")]
EDGE_BOT = beam_top(PF) - EDGE_B
PURL_BOT = beam_top(PU1) - PURL_B                              # välipalkin alapinta = VE2 lasiseinän yläreuna

# VE2 lasiseinä välipalkin linjassa: aloitustolppa J-päätyä vasten, 3 moduulia, ovi keskellä
GW_Y = PU1
MUL = 90                                                       # karmitolppa liimapuu 90x90
GW_X0, GW_X1 = WALL_J + MUL, X_OUT - P / 2                     # aloitustolpan jälkeen .. päätypilarin pintaan
GW_MOD = (GW_X1 - GW_X0 - 2 * MUL) / 3
GW_MODS = [(GW_X0 + i * (GW_MOD + MUL), GW_X0 + i * (GW_MOD + MUL) + GW_MOD) for i in range(3)]
GW_DOOR = 1                                                    # keskimmäinen moduuli
GW_DOOR_TOP = PURL_BOT - 60                                    # yläkisko välipalkin alapinnassa

# jäykistys
BR_X0, BR_X1 = RX0 + 24, X_OUT              # tuulisiteet ensimmäisestä vasasta päätypilareihin
BR_XM = (BR_X0 + BR_X1) / 2
BLOCK_Y = (1350, 2850)                      # 1. vasan välikappaleet hirsien päihin
ROD_BAYS = ((0, 1), (3, 4))                 # päädyn uloimmat pilarivälit (PY_END-indeksit)

RAFT_X = []
x = RX1 - 24
while x > RX0 + 300:
    RAFT_X.append(x)
    x -= 900
RAFT_X.append(RX0 + 24)

# lattiarunko
LONG_Y = [FY0 + 48 + i * (FY1 - FY0 - 96) / 5 for i in range(6)]   # pituuspalkit 2x48x123
if VE2:                                                        # yksi pituuspalkki lasiseinän alle
    _a, _r = FY0 + 48, FY1 - 48
    LONG_Y = [_a, (_a + GW_Y) / 2, GW_Y, GW_Y + (_r - GW_Y) / 3, GW_Y + 2 * (_r - GW_Y) / 3, _r]
STRIP_REAR = TERR_Y - 48
CROSS_CC = 500
FOOT_X = PX[1:]
STRIP_FOOT_X = [STRIP_X0 + 120 + i * (X_IN - STRIP_X0 - 120) / 3 for i in range(4)]

# ================================================================ dokumentti (yksi per arkki)
LAYERS = {   # nimi: (väri, viivatyyppi, viivanpaksuus 1/100 mm)
    "K-EXIST": (8, None, 18), "K-DEMO": (1, "DASHED", 25), "K-FLOOR": (3, None, 35),
    "K-DECK": (3, None, 13), "K-FRAME": (30, None, 25), "K-FOOT": (8, "DASHED", 18),
    "K-POST": (4, None, 35), "K-BEAM": (5, None, 35), "K-RAFTER": (5, None, 18),
    "K-ROOF": (5, None, 35), "K-WALL": (4, None, 25), "K-STEEL": (6, None, 25),
    "K-HIDDEN": (9, "HIDDEN", 18), "K-EAVE": (9, "DASHDOT", 18), "K-DIM": (2, None, 18),
    "K-TEXT": (7, None, 25), "K-LEVEL": (2, None, 18), "K-FRAME-SHEET": (7, None, 50),
    "K-GLASS": (140, None, 25), "K-BRACE": (1, None, 35),
}
doc = msp = None


def start_sheet():
    global doc, msp
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4
    doc.header["$MEASUREMENT"] = 1
    doc.header["$LTSCALE"] = 10
    doc.header["$LWDISPLAY"] = 1
    msp = doc.modelspace()
    for name, (color, lt, lw) in LAYERS.items():
        lay = doc.layers.add(name, color=color)
        lay.dxf.lineweight = lw
        if lt:
            lay.dxf.linetype = lt


def finish_sheet(no, content):
    """kehys, nimiö ja A3-tulostusasetukset; mallitila = A3-arkki 1:50"""
    msp.add_lwpolyline([(375, 375), (PAGE_W - 375, 375), (PAGE_W - 375, PAGE_H - 375), (375, PAGE_H - 375)],
                       close=True, dxfattribs={"layer": "K-FRAME-SHEET"})
    tb = (PAGE_W - 375 - 7500, 375, PAGE_W - 375, 375 + 2500)
    msp.add_lwpolyline([(tb[0], tb[1]), (tb[2], tb[1]), (tb[2], tb[3]), (tb[0], tb[3])], close=True,
                       dxfattribs={"layer": "K-FRAME-SHEET"})
    msp.add_line((tb[2] - 1500, tb[1]), (tb[2] - 1500, tb[1] + 1000), dxfattribs={"layer": "K-FRAME-SHEET"})
    msp.add_line((tb[0], tb[1] + 1000), (tb[2], tb[1] + 1000), dxfattribs={"layer": "K-FRAME-SHEET"})
    for t, x, y, h in ((f"KESÄKEITTIÖ VE{VE} - SAUNAN PÄÄTY", tb[0] + 200, tb[3] - 450, TH_SHEET * 0.8),
                       (content, tb[0] + 200, tb[3] - 900, TH_T),
                       (f"VE{VE}: {VE_DESC}", tb[0] + 200, tb[1] + 600, TH),
                       ("Luonnos 14.11.2026, 1:50 (A3). Liittyy: nykytila/sauna_nykytila_*", tb[0] + 200,
                        tb[1] + 200, TH * 0.85),
                       ("ARKKI", tb[2] - 1350, tb[1] + 650, TH), (f"{no}/{N_SHEETS}", tb[2] - 1350, tb[1] + 150,
                                                                  TH_SHEET)):
        msp.add_text(t, height=h, dxfattribs={"layer": "K-TEXT", "style": "OpenSans"}
                     ).set_placement((x, y), align=TA.BOTTOM_LEFT)
    doc.header["$PLIMMIN"] = (0, 0)
    doc.header["$PLIMMAX"] = (420, 297)
    doc.header["$PSVPSCALE"] = 1 / SCALE
    lay = doc.layouts.new("A3 1-50")
    lay.page_setup(size=(420, 297), margins=(0, 0, 0, 0), units="mm")
    lay.add_viewport(center=(210, 148.5), size=(420, 297), view_center_point=(PAGE_W / 2, PAGE_H / 2),
                     view_height=297 * SCALE)
    doc.set_modelspace_vport(height=PAGE_H * 1.05, center=(PAGE_W / 2, PAGE_H / 2))
    doc.audit()
    path = OUT.format(no, SHEET_NAMES[no])
    doc.saveas(path)
    print("saved", path)


class View:
    """Paikallinen (u, v) mm -> mallitila. sign = -1 peilaa u-akselin (takajulkisivu)."""

    def __init__(self, ox, oy, sign=1):
        self.ox, self.oy, self.sign = ox, oy, sign

    def M(self, u, v):
        return (self.ox + self.sign * u, self.oy + v)

    def line(self, p, q, layer):
        msp.add_line(self.M(*p), self.M(*q), dxfattribs={"layer": layer})

    def pl(self, pts, layer, closed=False):
        msp.add_lwpolyline([self.M(*p) for p in pts], close=closed, dxfattribs={"layer": layer})

    def rect(self, u0, v0, u1, v1, layer):
        self.pl([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], layer, closed=True)

    def solid(self, u0, v0, u1, v1, layer):
        self.rect(u0, v0, u1, v1, layer)
        h = msp.add_hatch(color=256, dxfattribs={"layer": layer})
        h.paths.add_polyline_path([self.M(u0, v0), self.M(u1, v0), self.M(u1, v1), self.M(u0, v1)],
                                  is_closed=True)

    def hatch(self, pts, layer, pattern="ANSI31", scale=0.6):
        h = msp.add_hatch(color=256, dxfattribs={"layer": layer})
        h.set_pattern_fill(pattern, scale=SCALE * scale)
        h.paths.add_polyline_path([self.M(*p) for p in pts], is_closed=True)

    def circle(self, u, v, r, layer):
        msp.add_circle(self.M(u, v), r, dxfattribs={"layer": layer})

    def text(self, s, u, v, h=TH, layer="K-TEXT", rot=0, align=TA.BOTTOM_LEFT):
        if self.sign < 0 and align == TA.BOTTOM_LEFT:
            align = TA.BOTTOM_RIGHT
        elif self.sign < 0 and align == TA.BOTTOM_RIGHT:
            align = TA.BOTTOM_LEFT
        msp.add_text(s, height=h, rotation=rot, dxfattribs={"layer": layer, "style": "OpenSans"}
                     ).set_placement(self.M(u, v), align=align)

    def dim_h(self, u0, u1, v, vb, label=None):
        a, b = sorted((u0, u1))
        s = 1 if vb > v else -1
        for u in (a, b):
            self.line((u, v + s * 75), (u, vb + s * 75), "K-DIM")
            self.line((u - 60, vb - 60), (u + 60, vb + 60), "K-DIM")
        self.line((a - 75, vb), (b + 75, vb), "K-DIM")
        self.text(label or f"{round(b - a)}", (a + b) / 2, vb + 40, layer="K-DIM", align=TA.BOTTOM_CENTER)

    def dim_v(self, u, v0, v1, ub, label=None):
        a, b = sorted((v0, v1))
        s = 1 if ub > u else -1
        for v in (a, b):
            self.line((u + s * 75, v), (ub + s * 75, v), "K-DIM")
            self.line((ub - 60, v - 60), (ub + 60, v + 60), "K-DIM")
        self.line((ub, a - 75), (ub, b + 75), "K-DIM")
        self.text(label or f"{round(b - a)}", ub - 40 * self.sign, (a + b) / 2, layer="K-DIM",
                  rot=90, align=TA.BOTTOM_CENTER)

    def chain_h(self, us, v, vb, labels=None):
        for i, (a, b) in enumerate(zip(us, us[1:])):
            self.dim_h(a, b, v, vb, labels[i] if labels else None)

    def chain_v(self, u, vs, ub):
        for a, b in zip(vs, vs[1:]):
            self.dim_v(u, a, b, ub)

    def level(self, u, z, label, length=500):
        self.line((u, z), (u + length, z), "K-LEVEL")
        tip = u + length * 0.3
        self.pl([(tip, z), (tip - 50, z + 110), (tip + 50, z + 110)], "K-LEVEL", closed=True)
        self.text(label, u, z + 150, layer="K-LEVEL")


def title(s, x, y, sub=None):
    msp.add_text(s, height=TH_T, dxfattribs={"layer": "K-TEXT", "style": "OpenSans"}
                 ).set_placement((x, y), align=TA.BOTTOM_LEFT)
    msp.add_line((x, y - 60), (x + len(s) * TH_T * 0.62, y - 60), dxfattribs={"layer": "K-TEXT"})
    if sub:
        msp.add_text(sub, height=TH, dxfattribs={"layer": "K-TEXT", "style": "OpenSans"}
                     ).set_placement((x, y - 260), align=TA.BOTTOM_LEFT)


# ---------------------------------------------------------------- yhteiset pohjaelementit
def existing_plan(v, roof=True):
    """olemassa oleva rakennus, terassi ja räystäät (yksinkertaistettu)"""
    v.rect(-65, -65, 5465, 4265, "K-EXIST")
    v.rect(65, 65, 5335, 4135, "K-EXIST")
    for x in (-230, 5630):                                    # hirsien nurkkaulokkeet
        for y in (0, 4200):
            v.rect(min(x, x + (65 if x < 0 else -65)), y - 65, max(x, x + (65 if x < 0 else -65)), y + 65,
                   "K-EXIST")
    v.text("SAUNA (olemassa oleva)", 2700, 2050, h=TH_T, align=TA.MIDDLE_CENTER)
    if TER_CUT:                                                # VE2A: terassi katkaistu lasiseinän kohdalta
        v.pl([(2630, 0), (2630, TERR_Y), (6305, TERR_Y), (6305, GW_Y - 45), (5465, GW_Y - 45)], "K-EXIST")
        v.pl([(5465, GW_Y + 45), (6305, GW_Y + 45), (6305, 1600), (5465, 1600)], "K-DEMO")
    else:
        v.pl([(2630, 0), (2630, TERR_Y), (6305, TERR_Y), (6305, 1600), (5465, 1600)], "K-EXIST")
    v.text("terassi +0.165 (säilyy, kaide pois)", 4800, -500, align=TA.MIDDLE_CENTER)
    if roof:
        v.pl([(-600, -600), (-600, 4800), (6000, 4800), (6000, 1635), (6410, 1635), (6410, -870),
              (2225, -870), (2225, -600)], "K-EAVE", closed=True)
        v.text("nykyinen räystäs ja kuistin katto (säilyvät)", 6480, -1050, layer="K-EXIST")


def new_floor_outline(v):
    v.pl([(SLAB_X1, FY0), (KX1, FY0), (KX1, FY1), (WALL_J, FY1), (WALL_J, TSLAB_Y1), (SLAB_X1, TSLAB_Y1)],
         "K-FLOOR", closed=True)
    v.pl([(STRIP_X0, TERR_Y), (STRIP_X0, FY0), (SLAB_X1, FY0)], "K-FLOOR")
    v.line((STRIP_X0, TERR_Y), (2630, TERR_Y), "K-FLOOR")
    v.rect(STRIP_X0, TERR_Y, 3590, -60, "K-FLOOR")             # terassin jatke puretun portaan tilalle


def glass_plan_x(v, x, a, b):
    """lasitus pohjassa (seinä x-vakio): karmin rajat + lasi"""
    for d in (-30, 30):
        v.line((x + d, a), (x + d, b), "K-GLASS")
    v.line((x, a), (x, b), "K-GLASS")


def glass_plan_y(v, y, a, b):
    for d in (-30, 30):
        v.line((a, y + d), (b, y + d), "K-GLASS")
    v.line((a, y), (b, y), "K-GLASS")


def walls_plan(v):
    """takaseinä umpi koko korkeudelta; VE1 pääty ja etusivu lasitettu, VE2 lasiseinä välipalkin linjassa"""
    v.rect(LOG_END, FY1 - 25, KX1, FY1, "K-WALL")
    v.hatch([(LOG_END, FY1 - 25), (KX1, FY1 - 25), (KX1, FY1), (LOG_END, FY1)], "K-WALL", "SOLID")
    v.rect(LOG_END, PR - P / 2, LOG_END + 48, PR + P / 2 - 25, "K-WALL")   # aloitustolppa 48x98
    for i, (a, b) in enumerate(zip(PY_END, PY_END[1:])):
        if not (VE2 and i == 0):
            glass_plan_x(v, X_OUT, a + P / 2, b - P / 2)
    if VE2:
        glasswall_plan(v)
        return
    for i, (a, b) in enumerate(zip(PX, PX[1:])):
        if i != DOOR_BAY:
            glass_plan_y(v, PF, a + P / 2, b - P / 2)
    glass_plan_y(v, PF, GAP_X0, X_IN - P / 2)
    v.rect(LOG_END, PF - P / 2, GAP_X0, PF + P / 2, "K-WALL")              # aloitustolppa nurkkaa vasten
    # liukuovi: suljettu asento (ehjä) ja avattu asento (katkoviiva) viereisen lasin edessä
    a, b = PX[DOOR_BAY] + P / 2 - 30, PX[DOOR_BAY + 1] - P / 2 + 30
    yo = PF - P / 2 - DOOR_OFF
    v.rect(a, yo - 25, b, yo + 25, "K-GLASS")
    w = b - a
    v.rect(a + w + P, yo - 25, b + w + P, yo + 25, "K-HIDDEN")
    v.line((a + 0.25 * w, yo - 180), (a + 0.95 * w, yo - 180), "K-GLASS")
    v.pl([(a + 0.95 * w - 90, yo - 135), (a + 0.95 * w, yo - 180), (a + 0.95 * w - 90, yo - 225)], "K-GLASS")


def glasswall_plan(v):
    """VE2: kantamaton lasiseinä välipalkin alla, karmitolpat 90x90, liukuovi keskimoduulissa"""
    v.rect(WALL_J, GW_Y - MUL / 2, WALL_J + MUL, GW_Y + MUL / 2, "K-GLASS")    # aloitustolppa J-päätyä vasten
    for i, (a, b) in enumerate(GW_MODS):
        if i < 2:
            v.rect(b, GW_Y - MUL / 2, b + MUL, GW_Y + MUL / 2, "K-GLASS")       # karmitolpat
        if i != GW_DOOR:
            glass_plan_y(v, GW_Y, a, b)
    a, b = GW_MODS[GW_DOOR]
    a, b = a - 30, b + 30
    yo = GW_Y - MUL / 2 - DOOR_OFF
    v.rect(a, yo - 25, b, yo + 25, "K-GLASS")
    w = b - a
    v.rect(a + w + MUL - 60, yo - 25, b + w + MUL - 60, yo + 25, "K-HIDDEN")
    v.line((a + 0.25 * w, yo - 180), (a + 0.95 * w, yo - 180), "K-GLASS")
    v.pl([(a + 0.95 * w - 90, yo - 135), (a + 0.95 * w, yo - 180), (a + 0.95 * w - 90, yo - 225)], "K-GLASS")


def posts_plan(v):
    for xs_, y in ((PXF, PF), (PXR, PR)):
        for x in xs_:
            v.solid(x - P / 2, y - P / 2, x + P / 2, y + P / 2, "K-POST")
    for y in PY_END[1:-1]:
        v.solid(X_OUT - P / 2, y - P / 2, X_OUT + P / 2, y + P / 2, "K-POST")


# ================================================================ selitykset
NOTES_PURKU = """#PURETAAN
- Terassin kaide
- Etuportaat (tilalle terassin jatke +0.165 ja porraskaista)
- Päätyportaat"""
if TER_CUT:
    NOTES_PURKU += "\n- Terassin runko ja kansi lasiseinän sisäpuolelta (betonilaatta jää)"
NOTES_LATTIA = """#LATTIA ±0.000 (= pohjalaatan yläpinta)
- Kansilauta 28x120 kyll., rako 5, pituussuuntaan
- Pituuspalkit 2x48x123 kyll., poikkipalkit 48x123 k500 väliin
- Porraskaista terassin edessä 5 lautaa = 625, koko pituudelta
- Runko alkaa laatan reunasta: terassin kohdalla laatan päädystä,
  terassin ja takaseinän välillä seinälinjasta J
- Pilarianturat, routasuojaus - tarkennetaan"""
if VE2:
    NOTES_LATTIA += "\n- Pituuspalkki lasiseinän alle (y 1046)"
if TER_CUT:
    NOTES_LATTIA += ("\n- Katkaistun terassin kohdalla kansilaudoitus suoraan betonilaatan päälle"
                     "\n  (yläpinta n. +0.028, liitos keittiön lattiaan viisteellä)")
if VE == "2B":
    NOTES_LATTIA += "\n- Terassi säilyy: lasiseinän sisäpuolelle korotettu taso +0.165, n. 840 x 510"
if not VE2:
    NOTES_SEINAT = """#SEINÄT
- Pilarit liimapuu 115x115, omat anturat
- Takaseinä umpi koko korkeudelta, rakennuksen seinään asti,
  aloitustolppa 48x98 hirsien nurkkaulokkeita vasten
- Päätyseinä ja etusivu: lasitus koko korkeudelle pilarien väliin
  (karmit pilareihin, turvalasi, tyyppi tarkennetaan)
- Päädyn lasitus ulottuu vasojen alapintaan (päätykolmio lasia)
- Etusivu linjassa rakennuksen etuseinän kanssa
- Liukuovi etusivun 1. pilariväliin, ovilehti ulkopuolisella kiskolla
  (yläkisko reunapalkkiin), aukko n. 900 x 1900, avautuu
  viereisen kiinteän lasin eteen
- Rakennuksen nurkan ja 1. pilarin väliin kiinteä lasi terassin päälle"""
else:
    NOTES_SEINAT = f"""#SEINÄT
- Pilarit liimapuu 115x115, omat anturat: etureunassa 3 (jako 1524),
  takareunassa 4 (jako 1016)
- Takaseinä umpi koko korkeudelta, rakennuksen seinään asti,
  aloitustolppa 48x98 hirsien nurkkaulokkeita vasten
- Lasiseinä välipalkin linjassa (y 1046) J-päädystä päätyyn,
  välipalkki ylähirtenä, kantamaton karmirunko 90x90 liimapuu,
  3 moduulia, turvalasi, aloitustolppa J-päädyn hirsiä vasten
- Liukuovi keskimmäisessä moduulissa, ovilehti ulkopuolisella kiskolla,
  aukko n. {round(GW_MOD)} x {round(GW_DOOR_TOP - 10)}, avautuu viereisen lasin eteen
- Päätyseinä lasitettu välipalkista takanurkkaan, etummainen väli avoin
- Lasiseinän edessä avoin katos (terassi ja porraskaista)"""
NOTES = NOTES_PURKU + "\n" + NOTES_LATTIA + "\n" + NOTES_SEINAT + """
#KATTO 22,5° (harja nykyisen harjan linjassa)
- Valokate
- Ruoteet 25x50 rima tai 22x100 lauta (jako valmistajan mukaan)
- Vasat 48x98 mitallistettu k900
- Reunapalkit sahatavara C24 48x123 (jänne 1016/1524)
- Väli- ja harjapalkit 2x48x198 C24 naulattuna pariksi (jänne 3,94 m), kiinnitys hirsipäätyyn
  teräskannakkeilla (läpipultit), rakennus v. 1990 - ei painumavaraa
- Keittiökatto 40 mm nykyisen katon alapinnan alapuolella
#JÄYKISTYS
- Kattotason tuulisiteet X molempiin lappeisiin, teräsvanne 40x2,
  vasojen päällä ruoteiden alla, ankkurinaulaus jokaiseen vasaan
- Harja- ja välipalkkien kannakkeet hirsipäätyyn mitoitetaan myös
  veto-, puristus- ja sivuttaisvoimalle (läpipultit)
- 1. vasa välikappaleilla hirsien päihin (y 1350 ja 2850),
  takareunapalkki teräslevyllä E/J-hirsinurkkaan
- Takaseinä: rankarunko 48x98 k600 + havuvaneri 12 mm verhouksen alla
- Päädyn uloimmat välit: vetotangot ø12 ristiin kiristimin,
  pilarien sisäpinnassa (lasitus ulkopuolelle)
- Nostoankkurointi: kattotuoliankkurit, palkkien yläpään kengät,
  nostoa kestävät pilarikengät, anturoiden paino tarkistetaan
- Väliaikainen vinotuenta, kunnes jäykistys on valmis
#HUOM
- Luonnosmitoitus, tarkistetaan rakennesuunnittelussa
  (lumikuorma, liitokset, perustukset)"""


def notes(nx, ny):
    for s in NOTES.split("\n"):
        if s.startswith("#"):
            ny -= 120
            msp.add_text(s[1:], height=TH, dxfattribs={"layer": "K-TEXT", "style": "OpenSans"}
                         ).set_placement((nx, ny), align=TA.BOTTOM_LEFT)
            msp.add_line((nx, ny - 40), (nx + 6300, ny - 40), dxfattribs={"layer": "K-TEXT"})
            ny -= 80
        else:
            msp.add_text(s, height=TH * 0.78, dxfattribs={"layer": "K-TEXT", "style": "OpenSans"}
                         ).set_placement((nx, ny), align=TA.BOTTOM_LEFT)
        ny -= 172
    return ny



# ================================================================ ARKKI 1
start_sheet()
# ================================================================ 1 KATTORAKENNE JA PILARIT
v1 = View(1700, 7700)
existing_plan(v1)
new_floor_outline(v1)
v1.pl([(5470, 1600), (6300, 1600), (6300, 2380), (5470, 2380)], "K-DEMO", closed=True)
v1.line((5470, 1600), (6300, 2380), "K-DEMO"); v1.line((5470, 2380), (6300, 1600), "K-DEMO")
v1.text("päätyportaat puretaan", 5885, 2480, layer="K-DEMO", align=TA.BOTTOM_CENTER)
v1.text("etuportaan tilalle terassin jatke +0.165", 2450, -40 - 2 * TH, h=TH * 0.8)
# katon ulkoraja
v1.pl([(RX0, EAVE_Y0), (RX1, EAVE_Y0), (RX1, EAVE_Y1), (RX0, EAVE_Y1)], "K-ROOF")
# vasat (yksiviiva) ja palkit (kaksoisviiva)
for x in RAFT_X:
    v1.line((x, EAVE_Y0), (x, EAVE_Y1), "K-RAFTER")
for y, h, lab in BEAMS:
    x0 = EDGE_X0 if h == EDGE_B else BEAM_X0
    bw = BW_OF[h]
    v1.rect(x0, y - bw / 2, RX1 - 48, y + bw / 2, "K-BEAM")
    if bw == PURL_W:
        v1.line((x0, y), (RX1 - 48, y), "K-BEAM")
    v1.text(lab, 7900, y + P / 2 + 30, layer="K-BEAM", align=TA.BOTTOM_CENTER)
    if h != EDGE_B:                                          # teräskannake hirsipäätyyn
        v1.rect(WALL_J, y - bw / 2 - 20, WALL_J + 80, y + bw / 2 + 20, "K-STEEL")
walls_plan(v1)
posts_plan(v1)
# jäykistys: tuulisiteet, välikappaleet, nurkkalevy, päädyn vetotangot
for ya, yb in ((PF, YC), (YC, PR)):
    for xa, xb in ((BR_X0, BR_XM), (BR_XM, BR_X1)):
        v1.line((xa, ya), (xb, yb), "K-BRACE")
        v1.line((xa, yb), (xb, ya), "K-BRACE")
for y in BLOCK_Y:
    v1.rect(LOG_END, y - 50, BR_X0 - 24, y + 50, "K-STEEL")
v1.rect(LOG_END - 70, PR - 70, EDGE_X0 + 60, PR + 70, "K-STEEL")
for i, j in ROD_BAYS:
    v1.line((X_OUT - P / 2 - 15, PY_END[i] + P / 2), (X_OUT - P / 2 - 15, PY_END[j] - P / 2), "K-BRACE")
v1.text("tuulisiteet X 40x2", BR_XM, 2600, h=TH * 0.85, layer="K-BRACE", align=TA.BOTTOM_CENTER)
v1.text("vasat 48x98 k900, valokate", WALL_J + 250, 3650, layer="K-RAFTER")
v1.text("harja- ja välipalkit hirsipäätyyn teräskannakkeilla", 5350, 3350, h=TH * 0.8,
        layer="K-STEEL", align=TA.BOTTOM_RIGHT)
v1.text("KESÄKEITTIÖ ±0.000", 8300, 1500, h=TH_T, layer="K-FLOOR", align=TA.MIDDLE_CENTER)
if not VE2:
    v1.text("lasitus", (PX[1] + PX[3]) / 2, -380, layer="K-GLASS", align=TA.MIDDLE_CENTER)
    v1.text("liukuovi", (PX[0] + PX[1]) / 2, -470, h=TH * 0.8, layer="K-GLASS", align=TA.MIDDLE_CENTER)
else:
    v1.text("lasiseinä välipalkin alla", (GW_MODS[0][0] + GW_MODS[0][1]) / 2, GW_Y + 120, h=TH * 0.8,
            layer="K-GLASS", align=TA.BOTTOM_CENTER)
    v1.text("liukuovi", (GW_MODS[1][0] + GW_MODS[1][1]) / 2, GW_Y - 420, h=TH * 0.8, layer="K-GLASS",
            align=TA.MIDDLE_CENTER)
    v1.text("AVOIN KATOS", 8300, 420, h=TH, layer="K-FLOOR", align=TA.MIDDLE_CENTER)
    if TER_CUT:
        v1.text("terassi katkaistu, kansi betonin päälle", (WALL_J + SLAB_X1) / 2, 1330, h=TH * 0.6,
                layer="K-DEMO", align=TA.MIDDLE_CENTER)
    else:
        v1.text("terassi +0.165 säilyy", (WALL_J + SLAB_X1) / 2, 1330, h=TH * 0.6, layer="K-EXIST",
                align=TA.MIDDLE_CENTER)
v1.text("takaseinä umpi koko korkeudelta, pääty lasitettu", 8300, PR - 450, layer="K-WALL",
        align=TA.BOTTOM_CENTER)
v1.text("porraskaista ±0.000, 5 x 28x120", 4300, FY0 + 220, layer="K-FLOOR", align=TA.MIDDLE_CENTER)
# mitat
v1.chain_h([WALL_J, KX1], FY1, FY1 + 1150, ["4000"])
v1.chain_h([X_IN] + PXR[1:], FY1, FY1 + 750)
if VE2:
    v1.chain_h(PXF, FY0, FY0 - 450)
v1.dim_h(KX1, RX1, EAVE_Y1, EAVE_Y1 + 350)
v1.chain_v(KX1, [FY0, TERR_Y, FACE_B, FY1], KX1 + 1500)
v1.chain_v(KX1, PY_END, KX1 + 1000)
v1.dim_v(RX1, EAVE_Y0, FY0, KX1 + 1000)
v1.chain_h([STRIP_X0, 3590, SLAB_X1], FY0, FY0 - 450)
v1.dim_h(WALL_J, SLAB_X1, FY0, FY0 - 450)
for n, x in (("G", 0), ("H", 2400), ("J", 5400)):
    v1.circle(x, -2050, 200, "K-TEXT")
    v1.text(n, x, -2050, align=TA.MIDDLE_CENTER)
    v1.line((x, -1850), (x, -1650), "K-TEXT")
title("1  KATTORAKENNE JA PILARIT 1:50", 750, 13900,
      "pilarit liimapuu 115x115, palkit sahatavara C24, vasat 48x98 k900")

ny_end = notes(14000, 13900)
assert ny_end > 375 + 2500 + 150, f"selitykset eivät mahdu: {ny_end}"
finish_sheet(1, "Kattorakenne ja pilarit, rakennetyypit")

# ================================================================ ARKKI 2
start_sheet()
# ================================================================ 2 LATTIARUNKO
v2 = View(1700, 8400)
existing_plan(v2, roof=False)
v2.pl([(-65, -65), (SLAB_X1, -65), (SLAB_X1, TSLAB_Y1), (WALL_J, TSLAB_Y1), (WALL_J, 4265), (-65, 4265)],
      "K-EXIST", closed=True)
v2.text("terassilaatta", 5880, 800, h=TH * 0.8, layer="K-EXIST", align=TA.MIDDLE_CENTER)
new_floor_outline(v2)
# pituuspalkit 2x48x123
for y in LONG_Y:
    x0 = WALL_J if y > TSLAB_Y1 else (STRIP_X0 if y < TERR_Y else SLAB_X1)
    v2.rect(x0, y - 48, KX1, y + 48, "K-FRAME")
    v2.line((x0, y), (KX1, y), "K-FRAME")
    if y > FACE_B:                                             # kiinnitys laatan reunaan
        v2.rect(x0 - 6, y - 70, x0 + 60, y + 70, "K-STEEL")
# reunapalkki 48x123 terassilaatan takareunaan (seinälinjasta laatan päätyyn)
v2.rect(WALL_J, TSLAB_Y1, SLAB_X1, TSLAB_Y1 + 48, "K-FRAME")
for xx in (WALL_J + 250, SLAB_X1 - 250):
    v2.rect(xx - 70, TSLAB_Y1 - 6, xx + 70, TSLAB_Y1 + 60, "K-STEEL")
v2.rect(STRIP_X0, STRIP_REAR - 24, SLAB_X1, STRIP_REAR + 24, "K-FRAME")
# poikkipalkit 48x123 pituuspalkkien väliin
xs = [SLAB_X1 + 24 + i * CROSS_CC for i in range(int((KX1 - SLAB_X1 - 48) / CROSS_CC) + 1)]
if KX1 - 24 - xs[-1] > 100:
    xs.append(KX1 - 24)
xs_rear = [WALL_J + 24, (WALL_J + SLAB_X1) / 2 + 12]          # seinälinjan ja laatan päädyn välillä
for a, b in zip(LONG_Y, LONG_Y[1:]):
    for x in xs:
        v2.rect(x - 24, a + 48, x + 24, b - 48, "K-FRAME")
    if b > TSLAB_Y1:
        lo = a + 48 if a > TSLAB_Y1 else TSLAB_Y1 + 48
        for x in xs_rear:
            v2.rect(x - 24, lo, x + 24, b - 48, "K-FRAME")
x = STRIP_X0 + 24
while x < SLAB_X1:
    v2.rect(x - 24, LONG_Y[0] + 48, x + 24, STRIP_REAR - 24, "K-FRAME")
    x += CROSS_CC
# perustukset
for fx in FOOT_X:
    for y in LONG_Y:
        v2.circle(fx, y, 125, "K-FOOT")
for fx in STRIP_FOOT_X:
    for y in (LONG_Y[0], STRIP_REAR):
        v2.circle(fx, y, 125, "K-FOOT")
for y in LONG_Y:
    if y < FACE_B + 200 or y > TSLAB_Y1:
        v2.circle(X_IN, y, 125, "K-FOOT")
for xs_, y in ((PXF, PF), (PXR, PR)):
    for x in xs_:
        v2.rect(x - 150, y - 150, x + 150, y + 150, "K-FOOT")
if TER_CUT:                                                     # katkaistun terassin kohta: kansi betonin päälle
    v2.rect(WALL_J, GW_Y + 45, SLAB_X1, TSLAB_Y1, "K-DECK")
    v2.hatch([(WALL_J, GW_Y + 45), (SLAB_X1, GW_Y + 45), (SLAB_X1, TSLAB_Y1), (WALL_J, TSLAB_Y1)], "K-DECK",
             "ANSI31", 1.2)
    v2.text("kansi betonin päälle +0.028", (WALL_J + SLAB_X1) / 2, TSLAB_Y1 + 120, h=TH * 0.6,
            layer="K-DECK", align=TA.BOTTOM_CENTER)
elif VE2:
    v2.text("terassi +0.165 säilyy", (WALL_J + SLAB_X1) / 2, TSLAB_Y1 + 120, h=TH * 0.6,
            layer="K-EXIST", align=TA.BOTTOM_CENTER)
if VE2:
    v2.text("pituuspalkki lasiseinän alle", 7900, GW_Y + 80, h=TH * 0.7, layer="K-FRAME", align=TA.BOTTOM_CENTER)
for y in PY_END[1:-1]:
    v2.rect(X_OUT - 150, y - 150, X_OUT + 150, y + 150, "K-FOOT")
posts_plan(v2)
# lautojen suunta
v2.line((7300, 3650), (8500, 3650), "K-DECK")
v2.pl([(8350, 3720), (8500, 3650), (8350, 3580)], "K-DECK")
v2.text("kansilaudoitus 28x120 kyll., rako 5, pituussuuntaan", 6400, FY0 - 900 - 4.8 * TH, layer="K-DECK")
v2.text("(terassin kohdalla laatan päätyyn, sen takana seinälinjaan J)", 6400, FY0 - 900 + 1.6 * TH, layer="K-FRAME")
v2.text("pituuspalkit 2x48x123 kyll. (6 linjaa), laatan reunaan kulmateräksillä", 6400, FY0 - 900,
        layer="K-FRAME")
v2.text(f"poikkipalkit 48x123 kyll. pituuspalkkien väliin k{CROSS_CC}, palkkikengät", 6400,
        FY0 - 900 - 1.6 * TH, layer="K-FRAME")
v2.text("○ pilarianturat ø250 palkkien alla, □ pilarien anturat 300x300 - routasyvyys tarkennetaan",
        6400, FY0 - 900 - 3.2 * TH, layer="K-FOOT")
v2.chain_h([WALL_J, X_IN] + FOOT_X, FY1, FY1 + 450)
v2.chain_h([STRIP_X0] + STRIP_FOOT_X[1:], FY0, FY0 - 450)
v2.chain_v(KX1, LONG_Y, KX1 + 600)
title("2  LATTIARUNKO JA PERUSTUKSET 1:50", 750, 13900,
      "lattian yläpinta ±0.000 = pohjalaatan yläpinta, palkkien yläpinta -0.028")

# ================================================================ korkeusnäkymien osat
def roof_band_gable(v):
    """keittiökatto päätynäkymässä: pinta, vasan alapinta, palkkien päät"""
    for off in (0, BATTEN + SHEET, ROOF_BUILD):
        v.pl([(EAVE_Y0, ktop(EAVE_Y0) - off), (YC, K_RIDGE - off), (EAVE_Y1, ktop(EAVE_Y1) - off)], "K-ROOF")
    for ue, s in ((EAVE_Y0, 1), (EAVE_Y1, -1)):
        v.line((ue, ktop(ue)), (ue, ktop(ue) - ROOF_BUILD), "K-ROOF")


def main_roof_gable(v):
    for off in (0, MAIN_T):
        v.pl([(-870, mtop(-870) - off), (YC, MAIN_RIDGE - off), (4800, mtop(4800) - off)], "K-EXIST")
    v.pl([(-65, 0), (-65, mtop(-65) - 220), (YC, MAIN_RIDGE - 220), (4265, mtop(4265) - 220), (4265, 0)],
         "K-EXIST")


def cladding(v, u0, u1, z1, step=100):
    v.rect(u0, 0, u1, z1, "K-WALL")
    z = step
    while z < z1 - 30:
        v.line((u0, z), (u1, z), "K-WALL")
        z += step


def glass_elev(v, u0, u1, t0, t1, z0=0, layer="K-GLASS"):
    """lasiosa: karmi (ulkoreuna, yläreuna voi olla vino) + lasin reuna + heijastusviivat"""
    f = GLASS_F
    v.pl([(u0, z0), (u1, z0), (u1, t1), (u0, t0)], layer, closed=True)
    k = (t1 - t0) / (u1 - u0)
    g0, g1 = t0 + k * f - f, t1 - k * f - f
    v.pl([(u0 + f, z0 + f), (u1 - f, z0 + f), (u1 - f, g1), (u0 + f, g0)], layer, closed=True)
    w = u1 - u0
    for c, L in ((0.35, 0.18), (0.45, 0.10)):
        uc = u0 + c * w
        zc = z0 + 0.5 * (t0 + t1 - 2 * z0) * 0.55
        v.line((uc, zc), (uc + L * w, zc + L * w), layer)


# ================================================================ 3 PÄÄTYJULKISIVU (kesäkeittiön päästä)
v3 = View(14800, 9550)
v3.line((-1800, GROUND), (5300, GROUND), "K-EXIST")
main_roof_gable(v3)
v3.rect(TERR_Y, 0, FACE_B, 165, "K-EXIST")
v3.rect(FY0, FLOOR_BOT, FY1, 0, "K-FLOOR")
v3.line((FY0, -DECK), (FY1, -DECK), "K-FLOOR")
for y, h, _ in BEAMS:
    t = beam_top(y)
    v3.rect(y - BW_OF[h] / 2, t - h, y + BW_OF[h] / 2, t, "K-BEAM")
    if h == PURL_B:
        v3.line((y, t - h), (y, t), "K-BEAM")
    v3.rect(y - P / 2, 0, y + P / 2, t - h, "K-POST")
under = lambda y: ktop(y) - ROOF_BUILD                       # vasojen alapinta päätylinjassa
for i, (a, b) in enumerate(zip(PY_END, PY_END[1:])):
    if not (VE2 and i == 0):
        glass_elev(v3, a + P / 2, b - P / 2, under(a + P / 2), under(b - P / 2))
roof_band_gable(v3)
post_top = {y: beam_top(y) - h for y, h, _ in BEAMS}
for i, j in ROD_BAYS:                                   # vetotangot ristiin uloimmissa väleissä
    a, b = PY_END[i] + P / 2, PY_END[j] - P / 2
    zt = min(post_top[PY_END[i]], post_top[PY_END[j]]) - 150
    v3.line((a, 150), (b, zt), "K-BRACE")
    v3.line((a, zt), (b, 150), "K-BRACE")
v3.text("vetotangot ø12", (PY_END[3] + PY_END[4]) / 2, 1100, h=TH * 0.8, layer="K-BRACE", align=TA.BOTTOM_CENTER)
v3.level(-1700, 0, "±0.000", 700)
v3.level(-1700, K_RIDGE, f"+{K_RIDGE / 1000:.3f}".replace(".", ","), 700)
v3.level(-1700, MAIN_RIDGE, "N+3,300", 700)
v3.level(-1700, round(EDGE_BOT), f"+{EDGE_BOT / 1000:.3f}".replace(".", ",") + " reunapalkin alapinta", 700)
v3.text("valokate 22,5°", 600, ktop(600) + 120, rot=22.5, layer="K-ROOF")
v3.text("lasitus koko korkeudelle", YC, 1100, layer="K-GLASS", align=TA.BOTTOM_CENTER)
if VE2:
    v3.text("avoin", (PF + PU1) / 2, 500, h=TH * 0.8, layer="K-TEXT", align=TA.BOTTOM_CENTER)
v3.chain_h(PY_END, 0, -800)
v3.dim_h(FY0, FY1, 0, -1250)
title("3  PÄÄTYJULKISIVU 1:50", 13000, 13900, "kesäkeittiön päästä rakennusta kohti")

finish_sheet(2, "Lattiarunko ja perustukset, päätyjulkisivu")

# ================================================================ ARKKI 3
start_sheet()
# ================================================================ 4 JULKISIVU ETUSIVULTA
v4 = View(1900, 9800)
v4.line((-900, GROUND), (11300, GROUND), "K-EXIST")
v4.rect(-65, GROUND, SLAB_X1, 0, "K-EXIST")
v4.rect(-230, 0, 5630, 2010, "K-EXIST")
v4.rect(-600, 2010, 2225, 2140, "K-EXIST")
v4.rect(2225, 1900, 6410, 2030, "K-EXIST")
v4.pl([(-600, 2140), (-600, MAIN_RIDGE), (6000, MAIN_RIDGE), (6000, 3110), (6410, 3110), (6410, 2030)],
      "K-EXIST")
v4.text("SAUNA (olemassa oleva, ks. sauna_julkisivut_1-50)", 2700, 1000, layer="K-EXIST",
        align=TA.MIDDLE_CENTER)
v4.rect(2630, 0, 3590, 165, "K-EXIST")
v4.rect(3590, 0, SLAB_X1, 165, "K-EXIST")
v4.rect(STRIP_X0, 0, 2630, 165, "K-FLOOR")
v4.rect(STRIP_X0, FLOOR_BOT, KX1, 0, "K-FLOOR")
v4.line((STRIP_X0, -DECK), (KX1, -DECK), "K-FLOOR")
eave = ktop(EAVE_Y0)
v4.rect(6410, eave - ROOF_BUILD, RX1, eave, "K-ROOF")
v4.pl([(6410, eave), (6410, K_RIDGE), (RX1, K_RIDGE), (RX1, eave)], "K-ROOF")
v4.rect(RX1 - 48, eave, RX1, K_RIDGE, "K-ROOF")
v4.rect(6410, EDGE_BOT, RX1 - 48, beam_top(PF), "K-BEAM")
for x in PXF:
    v4.rect(x - P / 2, 0, x + P / 2, EDGE_BOT, "K-POST")
if not VE2:
    for i, (a, b) in enumerate(zip(PX, PX[1:])):
        if i != DOOR_BAY:
            glass_elev(v4, a + P / 2, b - P / 2, EDGE_BOT, EDGE_BOT)
    glass_elev(v4, GAP_X0, X_IN - P / 2, EDGE_BOT, EDGE_BOT, z0=165)       # kiinteä lasi terassin päällä
    # liukuovi (ovilehti pilarien edessä, yläkisko reunapalkin alapinnassa)
    a, b = PX[DOOR_BAY] + P / 2 - 30, PX[DOOR_BAY + 1] - P / 2 + 30
    DOOR_TOP = EDGE_BOT - 60
    v4.rect(a - 40, DOOR_TOP, b + (b - a) + P + 40, EDGE_BOT, "K-GLASS")    # yläkisko
    glass_elev(v4, a, b, DOOR_TOP, DOOR_TOP, z0=10)
    v4.rect(b - 140, 950, b - 110, 1250, "K-GLASS")                          # vedin
    v4.text("liukuovi", (a + b) / 2, DOOR_TOP - 300, h=TH * 0.8, layer="K-GLASS", align=TA.BOTTOM_CENTER)
    v4.dim_v(a, 10, DOOR_TOP, a - 250, f"{round(DOOR_TOP - 10)}")
else:
    # lasiseinä taustalla välipalkin linjassa: näkyvä osa reunapalkin alapintaan, yläosa katkoviivalla
    gz0 = 165 if not TER_CUT else 28
    top = min(PURL_BOT, EDGE_BOT)
    v4.rect(WALL_J, gz0, WALL_J + MUL, top, "K-GLASS")
    for i, (a, b) in enumerate(GW_MODS):
        if i < 2:
            v4.rect(b, 0, b + MUL, top, "K-GLASS")
        if i != GW_DOOR:
            glass_elev(v4, a, b, top, top, z0=0 if a > SLAB_X1 else gz0)
        v4.line((a, PURL_BOT), (b, PURL_BOT), "K-HIDDEN")
    a, b = GW_MODS[GW_DOOR]
    a, b = a - 30, b + 30
    glass_elev(v4, a, b, top, top, z0=10)
    v4.line((a, GW_DOOR_TOP), (b, GW_DOOR_TOP), "K-HIDDEN")
    v4.rect(b - 140, 950, b - 110, 1250, "K-GLASS")
    v4.text("liukuovi", (a + b) / 2, 1500, h=TH * 0.8, layer="K-GLASS", align=TA.BOTTOM_CENTER)
    v4.text("lasiseinä taustalla (y 1046)", (GW_MODS[2][0] + GW_MODS[2][1]) / 2, 1500, h=TH * 0.7,
            layer="K-GLASS", align=TA.BOTTOM_CENTER)
    v4.dim_v(a, 10, GW_DOOR_TOP, a - 250, f"{round(GW_DOOR_TOP - 10)}")
    v4.chain_h([WALL_J] + [m for ab in GW_MODS for m in ab] + [X_OUT + P / 2], 0, -1600)
v4.level(KX1 + 200, 0, "±0.000")
v4.level(KX1 + 200, round(eave), f"+{eave / 1000:.3f} räystäs".replace(".", ","))
v4.level(KX1 + 200, K_RIDGE, f"+{K_RIDGE / 1000:.3f}".replace(".", ","))
v4.chain_h(PXF, 0, -700)
v4.chain_h([WALL_J, KX1, RX1], 0, -1150)
title("4  JULKISIVU ETUSIVULTA 1:50", 750, 13900,
      "etusivu lasitettu koko korkeudelle, liukuovi" if not VE2 else
      "etusivu avoin katos, lasiseinä ja liukuovi välipalkin linjassa")

# ================================================================ 5 JULKISIVU TAKASIVULTA (peilattu)
v5 = View(12750, 3600, sign=-1)
v5.line((-900, GROUND), (11300, GROUND), "K-EXIST")
v5.rect(-65, GROUND, WALL_J, 0, "K-EXIST")
v5.rect(-230, 0, 5630, 2010, "K-EXIST")
v5.rect(-600, 2010, 6000, 2150, "K-EXIST")
v5.pl([(-600, 2150), (-600, MAIN_RIDGE), (6000, MAIN_RIDGE), (6000, 2150)], "K-EXIST")
v5.text("SAUNA (olemassa oleva)", 2700, 1000, layer="K-EXIST", align=TA.MIDDLE_CENTER)
v5.rect(WALL_J, FLOOR_BOT, KX1, 0, "K-FLOOR")
v5.line((WALL_J, -DECK), (KX1, -DECK), "K-FLOOR")
v5.rect(6000, eave - ROOF_BUILD, RX1, eave, "K-ROOF")
v5.pl([(6000, eave), (6000, K_RIDGE), (RX1, K_RIDGE), (RX1, eave)], "K-ROOF")
v5.rect(RX1 - 48, eave, RX1, K_RIDGE, "K-ROOF")
v5.rect(6000, EDGE_BOT, RX1 - 48, beam_top(PR), "K-BEAM")
cladding(v5, LOG_END, KX1, beam_top(PR))                        # ulkoverhous pilarien ja palkin ulkopuolella
for x in PXR:
    v5.rect(x - P / 2, 0, x + P / 2, EDGE_BOT, "K-HIDDEN")
v5.level(KX1 + 200, 0, "±0.000")
v5.level(KX1 + 200, K_RIDGE, f"+{K_RIDGE / 1000:.3f}".replace(".", ","))
v5.chain_h([X_IN] + PX[1:], 0, -700)
v5.dim_v(KX1, 0, beam_top(PR), KX1 + 900)
title("5  JULKISIVU TAKASIVULTA 1:50", 750, 7700, "takaseinä umpi koko korkeudelta, levyjäykistetty")

finish_sheet(3, "Julkisivut etu- ja takasivulta")
print(f"VE{VE}: glass wall modules {[round(b - a) for a, b in GW_MODS]}, door top {GW_DOOR_TOP:.0f}, "
      f"front posts {[round(x) for x in PXF]}")
print(f"edge beam bottom {EDGE_BOT:.0f}, eave {eave:.0f}, posts x {[round(x) for x in PX]}, "
      f"posts y {[round(y) for y in PY_END]}, long beams {[round(y) for y in LONG_Y]}, rafters {len(RAFT_X)}")
