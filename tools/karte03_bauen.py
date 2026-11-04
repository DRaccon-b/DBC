"""Baut Karte 03 (Server Desert).

  python3 tools/karte03_kacheln.py   # neue Grundkacheln (Weg, Kies, Platz, Lehm, Duene)
  python3 tools/karte03_bauen.py     # Boden + Bauwerke (+ Objekte, falls platziert)

Wiederverwendet: Sand/Gras/Wasser-Kacheln und die Wang-Sets gras_weg, wasser_sand, wasser_gras aus
Karte 01 (inkl. Wasseranimation), Bruecke aus tools/bauwerke.py, Bodenfuss/Schatten-Regeln aus Karte 02.
Neu: Weg/Kies/Platz/Lehm/Duene (tools/karte03_kacheln.py), erhoehte Sandsteinmauern der Ruinen-Arena
und der Ziegelring um den Garten, Duenenrand, Teleporter, Datenkabel.
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import karte_bauen as kb
import industrie as ind
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte03')
BASIS1 = os.path.join(ROOT, 'assets', 'basis')
BASIS3 = os.path.join(ROOT, 'assets', 'karte03', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte03')
T = 16
N_FRAMES = kb.N_FRAMES
CODE = {'sand': 's', 'gras': 'g', 'wasser': 'x', 'weg': 'w', 'kies': 'k', 'platz': 'p', 'lehm': 'l', 'duene': 'd'}
SANDSTEIN = ind.pal('#6a4a2c', '#8a6640', '#a88250', '#c4a066', '#dcbc80', '#ecd49c', '#f8e8c0')
ZIEGEL = ind.pal('#3e2218', '#5a3020', '#7a4430', '#95553a', '#ae6a48', '#c48460', '#d89a74')


def r(n):
    return Image.open(n).convert('RGBA')


def zellen_der_form(z, cols, rows):
    if 'r' in z:
        x0, y0, x1, y1 = z['r']
        return [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]
    cx, cy, rx, ry = z['e']
    return [(x, y) for y in range(rows) for x in range(cols)
            if ((x + 0.5 - cx - 0.5) / rx) ** 2 + ((y + 0.5 - cy - 0.5) / ry) ** 2 <= 1]


def mauer_zellen(pfad, dicke=2):
    zellen = set()
    for (ax, ay), (bx, by) in zip(pfad, pfad[1:]):
        n = max(abs(bx - ax), abs(by - ay), 1)
        for i in range(n + 1):
            x = round(ax + (bx - ax) * i / n); y = round(ay + (by - ay) * i / n)
            for dx in range(dicke):
                for dy in range(dicke):
                    zellen.add((x + dx, y + dy))
    return zellen


def mauer_zeichnen(L, zellen, pal, hoehe, ziegel=True, rnd=None):
    """Erhoehte Mauer aus Kacheln: Front (Ziegelverband) an jeder Suedkante, Kappe um `hoehe` nach oben
    versetzt, Seitenkanten dunkel; Schatten nach rechts unten auf den Boden."""
    rnd = rnd or random.Random(3)
    for (x, y) in sorted(zellen, key=lambda c: c[1]):
        X, Y = x * T, y * T
        # Schatten (Licht oben links)
        if (x + 1, y) not in zellen:
            for yy in range(Y - hoehe + 4, Y + T + 2):
                for d, f in ((0, 0.62), (1, 0.75), (2, 0.88)):
                    L.neutral(X + T + d, yy, f)
        if (x, y + 1) not in zellen:
            for xx in range(X + 3, X + T + 3):
                for d, f in ((0, 0.6), (1, 0.74), (2, 0.88)):
                    L.neutral(xx, Y + T + d, f)
    for (x, y) in sorted(zellen, key=lambda c: c[1]):
        X, Y = x * T, y * T
        if (x, y + 1) not in zellen:                        # Front
            for yy in range(Y + T - hoehe, Y + T):
                k = yy - (Y + T - hoehe)
                for xx in range(X, X + T):
                    zeile = k // 4
                    vers = 4 if zeile % 2 else 0
                    c = pal[2]
                    if ziegel and (k % 4 == 3 or (xx + vers) % 8 == 7):
                        c = pal[1]
                    elif ziegel and k % 4 == 0:
                        c = pal[3]
                    if k >= hoehe - 2:
                        c = pal[0]
                    L.p(xx, yy, c)
        for yy in range(Y - hoehe, Y + T - hoehe):          # Kappe
            k = yy - (Y - hoehe)
            for xx in range(X, X + T):
                c = pal[4] if (xx + yy) % 7 else pal[3]
                if ziegel and ((k % 8 == 7) or ((xx + (4 if (k // 8) % 2 else 0)) % 16 == 15)):
                    c = pal[3]
                if (x, y - 1) not in zellen and k < 2:
                    c = pal[6] if k == 0 else pal[5]
                if (x - 1, y) not in zellen and xx == X:
                    c = pal[5]
                if (x + 1, y) not in zellen and xx == X + T - 1:
                    c = pal[1]
                L.p(xx, yy, c)
        if (x - 1, y) not in zellen or (x + 1, y) not in zellen:      # Seitenkanten der Front
            if (x, y + 1) not in zellen:
                for yy in range(Y + T - hoehe, Y + T):
                    if (x - 1, y) not in zellen:
                        L.p(X, yy, pal[3])
                    if (x + 1, y) not in zellen:
                        L.p(X + T - 1, yy, pal[0])
        if rnd.random() < 0.25:                             # Verwitterung auf der Kappe
            L.p(X + rnd.randint(2, 13), Y - hoehe + rnd.randint(2, 13), pal[2])


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    cls = [['s'] * cols for _ in range(rows)]
    for z in lay['boden']:
        for (x, y) in zellen_der_form(z, cols, rows):
            if 0 <= x < cols and 0 <= y < rows:
                cls[y][x] = CODE[z['art']]

    # --- 1. Basis: Sand/Gras/Wasser mit Wang-Uebergaengen aus Karte 01
    basis = {k: [r(os.path.join(BASIS1, '%s_%d.png' % (n, i))) for i in range(5)]
             for k, n in (('s', 'sand'), ('g', 'gras'), ('x', 'wasser'))}
    neu = {k: [r(os.path.join(BASIS3, '%s_%d.png' % (n, i))) for i in range(5)]
           for k, n in (('w', 'weg'), ('k', 'kies'), ('p', 'platz'), ('l', 'lehm'), ('d', 'duene'))}
    sets = {n: kb.lade_set(n) for n in ('gras_weg', 'wasser_sand', 'wasser_gras')}
    PAARE = {frozenset('gs'): ('gras_weg', 's', 'g'), frozenset('gx'): ('wasser_gras', 'x', 'g'),
             frozenset('sx'): ('wasser_sand', 'x', 's')}
    grund = lambda k: k if k in 'gx' else 's'
    def zg(x, y):
        return grund(cls[min(max(y, 0), rows - 1)][min(max(x, 0), cols - 1)])
    vk = [[None] * (cols + 1) for _ in range(rows + 1)]
    for vy in range(rows + 1):
        for vx in range(cols + 1):
            c = Counter(zg(vx + dx, vy + dy) for dx in (-1, 0) for dy in (-1, 0))
            vk[vy][vx] = next((k for k in 'xsg' if c[k] >= 2), 's')
    for _ in range(4):                                     # keine Kachel mit drei Arten: Gras weicht
        for y in range(rows):
            for x in range(cols):
                ecken = [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]
                if len({vk[b][a] for a, b in ecken}) == 3:
                    for a, b in ecken:
                        if vk[b][a] == 'g':
                            vk[b][a] = 's'
    img = Image.new('RGBA', (cols * T, rows * T))
    wasserzellen = []
    for y in range(rows):
        for x in range(cols):
            e = {vk[y][x], vk[y][x + 1], vk[y + 1][x], vk[y + 1][x + 1]}
            if len(e) == 1:
                k = e.pop()
                i = kb.variante(x, y)
                kachel, beschr = basis[k][i], 'basis:%s_%d' % ({'s': 'sand', 'g': 'gras', 'x': 'wasser'}[k], i)
            else:
                name, lo, up = PAARE[frozenset(e)]
                pat = [[255] * 4]
                for vy in (y, y + 1):
                    pat.append([255] + [0 if vk[vy][vx] == lo else 1 for vx in (x, x + 1)] + [255])
                pat.append([255] * 4)
                t, _ = kb.waehle(sets[name]['tiles'], pat)
                kachel, beschr = t['img'], '%s:%s' % (name, t['name'])
            if frame is not None and ('wasser' in beschr):
                kachel = kb.wasser_frame(kachel, beschr, 'W' if x < 6 else 'D', y, x, frame,
                                         {'w': basis['x'], 'm': basis['x']})
                wasserzellen.append((x, y))
            img.paste(kachel, (x * T, y * T))
    L = ind.Leinwand(img)

    # --- 2. Boden-Overlays auf Sand: Weg, Kies, Platz, Lehm, Duene
    def maske_von(art, blur=3.0, rausch=0.3, seed=1):
        m = Image.new('L', img.size, 0)
        d = ImageDraw.Draw(m)
        for y in range(rows):
            for x in range(cols):
                if cls[y][x] == art:
                    d.rectangle((x * T, y * T, x * T + T - 1, y * T + T - 1), fill=255)
        a = np.array(m.filter(ImageFilter.GaussianBlur(blur))).astype(np.float32) / 255
        h, w = a.shape
        n = np.random.RandomState(seed).rand(h // 4 + 2, w // 4 + 2)
        n = np.array(Image.fromarray((n * 255).astype(np.uint8)).resize((w + 8, h + 8), Image.BICUBIC))[:h, :w] / 255
        return a + (n - 0.5) * rausch

    def textur(art):
        t = np.zeros((rows * T, cols * T, 4), np.uint8)
        for y in range(rows):
            for x in range(cols):
                t[y * T:(y + 1) * T, x * T:(x + 1) * T] = np.array(neu[art][kb.variante(x, y)])
        return t

    a_img = np.array(img)
    for art, blur, rausch, rand in (('w', 4.0, 0.22, 'weich'), ('k', 2.2, 0.35, 'steine')):
        f = maske_von(art, blur, rausch, seed=7 if art == 'w' else 9)
        tex = textur(art)
        innen = f > 0.5
        a_img[innen] = tex[innen]
        saum = (f > 0.36) & ~innen
        if rand == 'weich':                                # Weg: weicher Uebergang, Sand dunkler
            a_img[saum, :3] = (a_img[saum, :3].astype(np.float32) * 0.94).astype(np.uint8)
        else:                                              # Kies: einzelne Steine im Rand, Schatten
            ys, xs = np.nonzero(saum)
            rs = np.random.RandomState(5)
            for yy, xx in zip(ys, xs):
                if rs.rand() < 0.18:
                    a_img[yy, xx, :3] = tex[yy, xx, :3]
                else:
                    a_img[yy, xx, :3] = (a_img[yy, xx, :3] * 0.93).astype(np.uint8)
    img.paste(Image.fromarray(a_img))
    L = ind.Leinwand(img)
    # Platz: harte Kante mit Bordstein und Schatten; Lehm: leicht erhabene Scholle mit Front
    for y in range(rows):
        for x in range(cols):
            k = cls[y][x]
            if k in 'pld':
                img.paste(neu[k][kb.variante(x, y)], (x * T, y * T))
    for y in range(rows):
        for x in range(cols):
            k = cls[y][x]
            if k not in 'pld':
                continue
            X, Y = x * T, y * T
            nb = lambda dx, dy: cls[y + dy][x + dx] if 0 <= x + dx < cols and 0 <= y + dy < rows else k
            if k == 'p':
                pal_ = (ind.rgb('#3a3e52'), ind.rgb('#b0b8cc'))
                for i in range(T):
                    if nb(0, -1) != 'p': L.p(X + i, Y, pal_[1]); L.p(X + i, Y + 1, pal_[0])
                    if nb(0, 1) != 'p': L.p(X + i, Y + T - 1, pal_[0]); L.neutral(X + i, Y + T, 0.75)
                    if nb(-1, 0) != 'p': L.p(X, Y + i, pal_[1])
                    if nb(1, 0) != 'p': L.p(X + T - 1, Y + i, pal_[0]); L.neutral(X + T, Y + i, 0.78)
            elif k == 'l':
                for i in range(T):
                    if nb(0, -1) != 'l': L.p(X + i, Y, ind.rgb('#c07a4e'))
                    if nb(-1, 0) != 'l': L.p(X, Y + i, ind.rgb('#a8643e'))
                    if nb(1, 0) != 'l': L.p(X + T - 1, Y + i, ind.rgb('#4a2a1e'))
                    if nb(0, 1) != 'l':                    # Front 4 px + Schatten
                        for d, c in ((0, '#6e3c28'), (1, '#5a3020'), (2, '#4a2a1e'), (3, '#3a2018')):
                            L.p(X + i, Y + T - 4 + d, ind.rgb(c))
                        L.neutral(X + i + 2, Y + T, 0.7); L.neutral(X + i + 2, Y + T + 1, 0.85)
            elif k == 'd':
                rs = random.Random(x * 31 + y)
                if nb(0, 1) not in 'd':                    # Duene ueber Sand: Hang nach Sueden
                    for i in range(T):
                        welle = int(2 * math.sin((X + i) / 9.0) + 2 * math.sin((X + i) / 23.0))
                        for d in range(10):
                            yy = Y + T - 3 + welle + d
                            if d < 2:
                                L.p(X + i, yy, ind.rgb('#d8bc84'))
                            elif d < 7:
                                L.p(X + i, yy, ind.rgb('#e6cc96') if d < 4 else ind.rgb('#d6b47c'))
                            else:
                                L.neutral(X + i, yy, 0.86 + d * 0.012)
                if nb(0, -1) not in 'd':                   # Duene unter Sand: Kamm mit Lichtkante
                    for i in range(T):
                        welle = int(2 * math.sin((X + i) / 8.0 + 1) + 1.5 * math.sin((X + i) / 19.0))
                        for d in range(-3, 3):
                            yy = Y + welle + d
                            L.p(X + i, yy, ind.rgb('#fff8e6') if d == -3 else ind.rgb('#f4e4bc') if d < 0 else ind.rgb('#e2c890'))
                for (nx, ny, sx) in ((-1, 0, 0), (1, 0, T - 1)):
                    if nb(nx, ny) not in 'd':
                        for j in range(T):
                            welle = int(2 * math.sin((Y + j) / 7.0))
                            xx = X + sx + welle * (1 if nx > 0 else -1)
                            L.p(xx, Y + j, ind.rgb('#e2c890'))
                            L.p(xx + (1 if nx < 0 else -1), Y + j, ind.rgb('#fff8e6'))

    # Sandrippel und Steinchen auf freiem Sand
    rs = random.Random(21)
    for y in range(rows):
        for x in range(cols):
            if cls[y][x] != 's' or vk[y][x] != 's':
                continue
            r_ = rs.random()
            X, Y = x * T + rs.randint(2, 12), y * T + rs.randint(2, 12)
            if r_ < 0.08:
                for i in range(rs.randint(3, 6)):
                    L.p(X + i, Y + (i // 3), ind.rgb('#c9a46e')); L.p(X + i, Y + 1 + (i // 3), ind.rgb('#f2dba6'))
            elif r_ < 0.11:
                L.p(X, Y, ind.rgb('#9c7448')); L.p(X + 1, Y, ind.rgb('#c09a62')); L.neutral(X + 1, Y + 1, 0.8)

    # --- 3. Kabelnetz (Datenkabel am Boden, lila), Steg, Teleporter
    lila = (ind.rgb('#2a2050'), ind.rgb('#4a3a8a'), ind.rgb('#7a6ac8'))
    knoten = set()
    for (a, b) in lay.get('kabel', []):
        (ax, ay), (bx, by) = a, b
        knoten.update({(ax, ay), (bx, by)})
        if ax == bx:
            for yy in range(min(ay, by) * T + 8, max(ay, by) * T + 9):
                L.p(ax * T + 7, yy, lila[1]); L.p(ax * T + 8, yy, lila[0]); L.p(ax * T + 6, yy, lila[2])
                L.neutral(ax * T + 9, yy + 1, 0.8)
        else:
            for xx in range(min(ax, bx) * T + 8, max(ax, bx) * T + 9):
                L.p(xx, ay * T + 7, lila[2]); L.p(xx, ay * T + 8, lila[1]); L.p(xx, ay * T + 9, lila[0])
                L.neutral(xx + 1, ay * T + 10, 0.8)
    for (kx, ky) in knoten:                                # Verteilerdosen
        X, Y = kx * T + 4, ky * T + 4
        L.rect(X, Y, X + 8, Y + 8, ind.rgb('#3e4850')); L.rect(X, Y, X + 8, Y + 1, ind.rgb('#8e9ba3'))
        L.rect(X, Y + 7, X + 8, Y + 8, ind.rgb('#1c2128')); L.p(X + 5, Y + 3, ind.rgb('#7ff0f5'))
    st = lay.get('steg')
    if st:
        bauwerke.zeichne_bruecke(img, st['x'] * T, (st['x'] + st['laenge']) * T, st['y'] * T,
                                 (st['y'] + st['breite']) * T - 2, frame=frame or 0)
        L = ind.Leinwand(img)
    puls = 0.5 + 0.5 * math.sin(2 * math.pi * (frame or 0) / N_FRAMES)
    for (tx, ty) in lay.get('teleporter', []):
        for i in range(2):
            for j in range(4):
                cx, cy = (tx + i) * T + 8, (ty + j) * T + 8
                for yy in range(-6, 7):
                    for xx in range(-7, 8):
                        d = (xx / 7) ** 2 + (yy / 6) ** 2
                        if d <= 1:
                            if d > 0.7:
                                c = ind.rgb('#3e4850') if yy > 0 else ind.rgb('#8e9ba3')
                            elif d > 0.35:
                                c = ind.rgb('#2fc7d8') if puls > 0.4 or d < 0.5 else ind.rgb('#2a8aa0')
                            else:
                                c = ind.rgb('#e6ffff') if puls > 0.6 else ind.rgb('#7ff0f5')
                            L.p(cx + xx, cy + yy, c)

    # --- 4. Erhoehte Mauern: Ruinen-Arena (Sandstein) und Garten-Ring (Ziegel)
    ar = lay.get('arena', {})
    arena = mauer_zellen(ar.get('pfad', [])) | mauer_zellen(ar.get('pfad2', []))
    if 'e' in ar:
        cx, cy, rx, ry = ar['e']
        dk = ar.get('dicke', 2)
        for y in range(rows):
            for x in range(cols):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                di = ((x - cx) / (rx - dk)) ** 2 + ((y - cy) / (ry - dk)) ** 2
                if d <= 1 and di > 1:
                    oo = ar.get('ost_offen')
                    if oo and x > cx + 3 and oo[0] <= y <= oo[1]:
                        continue
                    arena.add((x, y))
    if 'tor' in ar:
        x0, y0, x1, y1 = ar['tor']
        arena = {c for c in arena if not (x0 <= c[0] <= x1 and y0 <= c[1] <= y1)}
    mauer_zeichnen(L, arena, SANDSTEIN, 24)
    ga = lay.get('garten')
    garten = set()
    if ga:
        cx, cy, rx, ry = ga['e']
        for y in range(rows):
            for x in range(cols):
                d = ((x + 0.5 - cx - 0.5) / rx) ** 2 + ((y + 0.5 - cy - 0.5) / ry) ** 2
                dinnen = ((x + 0.5 - cx - 0.5) / (rx - ga['dicke'])) ** 2 + ((y + 0.5 - cy - 0.5) / (ry - ga['dicke'])) ** 2
                if d <= 1 and dinnen > 1 and not (ga['oeffnung'][0] <= x <= ga['oeffnung'][1] and y > cy):
                    garten.add((x, y))
        mauer_zeichnen(L, garten, ZIEGEL, 14)
    if speichern:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))

    # Bodenmaske fuer Schatten: nicht auf Mauerkappen/-fronten, nicht auf Duenen
    boden = np.ones((rows * T, cols * T), np.float32)
    for (x, y) in arena:
        boden[max(0, y * T - 24):(y + 1) * T, x * T:(x + 1) * T] = 0
    for (x, y) in garten:
        boden[max(0, y * T - 14):(y + 1) * T, x * T:(x + 1) * T] = 0

    # --- 5. Objekte
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = []
    if os.path.exists(pf):
        objs = sorted(json.load(open(pf)), key=lambda o: (o.get('ebene', 1), o['y'] + o.get('fuss', 0)))
        cache = {}
        for o in objs:
            if o['datei'] not in cache:
                cache[o['datei']] = Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA')
        objekte_zeichnen(img, objs, cache, boden, frame)
    if frame is not None:
        animieren(img, objs, frame)
        return img
    if speichern:
        img.save(os.path.join(KARTE, 'terrain.png'))
        json.dump({'tile_size': T, 'cols': cols, 'rows': rows, 'klassen': [''.join(r_) for r_ in cls],
                   'arena': sorted(arena), 'garten': sorted(garten)},
                  open(os.path.join(KARTE, 'tilemap.json'), 'w'))
    print('Karte 03 %dx%d gebaut' % (cols, rows))
    return img


def objekte_zeichnen(img, objs, cache, boden, frame):
    """Kantenintegration (Sand angeweht, Steinchen), Fussschatten + Schlagschatten (nur auf Boden),
    dann die Sprites (mit Wind fuer Palmen)."""
    L = ind.Leinwand(img)
    rk = random.Random(11)
    for o in objs:
        if o.get('ohne_fuss'):
            continue
        a = np.array(cache[o['datei']].getchannel('A')) >= 200
        zeilen = np.nonzero(a.any(axis=1))[0]
        if len(zeilen) == 0:
            continue
        for xi in np.nonzero(a.any(axis=0))[0]:
            yu = int(np.nonzero(a[:, xi])[0].max())
            if yu < zeilen.max() - 4:
                continue
            X, Y = o['x'] + int(xi), o['y'] + yu
            for d, f in ((1, 0.7), (2, 0.84)):
                L.neutral(X, Y + d, f, waerme=4)
            if rk.random() < 0.25:                         # angewehter Sand vor der Kante
                L.p(X + rk.randint(-1, 1), Y + rk.randint(0, 2), ind.rgb('#e8cf98') if rk.random() < 0.5 else ind.rgb('#d8b87e'))
    sm = np.zeros(boden.shape, np.float32)
    ellip = Image.new('L', img.size, 0)
    ed = ImageDraw.Draw(ellip)
    for o in objs:
        sp = cache[o['datei']]
        a = np.array(sp.getchannel('A')) >= 200
        zeilen = np.nonzero(a.any(axis=1))[0]
        if len(zeilen) < 4 or o.get('ohne_schatten'):
            continue
        fuss_y = o['y'] + zeilen.max()
        cx = o['x'] + sp.width // 2
        w = int(sp.width * 0.6)
        ed.ellipse((cx - w // 2, fuss_y - 3, cx + w // 2, fuss_y + 3), fill=90)
        for zi in zeilen:
            k = zeilen.max() - zi
            ty = int(fuss_y - 2 + k * 0.42 * 0.55)
            dx = int(3 + k * 0.42)
            if 0 <= ty < sm.shape[0]:
                xs = np.nonzero(a[zi])[0] + o['x'] + dx
                xs = xs[(xs >= 0) & (xs < sm.shape[1])]
                sm[ty, xs] = 1.0
    sch = np.maximum(np.array(ellip.filter(ImageFilter.GaussianBlur(1.2))),
                     np.array(Image.fromarray((sm * 72).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))))
    sch = (sch.astype(np.float32) * boden).astype(np.uint8)
    dunkel = Image.new('RGBA', img.size, (70, 40, 30, 255))
    dunkel.putalpha(Image.fromarray(sch))
    img.alpha_composite(dunkel)
    for o in objs:
        sp = cache[o['datei']]
        if frame is not None and o.get('anim') == 'wehen':
            sp = kb.wehen(sp, kb.wind(frame, o['x']))
        img.alpha_composite(sp, (o['x'], o['y']))


FEUER = [(0xc8, 0x3a, 0x1e), (0xe8, 0x70, 0x2a), (0xf5, 0xb0, 0x42), (0xff, 0xf2, 0xa0)]


def animieren(img, objs, frame):
    """Feuer (Fackeln, Lagerfeuer) flackert mit Lichtschein, Kristall/Leuchten pulsieren, Antennen
    blinken, Musiknoten steigen von der Buehne auf."""
    a = np.array(img)
    puls = 0.5 + 0.5 * math.sin(frame / N_FRAMES * 2 * math.pi)
    glut = Image.new('RGBA', img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glut)
    for i, o in enumerate(objs):
        anim = o.get('anim')
        if anim not in ('feuer', 'leuchten', 'blinken', 'musik'):
            continue
        sp = Image.open(os.path.join(OBJ, o['datei']))
        x0, y0 = max(0, o['x']), max(0, o['y'])
        x1, y1 = min(a.shape[1], o['x'] + sp.width), min(a.shape[0], o['y'] + sp.height)
        reg = a[y0:y1, x0:x1]
        rr = reg[..., :3].astype(np.int16)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        if anim == 'feuer':
            m_all = np.zeros(rr.shape[:2], bool)
            stufe = (((yy * 2 + xx * 3 + frame * 5) % 7) > 3).astype(int) * 2 - 1
            for k, c in enumerate(FEUER):
                m = (rr == c).all(axis=2)
                m_all |= m
                ziel = np.clip(k + stufe, 0, 3)
                for j, cz in enumerate(FEUER):
                    reg[m & (ziel == j), :3] = cz
            ys, xs = np.nonzero(m_all)
            if len(xs):
                fx, fy = x0 + xs.mean(), y0 + ys.mean()
                fl = 0.75 + 0.25 * math.sin(frame * 2.3 + i)
                for rad, al in ((18, 30), (11, 44), (6, 60)):
                    gd.ellipse((fx - rad, fy - rad * 0.6, fx + rad, fy + rad * 0.6), fill=(255, 160, 70, int(al * fl)))
        elif anim == 'leuchten':
            m = ((rr[..., 2] > 180) & (rr[..., 1] > 150) & (rr[..., 0] < 160))
            reg[m, :3] = np.clip(reg[m, :3] * (0.75 + 0.45 * puls), 0, 255).astype(np.uint8)
        elif anim == 'blinken':
            m = ((rr[..., 0] > 170) & (rr[..., 1] < 120)) | ((rr[..., 2] > 200) & (rr[..., 0] < 140))
            if (frame + i * 3) % 8 < 3:
                reg[m, :3] = (reg[m, :3] * 0.45).astype(np.uint8)
        a[y0:y1, x0:x1] = reg
        if anim == 'musik':
            rnd = random.Random(i)
            for k in range(4):
                t = ((frame + k * 4) % 16) / 16
                nx = o['x'] + sp.width * (0.2 + 0.6 * ((k * 37 + i) % 10) / 10) + math.sin(t * 6 + k) * 3
                ny = o['y'] + 6 - t * 30
                farbe = (122, 106, 200, int(255 * (1 - t)))
                gd.rectangle((nx, ny, nx + 1, ny + 3), fill=farbe)
                gd.rectangle((nx - 2, ny + 3, nx + 1, ny + 4), fill=farbe)
                gd.point((nx + 2, ny), fill=farbe)
    img.paste(Image.fromarray(a))
    img.alpha_composite(glut)


def main():
    bauen()


if __name__ == '__main__':
    main()
