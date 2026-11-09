"""Erklaergrafik (englisch, dunkler Hintergrund) zum Zufallskarten-System -> maps/zufall/system_explained.png

  python3 tools/zufall_erklaerung.py [startwert]      (Standard 2; Karte muss mit 6x5 Feldern gebaut sein)
"""
import os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import zufall_stuecke as zs, zufall_karte as zk

ROOT = zk.ROOT
FONT = '/usr/share/fonts/opentype/inter/'
MONO = '/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Regular.ttf'
BG, PANEL, LINE = (18, 19, 22), (30, 32, 37), (58, 62, 70)
TXT, DIM, AKZ = (236, 238, 242), (150, 156, 166), (79, 208, 200)
START, BOSS = (79, 208, 200), (232, 92, 92)
N = zs.N


def f(stil, gr):
    p = {'b': 'Inter-Bold.otf', 's': 'Inter-SemiBold.otf', 'r': 'Inter-Regular.otf'}[stil]
    return ImageFont.truetype(os.path.join(FONT, p), gr)


def mono(gr):
    try:
        return ImageFont.truetype(MONO, gr)
    except OSError:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', gr)


def text_block(d, xy, txt, font, fill, breite, abstand=6):
    """Text mit Zeilenumbruch auf breite Pixel; gibt die y-Position danach zurueck."""
    x, y = xy
    for absatz in txt.split('\n'):
        zeile = ''
        for w in absatz.split(' '):
            t = (zeile + ' ' + w).strip()
            if d.textlength(t, font=font) > breite and zeile:
                d.text((x, y), zeile, font=font, fill=fill)
                y += font.size + abstand
                zeile = w
            else:
                zeile = t
        d.text((x, y), zeile, font=font, fill=fill)
        y += font.size + abstand
    return y


def raster_bild(raster, px, objekte=(), rahmen=True):
    im = zs.bild(raster, px).convert('RGB')
    d = ImageDraw.Draw(im)
    for _, x, y in objekte:
        d.ellipse((x * px + 1, y * px + 1, (x + 1) * px - 2, (y + 1) * px - 2), fill=(232, 92, 92))
    if rahmen:
        d.rectangle((0, 0, im.width - 1, im.height - 1), outline=(10, 10, 10))
    return im


def panel(d, box, nummer, titel):
    d.rounded_rectangle(box, 18, fill=PANEL)
    x, y = box[0] + 28, box[1] + 22
    d.ellipse((x, y, x + 40, y + 40), fill=AKZ)
    d.text((x + 20, y + 20), str(nummer), font=f('b', 22), fill=BG, anchor='mm')
    d.text((x + 56, y + 20), titel, font=f('b', 30), fill=TXT, anchor='lm')
    return x, y + 64


def pfeil(d, x0, x1, y):
    d.line((x0, y, x1 - 14, y), fill=AKZ, width=5)
    d.polygon([(x1, y), (x1 - 18, y - 11), (x1 - 18, y + 11)], fill=AKZ)


def main():
    startwert = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    gw, gh = 6, 5
    rnd = random.Random(startwert)                       # gleiche Reihenfolge wie zufall_karte.main
    for _ in range(50):
        boss_xy, start, belegt, verb, pfad = zk.grundriss(rnd, gw, gh)
        try:
            wahl = zk.einsetzen(rnd, gw, gh, boss_xy, start, belegt, verb)
            break
        except RuntimeError:
            continue
    karte = Image.open(os.path.join(ROOT, 'maps', 'zufall', 'karte_%d.png' % startwert)).convert('RGB')
    assert karte.size == (gw * N * 16, gh * N * 16), 'Karte erst mit 6x5 Feldern bauen'

    W, H = 2400, 2610
    im = Image.new('RGB', (W, H), BG)
    d = ImageDraw.Draw(im)
    # ------------------------------------------------------------ Kopf
    d.text((80, 64), 'Procedural Forest Dungeons', font=f('b', 64), fill=TXT)
    d.text((80, 148), 'Random maps assembled from hand-made map chunks  ·  Map 01 style  ·  16 × 16 px tiles',
           font=f('r', 30), fill=DIM)
    d.line((80, 210, W - 80, 210), fill=LINE, width=2)

    # ------------------------------------------------------------ 1 Stuecke + Kanten
    x, y = panel(d, (80, 250, W - 80, 900), 1, 'Hand-made chunks with standardised edges')
    y = text_block(d, (x, y), 'Every chunk is a 14 × 14 tile grid painted by hand. Its four sides are read from the '
                   'outer two tile rows and must be one of three edge types. Two chunks fit together whenever the '
                   'touching edges have the same type.', f('r', 24), DIM, 1000)
    # Gelaende-Legende
    ly = y + 14
    for c, name in (('F', 'forest'), ('G', 'meadow'), ('P', 'sand path'), ('W', 'pond')):
        d.rectangle((x, ly, x + 26, ly + 26), fill=zs.FARBE[c])
        d.text((x + 38, ly + 13), name, font=f('r', 24), fill=TXT, anchor='lm')
        x += 38 + d.textlength(name, font=f('r', 24)) + 40
    x = 108
    # Kantentypen
    ky = ly + 64
    for typ, name in (('Z', 'closed  –  forest, no passage'), ('W', 'forest path  –  narrow gap'),
                      ('O', 'open  –  wide meadow')):
        kante = zs.KANTE[typ]
        for i, c in enumerate(kante):
            for r in range(2):
                d.rectangle((x + i * 26, ky + r * 26, x + i * 26 + 24, ky + r * 26 + 24), fill=zs.FARBE[c])
        d.text((x + 14 * 26 + 30, ky + 26), typ, font=mono(40), fill=AKZ, anchor='lm')
        d.text((x + 14 * 26 + 80, ky + 26), name, font=f('s', 26), fill=TXT, anchor='lm')
        ky += 84
    d.text((x, ky + 6), 'The path always crosses an edge in the middle (columns 6–7),', font=f('r', 22), fill=DIM)
    d.text((x, ky + 36), 'so rotated and mirrored chunks still connect.', font=f('r', 22), fill=DIM)
    # Beispiel-Stuecke
    namen = ['weg_bogen', 'wiese_teich', 'weg_ecke', 'weg_gabel', 'sackgasse_teich', 'sackgasse_brunnen',
             'start_lager', 'lichtung_runenbaum']
    titel = {'weg_bogen': 'path bend', 'wiese_teich': 'meadow + pond', 'weg_ecke': 'corner',
             'weg_gabel': 'fork', 'sackgasse_teich': 'dead end: pond', 'sackgasse_brunnen': 'dead end: well',
             'start_lager': 'start: portal', 'lichtung_runenbaum': 'rune-tree glade'}
    px, sx, sy = 9, 1180, 370
    for i, n in enumerate(namen):
        st = next(s for s in zs.STUECKE if s['name'] == n)
        cx, cy = sx + (i % 4) * 270, sy + (i // 4) * 250
        im.paste(raster_bild(st['raster'], px, st.get('objekte', [])), (cx, cy))
        k = zs.kanten(st['raster'])
        d.text((cx, cy + N * px + 10), titel[n], font=f('s', 22), fill=TXT)
        d.text((cx + N * px + 10, cy), ''.join(k[(0, 0, s)] for s in 'NOSW'), font=mono(20), fill=AKZ)
        d.text((cx + N * px + 10, cy + 26), 'NESW', font=mono(14), fill=DIM)
    d.ellipse((sx, 868, sx + 14, 882), fill=(232, 92, 92))
    d.text((sx + 24, 875), 'fixed object (portal, well, rune tree …)', font=f('r', 20), fill=DIM, anchor='lm')

    # ------------------------------------------------------------ 2 Lagen
    x, y = panel(d, (80, 940, W - 80, 1380), 2, 'Every chunk in up to 8 orientations')
    text_block(d, (x, y), '4 rotations × mirror. Fixed objects move with the chunk but stay upright. '
               'The boss arena only turns 180° so its pair of rune stones stays symmetric to the tree.',
               f('r', 24), DIM, 2100)
    st = next(s for s in zs.STUECKE if s['name'] == 'sackgasse_findling')
    lx = x
    for l in zs.lagen(st):
        im.paste(raster_bild(l['raster'], 13, l.get('objekte', [])), (lx, y + 60))
        d.text((lx + 91, y + 60 + 14 * 13 + 14), l['lage'].replace('s', 'mirror ') + '°', font=f('r', 20),
               fill=DIM, anchor='mt')
        lx += 14 * 13 + 74
    d.text((x, 1328), '20 chunks  →  145 usable orientations', font=f('s', 24), fill=AKZ)

    # ------------------------------------------------------------ 3/4/5 Ablauf
    oben = 1420
    # 3 Grundriss
    x, y = panel(d, (80, oben, 700, oben + 1000), 3, 'Layout')
    zelle = 92
    gx0, gy0 = x + 10, y + 20
    bx, by = boss_xy
    boss = {(bx + a, by + b) for a in (0, 1) for b in (0, 1)}
    for cx in range(gw):
        for cy in range(gh):
            farbe = (36, 64, 46) if (cx, cy) not in belegt and (cx, cy) not in boss else (52, 58, 66)
            d.rectangle((gx0 + cx * zelle + 3, gy0 + cy * zelle + 3, gx0 + (cx + 1) * zelle - 3,
                         gy0 + (cy + 1) * zelle - 3), fill=farbe)
    d.rounded_rectangle((gx0 + bx * zelle + 3, gy0 + by * zelle + 3, gx0 + (bx + 2) * zelle - 3,
                         gy0 + (by + 2) * zelle - 3), 10, fill=(90, 40, 44))
    mitte = lambda c: (gx0 + c[0] * zelle + zelle // 2, gy0 + c[1] * zelle + zelle // 2)
    haupt = {frozenset((pfad[i], pfad[i + 1])) for i in range(len(pfad) - 1)}
    for v in verb:
        a, b = tuple(v)
        if a in boss: a = (bx + 0.5, by + 0.5) if False else a
        pa, pb = mitte(a), mitte(b)
        if a in boss or b in boss:
            aussen = b if a in boss else a
            pa, pb = mitte(aussen), (gx0 + (bx + 1) * zelle, gy0 + (by + 1) * zelle)
            d.line((*pa, *pb), fill=BOSS, width=8)
        else:
            d.line((*pa, *pb), fill=(240, 196, 120) if v in haupt else (150, 130, 96), width=8 if v in haupt else 4)
    for c in belegt:
        r = 9 if c != start else 18
        d.ellipse((mitte(c)[0] - r, mitte(c)[1] - r, mitte(c)[0] + r, mitte(c)[1] + r),
                  fill=START if c == start else (220, 220, 220))
    bm = (gx0 + (bx + 1) * zelle, gy0 + (by + 1) * zelle)
    d.ellipse((bm[0] - 20, bm[1] - 20, bm[0] + 20, bm[1] + 20), fill=BOSS)
    ly = gy0 + gh * zelle + 30
    for farbe, txt, form in ((START, 'start camp (portal)', 'o'), (BOSS, 'boss arena (2 × 2 cells)', 'o'),
                             ((240, 196, 120), 'main path', '-'), ((150, 130, 96), 'side branch → dead end', '-'),
                             ((36, 64, 46), 'unused cell → dense forest', '#')):
        if form == 'o':
            d.ellipse((x + 10, ly, x + 34, ly + 24), fill=farbe)
        elif form == '-':
            d.line((x + 6, ly + 12, x + 38, ly + 12), fill=farbe, width=7)
        else:
            d.rectangle((x + 10, ly, x + 34, ly + 24), fill=farbe)
        d.text((x + 50, ly + 12), txt, font=f('r', 22), fill=TXT, anchor='lm')
        ly += 38
    text_block(d, (x, ly + 14), 'Start and boss as far apart as possible, a winding main path between them, '
               'side branches and sometimes a loop.', f('r', 22), DIM, 560)
    pfeil(d, 706, 754, oben + 300)

    # 4 Stuecke einsetzen
    x, y = panel(d, (760, oben, 1380, oben + 1000), 4, 'Fit chunks')
    rb = Image.new('RGB', (gw * N, gh * N))
    for (fx, fy), l in wahl.items():
        rb.paste(zs.bild(l['raster'], 1), (fx * N, fy * N))
    rb = rb.resize((gw * N * 6, gh * N * 6), Image.NEAREST)
    rd = ImageDraw.Draw(rb)
    for (fx, fy), l in wahl.items():
        w, h = l['felder']
        rd.rectangle((fx * N * 6, fy * N * 6, (fx + w) * N * 6 - 1, (fy + h) * N * 6 - 1), outline=(12, 12, 12), width=2)
    im.paste(rb, (x + 10, y + 20))
    ry = y + 20 + rb.height + 30
    text_block(d, (x, ry), 'For every cell a random chunk orientation is chosen whose edges match the layout '
               '(closed where there is no connection) and the neighbours already placed (same edge type). '
               'If nothing fits, the solver steps back (backtracking). Chunks already used are picked less often.',
               f('r', 22), DIM, 560)
    pfeil(d, 1386, 1434, oben + 300)

    # 5 Bauen
    x, y = panel(d, (1440, oben, W - 80, oben + 1000), 5, 'Build')
    kb = karte.resize((int(karte.width * 0.62), int(karte.height * 0.62)), Image.LANCZOS)
    im.paste(kb, (x + 10, y + 20))
    text_block(d, (x, y + 20 + kb.height + 30), 'Rendered with the Map 01 pipeline: soft terrain transitions, '
               'sunken ponds, forest floor, trees and decoration, lanterns along paths, companion plants at lone '
               'trees, grid snapping and a final overlap / ground check.', f('r', 22), DIM, 800)

    # ------------------------------------------------------------ Fusszeile
    fy = oben + 1040
    kacheln = [('20', 'hand-made chunks'), ('145', 'orientations'), ('~30 000', 'layouts (5 × 4 cells)'),
               ('10¹¹ – 10¹²', 'possible maps')]
    kx = 80
    for zahl, txt in kacheln:
        d.rounded_rectangle((kx, fy, kx + 420, fy + 130), 18, fill=PANEL)
        d.text((kx + 28, fy + 22), zahl, font=f('b', 44), fill=AKZ)
        d.text((kx + 28, fy + 84), txt, font=f('r', 22), fill=DIM)
        kx += 440
    d.rounded_rectangle((kx, fy, W - 80, fy + 130), 18, fill=PANEL)
    d.text((kx + 28, fy + 22), 'Seed = map', font=f('b', 30), fill=TXT)
    d.text((kx + 28, fy + 66), 'python3 tools/zufall_karte.py %d 6 5' % startwert, font=mono(20), fill=AKZ)
    d.text((kx + 28, fy + 96), 'same seed → same map', font=f('r', 20), fill=DIM)

    ziel = os.path.join(ROOT, 'maps', 'zufall', 'system_explained.png')
    im.save(ziel)
    print('->', os.path.relpath(ziel, ROOT), im.size)


if __name__ == '__main__':
    main()
