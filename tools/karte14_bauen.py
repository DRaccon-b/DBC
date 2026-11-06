"""Karte 14 (Spiral Mountain: Summit): Gipfel und Finale der Spiral-Mountain-Reihe. Ringsum dieselbe Bergwand wie
Karte 11-13, Gipfelpflaster, dunkler Schotter, violetter Kristallboden, erhoehte Felsnasen und Portalplatz (Kanten wie
die Plateaus der vorigen Karten), das rote Boss-Feld eine Etage hoeher (Ziegelfront mit Goldband und Pfeilern, Treppe,
Schachbrettrahmen, Spielkarten-Zeichen in den Ecken, grosse Spirale in der Mitte), Schachbrettweg und Treppenplatz.
Anspielungen auf die Herren des Gipfels nur ueber Farben und Motive (Harlekin, Karten, Ritter, Fledermausfluegel).

  python3 tools/karte14_layout.py && python3 tools/karte14_kacheln.py
  python3 tools/karte14_bauen.py && python3 tools/karte14_objekte.py && python3 tools/regeln_v11.py karte14 \\
    && python3 tools/karte14_objekte.py symmetrie && python3 tools/karte14_bauen.py
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte08_bauen as k8
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte14')
BASIS = os.path.join(ROOT, 'assets', 'karte14', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte14')
T = 16
N_FRAMES = 16
H = k4.H
weich, zell_maske = k4.weich, k4.zell_maske
k4.FELS['dunkelberg'] = ['#12141c', '#1a1d28', '#242836', '#303546', '#3e4458', '#50586e', '#666e86']
LIPPE_BERG = ['#3c4050', '#4a4e60', '#585e70', '#686e80', '#7a8092', '#8c92a4']
LIPPE_FELS = ['#40445a', '#4c5066', '#585c72', '#666a80', '#74788e', '#82869c']
FRONT = {2: 32, 5: 44}
GOLD = (214, 170, 72)
SYMBOLE = {   # 7x7, generische Spielkarten-Farben
    'herz': [".##.##.", "#######", "#######", ".#####.", "..###..", "...#...", "......."],
    'pik': ["...#...", "..###..", ".#####.", "#######", "#######", "..#.#..", ".#####."],
    'karo': ["...#...", "..###..", ".#####.", "#######", ".#####.", "..###..", "...#..."],
    'kreuz': ["..###..", "..###..", "##.#.##", "#######", "##.#.##", "...#...", "..###.."],
}


def textur(art, cols, rows):
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    ks = [np.array(Image.open(os.path.join(BASIS, '%s_%d.png' % (art, v))).convert('RGB')) for v in range(5)]
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return t


def kontur(m):
    return m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))


def symbol(a, name, x0, y0, farbe):
    for dy, zeile in enumerate(SYMBOLE[name]):
        for dx, ch in enumerate(zeile):
            if ch == '#':
                a[y0 + dy, x0 + dx] = farbe
                if dy + 1 < 7 and SYMBOLE[name][dy + 1][dx] != '#':
                    a[y0 + dy + 1, x0 + dx] = (90, 60, 20)


def spirale(a, cx, cy, r, frame):
    """Boss-Feld: grosse Spirale des Spiral Mountain - goldener Doppelring, Spielkarten-Zeichen dazwischen, drei
    violett-goldene Spiralarme drehen sich langsam, die Mitte pulsiert."""
    f = frame or 0
    Hh, W = a.shape[:2]
    yy, xx = np.mgrid[0:Hh, 0:W]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    a[d <= r] = (a[d <= r] * 0.62).astype(np.uint8)
    puls = 0.6 + 0.4 * math.sin(2 * math.pi * f / N_FRAMES)
    for rr, b in ((r - 1.5, 1.0), (r * 0.84, 0.8)):
        m = np.abs(d - rr) <= b
        a[m] = np.clip(np.array(GOLD, np.float32) * (0.75 + 0.25 * puls), 0, 255).astype(np.uint8)
    for k_, name in enumerate(('herz', 'pik', 'karo', 'kreuz') * 2):
        w = 2 * math.pi * k_ / 8 + math.pi / 8
        symbol(a, name, int(cx + math.cos(w) * r * 0.92) - 3, int(cy + math.sin(w) * r * 0.92) - 3,
               (200, 40, 56) if name in ('herz', 'karo') else (30, 24, 40))
    dreh = 2 * math.pi * f / N_FRAMES / 3
    for arm in range(3):
        for i in range(220):
            t = i / 220
            w = dreh + arm * 2 * math.pi / 3 + t * 4.2
            rr = t * r * 0.78
            X, Y = int(round(cx + math.cos(w) * rr)), int(round(cy + math.sin(w) * rr))
            c = (170, 110, 230) if (i // 12) % 2 else GOLD
            for dx, dy in ((0, 0), (1, 0), (0, 1)):
                a[Y + dy, X + dx] = tuple(int(v * (0.7 + 0.3 * puls)) for v in c)
    kern = d <= r * 0.1
    a[kern] = np.clip(np.array([230, 200, 255], np.float32) * (0.6 + 0.4 * puls), 0, 255).astype(np.uint8)


def bossfeld_front(a, feld, tr):
    """Suedfront des Boss-Felds (32 px): rote und dunkle Ziegel, oben ein Goldband, Pfeiler im festen Rhythmus,
    unten Kontaktschatten; mittig die Steintreppe."""
    Hh, W = feld.shape
    front = np.zeros_like(feld)
    F = 32
    sued = feld & ~np.roll(feld, -1, 0)
    tx0, tx1 = tr[0] * T, (tr[1] + 1) * T
    for y, x in zip(*np.nonzero(sued)):
        for d in range(F + 3):
            Y = y + 1 + d
            if Y >= Hh or feld[Y, x]:
                break
            if d >= F:
                a[Y, x] = (a[Y, x] * (0.6 if d == F else 0.8)).astype(np.uint8)
                continue
            front[Y, x] = True
            if tx0 <= x < tx1:
                continue
            reihe = d // 4
            xo = (x + (4 if reihe % 2 else 0)) % 8
            c = np.array((110, 36, 44) if (x // 8 + reihe) % 3 else (70, 62, 80), np.float32)
            if d % 4 == 3 or xo == 7:
                c = np.array((26, 18, 26), np.float32)
            if d < 3:
                c = np.array(GOLD, np.float32) * (1.0 if d == 0 else 0.75)
            if (x % 64) < 5 and d >= 3:                          # Pfeiler
                c = np.array((92, 92, 108), np.float32) if (x % 64) < 4 else np.array((30, 30, 40), np.float32)
            c = c * (1 - 0.3 * d / F)
            a[Y, x] = np.clip(c, 0, 255).astype(np.uint8)
    y0 = (tr[3] + 1) * T
    for d in range(F + 2):
        Y = y0 + d
        for x in range(tx0 - 3, tx1 + 3):
            if x < tx0 or x >= tx1:
                a[Y, x] = H('#1e1c26') if x in (tx0 - 3, tx1 + 2) else H('#5a5868')
            else:
                st = d % 6
                a[Y, x] = H('#8a8898') if st == 0 else (H('#626070') if st < 4 else H('#26242e'))
        front[Y, tx0 - 3:tx1 + 3] = False
    return front



def treiben(sp, frame, o):
    """Wolken am Gipfelrand treiben langsam hin und her (die ganze Wolke, 2 px)."""
    d = int(round(2 * math.sin(2 * math.pi * frame / N_FRAMES + o.get('x', 0) * 0.02)))
    out = Image.new('RGBA', sp.size)
    out.paste(sp, (d, 0))
    return out


k4.TEILANIM['treiben'] = treiben


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    cls = lay['klassen']
    hoehe = np.array([[int(c) for c in r] for r in lay['hoehe']])
    Wp, Hp = cols * T, rows * T
    a = textur('d', cols, rows)
    for art, bl, rausch, seed in (('k', 4.0, 0.5, 3), ('p', 3.5, 0.45, 9)):
        roh = zell_maske(cls, art, cols, rows)
        m = weich(roh, bl, rausch, seed)
        a[m] = textur(art, cols, rows)[m]
        k4.dunkeln(a, weich(roh, bl, rausch, seed, 0.36) & ~m, 0.84)
    for art in 'czbf':
        m = zell_maske(cls, art, cols, rows) > 0
        a[m] = textur(art, cols, rows)[m]
    platz = zell_maske(cls, 'b', cols, rows) > 0
    a[kontur(platz)] = H('#a88a4a')                               # Goldkante um den Treppenplatz
    weg = zell_maske(cls, 'z', cols, rows) > 0
    # --- Ebenen: Felsnasen und Portalplatz (2), Boss-Feld (2, eigene Front), Berg (5)
    em = {}
    em[5] = weich(k8.stufe(hoehe, 5, cols, rows), 5, 0.3, 37)
    felsn = weich(zell_maske(cls, 'v', cols, rows), 3, 0.25, 11) & ~em[5]
    a[felsn] = textur('v', cols, rows)[felsn]
    portal = zell_maske(cls, 'f', cols, rows) > 0
    feld = (zell_maske(cls, 'cz', cols, rows) > 0) & (k8.stufe(hoehe, 2, cols, rows) > 0)
    a[em[5]] = (textur('r', cols, rows)[em[5]] * np.array([0.56, 0.58, 0.66])).astype(np.uint8)
    # Boss-Feld: Goldkante, Pfosten in den Ecken des Rahmens, Kartenzeichen, Spirale
    a[kontur(feld)] = H('#b08a40')
    for (sx, sy, nm) in ((35, 13, 'herz'), (45, 13, 'pik'), (35, 22, 'karo'), (45, 22, 'kreuz'),
                         (31, 9, 'pik'), (49, 9, 'herz'), (31, 26, 'kreuz'), (49, 26, 'karo')):
        symbol(a, nm, sx * T + 4, sy * T + 4, (210, 170, 70))
    b = lay['boss']
    spirale(a, b[0] * T, b[1] * T, 4.6 * T, frame)
    treppen_info = []
    frei = np.zeros((Hp, Wp), bool)
    for (x0, x1, e, yb_kachel) in lay.get('treppen_sued', [])[1:]:
        px0, px1 = x0 * T + 1, (x1 + 1) * T - 1
        yb = (yb_kachel + 1) * T - 1
        frei[yb - 14:yb + FRONT[e] + 8, px0 - 6:px1 + 6] = True
        treppen_info.append((px0, px1, yb, FRONT[e], e))
    waende = np.zeros((Hp, Wp), bool)
    waende |= k4.hoehenkanten(a, felsn | portal | em[5], 'dunkelberg', FRONT[2], 12, LIPPE_FELS, frei | em[5], 31, berg=False)
    waende |= k4.hoehenkanten(a, em[5], 'dunkelberg', FRONT[5], 12, LIPPE_BERG, frei, 35, berg=False)
    front_b = bossfeld_front(a, feld, lay['treppen_sued'][0])
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[felsn | portal | feld] = 2
    lvl[em[5]] = 5
    lvl[waende] = 9
    lvl[front_b] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
    img = Image.fromarray(a).convert('RGBA')
    alt_S = bauwerke.S
    bauwerke.S = [H(c) + (255,) for c in k4.FELS['dunkelberg']]
    for (px0, px1, ye, f, e) in treppen_info:
        bauwerke.zeichne_treppe(img, px0 - 6, px1 + 6, ye + 2, ye + f + 2)
        for y in range(ye + 1, ye + f + 3):
            for x in range(px0 - 6, px1 + 6):
                lvl[min(Hp - 1, y), x] = 9
    bauwerke.S = alt_S
    a = np.array(img.convert('RGB'))
    for tp in lay.get('teleporter', []):
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: (0 if o.get('an_wand') else 1, o['y'] + o['fuss']))
        cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
        k8.schatten_ebene(img, [o for o in objs if not o.get('an_wand')], cache, lvl)
        vor_objekten = np.array(img)
        k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
        k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
        k8.verdeckung(img, [o for o in objs if not o.get('an_wand')], cache, lvl, vor_objekten)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 14 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
