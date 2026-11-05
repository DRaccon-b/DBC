"""Grafiken fuer die Bewerbung: Ebenen-Schema (links -> rechts) und Editor-Mockup.

python3 tools/bewerbung_grafiken.py  ->  bewerbung/ebenen_schema.png, bewerbung/editor_idee.png
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EBENEN = os.path.join(ROOT, "maps/karte01/ebenen")
OUT = os.path.join(ROOT, "bewerbung")
T = 16            # Kachelgroesse
S = 2             # Vergroesserung
X0, Y0, W, H = 74, 30, 16, 12   # Ausschnitt in Kacheln
SPIELER = (81, 34)              # Kachel, auf der die Spielfigur steht (Wert 3 = hinter Baumkrone)

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BG = (24, 26, 33)
FG = (235, 236, 240)
MUTED = (150, 155, 170)
ROT = (230, 70, 70)
BLAU = (70, 130, 240)
GRUEN = (90, 200, 120)


def f(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def ausschnitt(name):
    im = Image.open(os.path.join(EBENEN, name)).convert("RGBA")
    box = (X0 * T, Y0 * T, (X0 + W) * T, (Y0 + H) * T)
    return im.crop(box)


def raster():
    r = json.load(open(os.path.join(EBENEN, "kollision.json")))["raster"]
    return [[int(c) for c in row[X0:X0 + W]] for row in r[Y0:Y0 + H]]


def spielfigur():
    """Einfache 16x24-Platzhalterfigur (eigenes Pixelart, kein fremdes Sprite)."""
    im = Image.new("RGBA", (16, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    kontur = (40, 30, 60, 255)
    d.ellipse((3, 20, 12, 23), fill=(0, 0, 0, 70))                  # Schatten
    d.rectangle((5, 15, 7, 21), fill=(50, 60, 110, 255), outline=kontur)   # Beine
    d.rectangle((8, 15, 10, 21), fill=(50, 60, 110, 255), outline=kontur)
    d.rectangle((3, 9, 12, 16), fill=(220, 80, 60, 255), outline=kontur)   # Jacke
    d.ellipse((3, 1, 12, 10), fill=(250, 210, 170, 255), outline=kontur)   # Kopf
    d.rectangle((3, 1, 12, 4), fill=(240, 180, 40, 255), outline=kontur)   # Haare/Kappe
    d.point([(6, 6), (9, 6)], fill=kontur)
    return im


def schachbrett(w, h, k=8):
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(0, h, k):
        for x in range(0, w, k):
            c = (58, 62, 74) if (x // k + y // k) % 2 else (44, 47, 57)
            d.rectangle((x, y, x + k - 1, y + k - 1), fill=c + (255,))
    return im


def gross(im):
    return im.resize((im.width * S, im.height * S), Image.NEAREST)


def kollisions_bild(boden, g, alpha=110):
    im = boden.copy()
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y, row in enumerate(g):
        for x, v in enumerate(row):
            if v == 2:
                d.rectangle((x * T, y * T, x * T + T - 1, y * T + T - 1), fill=ROT + (alpha,))
            elif v == 3:
                d.rectangle((x * T, y * T, x * T + T - 1, y * T + T - 1), fill=BLAU + (alpha,))
    im = Image.alpha_composite(Image.blend(im, Image.new("RGBA", im.size, (20, 20, 20, 255)), 0.35), ov)
    return im


def gitter(im, farbe=(255, 255, 255, 50), schritt=T * S):
    d = ImageDraw.Draw(im)
    for x in range(0, im.width, schritt):
        d.line((x, 0, x, im.height), fill=farbe)
    for y in range(0, im.height, schritt):
        d.line((0, y, im.width, y), fill=farbe)
    return im


def figur_pos():
    sx, sy = SPIELER
    px = (sx - X0) * T
    py = (sy - Y0) * T + T - 24 + 2
    return px, py


def ebenen_schema():
    boden = ausschnitt("ebene1_boden.png")
    oben = ausschnitt("ebene3_ueberlagerung.png")
    g = raster()
    fig = spielfigur()
    pw, ph = W * T * S, H * T * S

    p1 = gross(boden)
    p2 = gitter(gross(kollisions_bild(boden, g)), (255, 255, 255, 40))
    p3 = schachbrett(pw, ph)
    fl = Image.new("RGBA", boden.size, (0, 0, 0, 0))
    fl.alpha_composite(fig, figur_pos())
    p3.alpha_composite(gross(fl))
    p4 = schachbrett(pw, ph)
    p4.alpha_composite(gross(oben))
    fertig = boden.copy()
    fertig.alpha_composite(fig, figur_pos())
    fertig.alpha_composite(oben)
    p5 = gross(fertig)

    panels = [
        ("1  Ground layer", "drawn first, below everything", p1),
        ("2  Collision map", "red = blocked, blue = walk-behind", p2),
        ("3  Player / NPCs", "drawn on top of the ground", p3),
        ("4  Overlay layer", "tree tops, lamp heads, roofs", p4),
        ("=  In game", "player hidden under the canopy", p5),
    ]
    gap, pad, top, bottom = 70, 40, 150, 120
    cw = pad * 2 + len(panels) * pw + (len(panels) - 1) * gap
    ch = top + ph + bottom
    c = Image.new("RGBA", (cw, ch), BG + (255,))
    d = ImageDraw.Draw(c)
    d.text((pad, 30), "How the map layers work  (left to right = draw order)", font=f(40, True), fill=FG)
    d.text((pad, 86), "Example: Map 01, 16 x 12 tiles of 16 px, shown at 2x. The collision map is data only and is never drawn in game.",
           font=f(24), fill=MUTED)
    for i, (titel, unter, p) in enumerate(panels):
        x = pad + i * (pw + gap)
        c.alpha_composite(p, (x, top))
        rand = GRUEN if i == 4 else (90, 95, 110)
        d.rectangle((x - 2, top - 2, x + pw + 1, top + ph + 1), outline=rand, width=3)
        d.text((x, top + ph + 18), titel, font=f(30, True), fill=FG)
        d.text((x, top + ph + 62), unter, font=f(22), fill=MUTED)
        if i < len(panels) - 1:
            ax, ay = x + pw + 12, top + ph // 2
            sym = "=" if i == 3 else "+"
            d.text((ax + gap // 2 - 12, ay - 26), sym, font=f(44, True), fill=FG)
    # Markierung der Spielfigur im Endbild
    px, py = figur_pos()
    x5 = pad + 4 * (pw + gap)
    d.ellipse((x5 + px * S - 22, top + py * S - 18, x5 + (px + 16) * S + 22, top + (py + 24) * S + 18),
              outline=(255, 220, 80), width=3)
    c.convert("RGB").save(os.path.join(OUT, "ebenen_schema.png"))


def editor_idee():
    boden = ausschnitt("ebene1_boden.png")
    oben = ausschnitt("ebene3_ueberlagerung.png")
    g = raster()
    fertig = boden.copy()
    fertig.alpha_composite(oben)
    pw, ph = W * T * S, H * T * S

    canvas = fertig.copy()
    ov = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d0 = ImageDraw.Draw(ov)
    for y, row in enumerate(g):
        for x, v in enumerate(row):
            farbe = {2: ROT, 3: BLAU}.get(v)
            if farbe:
                d0.rectangle((x * T, y * T, x * T + T - 1, y * T + T - 1), fill=farbe + (70,))
    canvas = gitter(gross(Image.alpha_composite(canvas, ov)), (255, 255, 255, 45))

    # ausgewaehlte Laterne (Kachel 85, 37..40)
    lx, ly0, ly1 = 85 - X0, 37 - Y0, 40 - Y0
    dc = ImageDraw.Draw(canvas)
    dc.rectangle((lx * T * S - 2, ly0 * T * S - 2, (lx + 1) * T * S + 1, (ly1 + 1) * T * S + 1),
                 outline=(255, 220, 80), width=4)
    # Pinsel-Vorschau: Kachel wird gerade gesperrt
    bx, by = 13, 9
    dc.rectangle((bx * T * S, by * T * S, (bx + 1) * T * S - 1, (by + 1) * T * S - 1),
                 fill=ROT + (150,), outline=(255, 255, 255), width=2)

    tb_w, lp_w, top, pad = 300, 470, 110, 30
    cw = pad + tb_w + pad + pw + pad + lp_w + pad
    ly = top + 560
    ch = ly + 130
    c = Image.new("RGBA", (cw, ch), BG + (255,))
    d = ImageDraw.Draw(c)
    d.rectangle((0, 0, cw, 70), fill=(36, 39, 48))
    d.text((pad, 18), "Map Editor  -  concept", font=f(30, True), fill=FG)
    d.text((cw - 520, 24), "File   Edit   View   Export", font=f(22), fill=MUTED)

    # Werkzeugleiste
    tx = pad
    d.text((tx, top - 10), "TILE TOOLS", font=f(18, True), fill=MUTED)
    tools = [
        ("Walkable", GRUEN, False),
        ("Block", ROT, True),
        ("Walk-behind", BLAU, False),
    ]
    y = top + 24
    for name, col, aktiv in tools:
        d.rounded_rectangle((tx, y, tx + tb_w, y + 58), 10, fill=(52, 56, 70) if aktiv else (36, 39, 48),
                            outline=(255, 220, 80) if aktiv else (70, 74, 88), width=3 if aktiv else 1)
        d.rectangle((tx + 16, y + 17, tx + 40, y + 41), fill=col)
        d.text((tx + 56, y + 14), name, font=f(24, aktiv), fill=FG)
        y += 72
    y += 16
    d.text((tx, y), "OBJECT TOOLS", font=f(18, True), fill=MUTED)
    y += 34
    for name in ["Layer up  ▲", "Layer down  ▼", "Split at foot"]:
        d.rounded_rectangle((tx, y, tx + tb_w, y + 58), 10, fill=(36, 39, 48), outline=(70, 74, 88))
        d.text((tx + 20, y + 14), name, font=f(24), fill=FG)
        y += 72

    # Karte
    mx = pad + tb_w + pad
    c.alpha_composite(canvas, (mx, top))
    d.rectangle((mx - 2, top - 2, mx + pw + 1, top + ph + 1), outline=(90, 95, 110), width=2)

    # Ebenen-Panel
    px = mx + pw + pad
    d.text((px, top - 10), "LAYERS  (top = drawn last)", font=f(18, True), fill=MUTED)
    rows = [
        ("Overlay", "above player", [("tree crowns", False), ("lamp head", True)]),
        ("Player / NPCs", "runtime only", []),
        ("Ground", "below player", [("grass, path, water", False), ("lamp foot", True), ("tree trunks", False)]),
    ]
    y = top + 24
    for titel, info, items in rows:
        hoehe = 64 + 44 * len(items)
        d.rounded_rectangle((px, y, px + lp_w, y + hoehe), 10, fill=(36, 39, 48), outline=(70, 74, 88))
        d.text((px + 18, y + 14), titel, font=f(25, True), fill=FG)
        d.text((px + lp_w - 170, y + 19), info, font=f(19), fill=MUTED)
        iy = y + 58
        for name, sel in items:
            if sel:
                d.rounded_rectangle((px + 10, iy - 4, px + lp_w - 10, iy + 34), 6, fill=(70, 62, 30))
            d.text((px + 34, iy), ("▸ " if sel else "  ") + name, font=f(21), fill=(255, 220, 80) if sel else FG)
            iy += 44
        y += hoehe + 16
    d.text((px, y + 6), "▲ / ▼ move the selected part", font=f(20), fill=MUTED)
    d.text((px, y + 36), "between Ground and Overlay.", font=f(20), fill=MUTED)

    # Legende unten
    d.text((pad, ly), "Paint tiles: green = walkable (1), red = blocked (2), blue = walkable but hides the player (3).",
           font=f(22), fill=FG)
    d.text((pad, ly + 38), "Yellow frame = selected object (lamp). Its foot blocks the tile, its head is on the Overlay.",
           font=f(22), fill=MUTED)
    d.text((pad, ly + 72), "Export: ground.png, overlay.png, collision.json  -  plain PNG + JSON, easy to load in any engine.",
           font=f(22), fill=MUTED)
    c.convert("RGB").save(os.path.join(OUT, "editor_idee.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    ebenen_schema()
    editor_idee()
    print("ok")
