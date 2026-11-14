"""Fotomontaasi: kesäkeittiö piirrettynä nykytilan valokuvaan (etusivu, SIVU 2 -suunta).

Kuva kalibroitu rakennuksen mittoihin: julkisivutaso (seinän B ulkopinta y=-65) 0.218 px/mm,
kamera ~8 m julkisivusta, ~0.9 m lattiatason yläpuolella. Geometria build_kesakeittio_dxf.py:n mukaan.
Käyttö: python photomontage_kesakeittio.py <valokuva> [ulostulo]
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "kesakeittio_fotomontaasi.jpg")

# ---- kamera
D, K = 8000.0, 1744.0          # etäisyys julkisivusta, s = K / (D + syvyys)
CX, CAM_X, CY, CAM_Z = 1000.0, 3339.0, 1097.0, 884.0
FACADE_Y = -65


def P(x, y, z):
    s = K / (D + (y - FACADE_Y))
    return (CX + s * (x - CAM_X), CY - s * (z - CAM_Z))


# ---- geometria (mm, kuten piirroksissa)
TAN = math.tan(math.radians(22.5))
SLAB_X1, KX1, WALL_J, LOG_END = 6302, 10302, 5465, 5630
FY0, FY1, TERR_Y = -1360, 4265, -735
P2 = 115 / 2
PF, PR, YC = -65 + P2, 4265 - P2, 2100
PU1, PU2 = (PF + YC) / 2, (PR + YC) / 2
X_IN, X_OUT = SLAB_X1 + P2, KX1 - P2
PX = [X_IN + i * (X_OUT - X_IN) / 3 for i in range(4)]
K_RIDGE = 3130
ROOF_BUILD = 50 + 98 / math.cos(math.radians(22.5))
RX0, RX1 = 5650, KX1 + 500
EAVE0, EAVE1 = -600, 4800


def ktop(y):
    return K_RIDGE - abs(y - YC) * TAN


def beam_top(y):
    return ktop(y) - ROOF_BUILD + 30


# ---- värit
WOOD = (92, 60, 43)
DECK_TOP, DECK_RIM = (112, 82, 63), (74, 50, 38)
WHITE = (226, 226, 218)


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c)


# ---- kuva + laajennus oikealle
photo = Image.open(SRC).convert("RGB")
W0, H0 = photo.size
EXT = 900
canvas = Image.new("RGB", (W0 + EXT, H0))
canvas.paste(photo, (0, 0))
# yläosa (puut, taivas): leveä peilattu kaista katon yläpuolelta -> ei toistoa
TOP_H = 700
top_src = photo.crop((W0 - EXT, 0, W0, TOP_H))                # kopio ilman peilausta (ei symmetriaa)
# alaosa (pensaat, sora): rakennuksen oikealta puolelta peilaten vuorotellen
bot = Image.new("RGB", (EXT, H0 - TOP_H + 80))
strip = photo.crop((1760, TOP_H - 80, W0, H0))
x, flip = 0, True
while x < EXT:
    bot.paste(strip.transpose(Image.FLIP_LEFT_RIGHT) if flip else strip, (x, 0))
    x += strip.width
    flip = not flip
canvas.paste(bot, (W0, TOP_H - 80))
grad = Image.linear_gradient("L").resize((EXT, 80)).transpose(Image.FLIP_TOP_BOTTOM)
canvas.paste(top_src.crop((0, 0, EXT, TOP_H - 80)), (W0, 0))
canvas.paste(top_src.crop((0, TOP_H - 80, EXT, TOP_H)), (W0, TOP_H - 80), grad)
hgrad = Image.linear_gradient("L").rotate(90, expand=True).resize((80, TOP_H)).transpose(Image.FLIP_LEFT_RIGHT)
edge = photo.crop((W0 - 80, 0, W0, TOP_H)).transpose(Image.FLIP_LEFT_RIGHT)   # pehmeä sauma
canvas.paste(edge, (W0, 0), hgrad)

layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
dr = ImageDraw.Draw(layer)


def quad(pts3, fill, alpha=255, outline=None, width=1):
    pts = [P(*p) for p in pts3]
    dr.polygon(pts, fill=fill + (alpha,), outline=(outline + (alpha,)) if outline else None, width=width)


def line3(a, b, col, w=2, alpha=255):
    dr.line([P(*a), P(*b)], fill=col + (alpha,), width=w)


def box(x0, x1, y0, y1, z0, z1, col):
    """näkyvät tahkot: etu (-y), vasen (-x, kamera vasemmalla), ylä- tai alapinta"""
    if CAM_Z < z0:
        quad([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], shade(col, 0.55))
    elif CAM_Z > z1:
        quad([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], shade(col, 1.15))
    if CAM_X < x0:
        quad([(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], shade(col, 0.72))
    quad([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], col)


def boards_plane_y(y, x0, x1, z0, z1, col, step=100):
    quad([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], col)
    z = z0 + step
    while z < z1 - 20:
        line3((x0, y, z), (x1, y, z), shade(col, 0.7), 2)
        z += step
    box(x0 - 10, x1 + 10, y - 40, y, z1, z1 + 28, shade(col, 1.1))


def boards_plane_x(x, y0, y1, z0, z1, col, step=100):
    quad([(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)], shade(col, 0.85))
    z = z0 + step
    while z < z1 - 20:
        line3((x, y0, z), (x, y1, z), shade(col, 0.6), 2)
        z += step


def roof_slope(y_eave, alpha, under):
    """valokatteinen lape: vasat, ruoteet, kate läpikuultavana"""
    ze, zr = ktop(y_eave), K_RIDGE
    xs = []
    x = RX1 - 24
    while x > RX0 + 300:
        xs.append(x)
        x -= 900
    xs.append(RX0 + 24)
    for x in xs:                                               # vasat 48x98
        line3((x, y_eave, ze - ROOF_BUILD + 50), (x, YC, zr - ROOF_BUILD + 50), shade(WOOD, 0.8), 5)
    n = 8
    for i in range(1, n):                                      # ruoteet
        t = i / n
        y = y_eave + (YC - y_eave) * t
        z = ze + (zr - ze) * t - 50
        line3((RX0, y, z), (RX1, y, z), shade(WOOD, 0.9), 2)
    quad([(RX0, y_eave, ze), (RX1, y_eave, ze), (RX1, YC, zr), (RX0, YC, zr)], (214, 226, 232), alpha)
    x = RX0 + 76
    while x < RX1:                                             # katelevyn profiili
        line3((x, y_eave, ze), (x, YC, zr), (240, 244, 246), 1, 90)
        x += 76
    # räystäs- ja päätylaudat (valkoiset kuten rakennuksessa)
    quad([(RX0, y_eave, ze - 150), (RX1, y_eave, ze - 150), (RX1, y_eave, ze), (RX0, y_eave, ze)],
         shade(WHITE, 0.62 if under else 1.0))
    quad([(RX1, y_eave, ze - 150), (RX1, YC, zr - 150), (RX1, YC, zr), (RX1, y_eave, ze)], shade(WHITE, 0.9))


# ================================================================ piirto kaukaa lähelle
# lattia
quad([(WALL_J, 1600, 0), (KX1, 1600, 0), (KX1, FY1, 0), (WALL_J, FY1, 0)], DECK_TOP)
quad([(SLAB_X1, FY0, 0), (KX1, FY0, 0), (KX1, 1600, 0), (SLAB_X1, 1600, 0)], DECK_TOP)
quad([(2430, FY0, 0), (SLAB_X1, FY0, 0), (SLAB_X1, TERR_Y, 0), (2430, TERR_Y, 0)], DECK_TOP)
for y in range(FY0 + 125, FY1, 125):                           # lautasaumat
    x0 = 2430 if y < TERR_Y else (SLAB_X1 if y < 1600 else WALL_J)
    line3((x0, y, 0), (KX1, y, 0), shade(DECK_TOP, 0.75), 1)
quad([(2430, FY0, -151), (KX1, FY0, -151), (KX1, FY0, 0), (2430, FY0, 0)], DECK_RIM)
quad([(2430, FY0, -151), (2430, TERR_Y, -151), (2430, TERR_Y, 0), (2430, FY0, 0)], shade(DECK_RIM, 0.8))
# takalape (näkyy etuosan alta)
roof_slope(EAVE1, 70, True)
# takaseinä umpiosa, takapilarit, takareunapalkki
boards_plane_y(FY1 - 22, LOG_END, KX1 - 22, 0, 1000, shade(WOOD, 0.85))
for x in PX:
    box(x - P2, x + P2, PR - P2, PR + P2, 0, beam_top(PR) - 135, WOOD)
box(5700, RX1 - 48, PR - P2, PR + P2, beam_top(PR) - 135, beam_top(PR), WOOD)
box(WALL_J, RX1 - 48, PU2 - P2, PU2 + P2, beam_top(PU2) - 225, beam_top(PU2), WOOD)
# päätyseinä
boards_plane_x(KX1 - 22, -65, FY1 - 22, 0, 1000, WOOD)
for y, h in ((PU2, 225), (YC, 225), (PU1, 225)):
    box(X_OUT - P2, X_OUT + P2, y - P2, y + P2, 0, beam_top(y) - h, WOOD)
box(WALL_J, RX1 - 48, YC - P2, YC + P2, beam_top(YC) - 225, beam_top(YC), WOOD)
box(WALL_J, RX1 - 48, PU1 - P2, PU1 + P2, beam_top(PU1) - 225, beam_top(PU1), WOOD)
# etupilarit ja etureunapalkki
for x in PX:
    box(x - P2, x + P2, PF - P2, PF + P2, 0, beam_top(PF) - 135, shade(WOOD, 1.08))
box(5700, RX1 - 48, PF - P2, PF + P2, beam_top(PF) - 135, beam_top(PF), shade(WOOD, 1.08))
# etulape
roof_slope(EAVE0, 95, False)

# ---- nykyisen katon ja kuistin peittävyys: alkuperäiset pikselit jäävät päälle
mask = Image.new("L", canvas.size, 0)
ImageDraw.Draw(mask).polygon([(80, 815), (375, 680), (1418, 680), (1718, 808), (1742, 826), (1742, 868),
                              (80, 868)], fill=255)
ImageDraw.Draw(mask).polygon([(1418, 680), (1650, 680), (1650, 868), (1418, 868)], fill=0)
ImageDraw.Draw(mask).polygon([(1418, 680), (1718, 808), (1742, 826), (1742, 868), (1418, 868)], fill=255)
md = ImageDraw.Draw(mask)
md.rectangle([0, 680, 1418, 1300], fill=255)            # rakennus peittää taakseen jäävät osat
md.rectangle([1418, 860, 1466, 1262], fill=255)         # kuistin pilari linjalla J
md.rectangle([1055, 1250, 1660, 1302], fill=255)        # terassin otsa
layer = layer.filter(ImageFilter.GaussianBlur(0.7))
# poistettava etuporras: korvataan porraskaistalla (kaista piirretty ylle), alue sen yläpuolella täytetään
rim = photo.crop((1262, 1262, 1459, 1345))               # terassin otsa + perusta portaan vierestä
canvas.paste(rim, (1058, 1262))
# varjo kesäkeittiön alla
shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
ImageDraw.Draw(shadow).polygon([P(SLAB_X1, -100, 0), P(KX1, -100, 0), P(KX1, FY1, 1000), P(SLAB_X1, FY1, 1000)],
                               fill=(0, 0, 0, 40))
shadow = shadow.filter(ImageFilter.GaussianBlur(25))
base = canvas.convert("RGBA")
base = Image.alpha_composite(base, shadow)
out = Image.alpha_composite(base, layer)
out.paste(canvas.crop((0, 0) + canvas.size), (0, 0), mask)
out = out.convert("RGB")
out.save(OUT, quality=92)
print("saved", OUT, out.size)
