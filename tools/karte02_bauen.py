"""Baut Karte 02 (Factorial Town).

  python3 tools/karte02_kacheln.py     # Grundkacheln (einmalig / nach Aenderungen)
  python3 tools/karte02_bauen.py

Eingaben: maps/karte02/layout.json (Zonen, Gebaeude, Schienen, Rohre, Markierungen),
          assets/karte02/basis/*.png, assets/tilesets/pixellab/k2_beton_gras.json,
          assets/objekte/karte02/platzierung.json (optional, von karte02_objekte.py)
Ausgaben: maps/karte02/terrain_basis.png (ohne Objekte), terrain.png, tilemap.json

Aufbau wie Karte 01: Boden aus handgezeichneten Kacheln (Beton in 2x2-Platten), Gras-Uebergaenge
als PixelLab-Wang-Set mit den Grundkacheln als Referenz, alles Gebaute prozedural (tools/industrie.py),
Objekte aus dem PixelLab-Objekt-Manager mit Bodenfuss, Schatten und Pixel-Kollision.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
from PIL import Image, ImageChops, ImageDraw, ImageFilter
import industrie as ind
import karte_bauen as kb

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte02')
BASIS = os.path.join(ROOT, 'assets', 'karte02', 'basis')
GRAS = os.path.join(ROOT, 'assets', 'basis')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte02')
T = 16
KLASSE = {'beton': 'b', 'asphalt': 'a', 'gehweg': 'w', 'platz': 'p', 'platz_hell': 'h', 'metall': 'm', 'gras': 'g',
          'schlamm': 's'}
N_FRAMES = kb.N_FRAMES


def lade(n):
    return Image.open(os.path.join(BASIS, n + '.png')).convert('RGBA')


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    cls = [['b'] * cols for _ in range(rows)]
    for z in lay['boden']:
        x0, y0, x1, y1 = z['r']
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                cls[y][x] = KLASSE[z['art']]

    beton = {(px, py, v): lade('beton_%d%d_%d' % (px, py, v)) for px in (0, 1) for py in (0, 1) for v in range(3)}
    andere = {k: [lade('%s_%d' % (n, v)) for v in range(5)] for n, k in
              (('asphalt', 'a'), ('gehweg', 'w'), ('platz', 'p'), ('platz_hell', 'h'), ('metall', 'm'))}
    gras = [Image.open(os.path.join(GRAS, 'gras_%d.png' % v)).convert('RGBA') for v in range(5)]
    bg = kb.lade_set('k2_beton_gras')
    beton_ref = lade('beton_11_0')

    def kachel(x, y):
        k = cls[y][x]
        if k in 'bs':
            return beton[(x % 2, y % 2, kb.variante(x, y, 3))]
        if k == 'g':
            return gras[kb.variante(x, y)]
        return andere[k][kb.variante(x, y)]

    # Gras-Vertices (>= 2 von 4 Nachbarzellen Gras)
    def z(x, y):
        return cls[min(max(y, 0), rows - 1)][min(max(x, 0), cols - 1)]
    vg = [[sum(z(vx + dx, vy + dy) == 'g' for dx in (-1, 0) for dy in (-1, 0)) >= 2
           for vx in range(cols + 1)] for vy in range(rows + 1)]

    img = Image.new('RGBA', (cols * T, rows * T))
    for y in range(rows):
        for x in range(cols):
            ecken = (vg[y][x], vg[y][x + 1], vg[y + 1][x], vg[y + 1][x + 1])
            if any(ecken) and not all(ecken) and bg is not None:
                pat = [[255] * 4]
                for vy in (y, y + 1):
                    pat.append([255, int(vg[vy][x]), int(vg[vy][x + 1]), 255])
                pat.append([255] * 4)
                t, _ = kb.waehle(bg['tiles'], pat)
                k = t['img'].copy()
                # Betonflaeche der Uebergangskachel durch die positionsrichtige Betonkachel ersetzen
                ziel = beton[(x % 2, y % 2, kb.variante(x, y, 3))].load()
                pk, pr = k.load(), beton_ref.load()
                for yy in range(T):
                    for xx in range(T):
                        if pk[xx, yy] == pr[xx, yy]:
                            pk[xx, yy] = ziel[xx, yy]
                img.paste(k, (x * T, y * T))
            elif all(ecken):
                img.paste(gras[kb.variante(x, y)], (x * T, y * T))
            else:
                img.paste(kachel(x, y) if cls[y][x] != 'g' else beton[(x % 2, y % 2, 0)], (x * T, y * T))

    L = ind.Leinwand(img)
    # --- Kanten zwischen Bodenarten (gerade Industriekanten, Licht von oben links)
    for y in range(rows):
        for x in range(cols):
            a = cls[y][x]
            for dx, dy in ((1, 0), (0, 1)):
                nx, ny = x + dx, y + dy
                if nx >= cols or ny >= rows:
                    continue
                b = cls[ny][nx]
                if a == b or 'g' in (a, b) or 's' in (a, b):
                    continue
                paar = {a, b}
                if paar == {'w', 'a'} and dy:
                    ind.bordstein(L, x * T, (x + 1) * T, ny * T, oben=(a == 'w'))
                    continue
                # Grenzlinie: dunkle Fuge + Lichtkante auf der unteren/rechten Seite
                for i in range(T):
                    if dy:
                        L.p(x * T + i, ny * T, ind.WAND[0] if 'm' in paar else ind.WAND[1])
                        L.p(x * T + i, ny * T + 1, ind.WAND[4] if b != 'm' else ind.WAND[2])
                    else:
                        L.p(nx * T, y * T + i, ind.WAND[0] if 'm' in paar else ind.WAND[1])
                        L.p(nx * T + 1, y * T + i, ind.WAND[4] if b != 'm' else ind.WAND[2])
    # --- Bodenflecken, Markierungen, Mittellinie
    gebaut = set()
    for g in lay.get('gebaeude', []) + lay.get('mauern', []):
        x0, y0, x1, y1 = g['r']
        gebaut.update((x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1))
    def nah_wand(x, y):
        return any((x + dx, y + dy) in gebaut for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    linien = set()
    for k in ('schienen', 'foerderbaender', 'rohre'):
        for l in lay.get(k, []):
            pts = l['pfad'] if 'pfad' in l else [l['von'], l['bis']]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                for x in range(min(ax, bx) - 1, max(ax, bx) + 3):
                    for y in range(min(ay, by) - 1, max(ay, by) + 3):
                        linien.add((x, y))
    for (tx, ty) in lay.get('bodenluefter', []):
        linien.update((tx + i, ty + j) for i in range(-1, 3) for j in range(-1, 3))
    pf_alt = os.path.join(OBJ, 'platzierung.json')        # Objekte stehen nie auf Dellen
    if os.path.exists(pf_alt):
        for o in json.load(open(pf_alt)):
            if o.get('basis') in ('schatten',):
                continue
            fx, fy = o['x'] // T, (o['y'] + o.get('fuss', 0)) // T
            for x in range(fx - 1, fx + 9):
                for y in range(fy - 4, fy + 2):
                    linien.add((x, y))
    dellen = ind.boden_details(L, cls, rows, cols, nah_wand, gesperrt=linien)
    ind.schlamm(L, [(x, y) for y in range(rows) for x in range(cols) if cls[y][x] == 's'])
    zebras = [m for m in lay.get('markierungen', []) if m['art'] == 'zebra']
    strassen = [z_ for z_ in lay['boden'] if z_['art'] == 'asphalt']
    for s in strassen:
        x0, y0, x1, y1 = s['r']
        ym = ((y0 + y1 + 1) * T) // 2 - 1
        for x in range(x0 * T + 4, (x1 + 1) * T - 4):
            if any(m['r'][0] * T - 4 <= x < (m['r'][2] + 1) * T + 4 for m in zebras if m['r'][1] <= (y0 + y1) // 2 <= m['r'][3]):
                continue
            if (x // 8) % 2 == 0:
                L.p(x, ym, ind.CREME); L.p(x, ym + 1, ind.rgb('#bdb38e'))
    for m in lay.get('markierungen', []):
        ind.markierung(L, m)
    # --- Schienen, Foerderbaender, Rohre
    for s in lay.get('schienen', []):
        ind.schiene(L, s['von'], s['bis'])
    for f in lay.get('foerderbaender', []):
        ind.foerderband(L, f['von'], f['bis'], frame or 0)
    for (tx, ty) in lay.get('bodenluefter', []):
        ind.bodenluefter(L, tx, ty, frame or 0)
    ind.dach_fassade(L, cls, rows, cols)
    for r in lay.get('rohre', []):
        if 'pfad' in r:
            ind.rohr_pfad(L, [tuple(p_) for p_ in r['pfad']])
        else:
            ind.rohr(L, r['von'], r['bis'])
    # --- Mauern und Gebaeude
    import random
    rnd = random.Random(5)
    for m in sorted(lay.get('mauern', []), key=lambda m: m['seite'] in ('links', 'rechts')):
        if m['seite'] != 'vorne':
            ind.mauer(L, m['r'], m['seite'], rnd)
    for g in sorted(lay.get('gebaeude', []), key=lambda g: g['r'][3]):
        ind.gebaeude(L, g, rnd)
    # Bodenmaske: nur hier duerfen Objektschatten liegen (nicht auf Daechern, Fassaden, Mauern,
    # Gebaeuden, Rohren, Foerderbaendern)
    import numpy as _npm
    boden = _npm.ones((rows * T, cols * T), _npm.float32)
    for y in range(rows):
        for x in range(cols):
            if cls[y][x] == 'm':
                boden[y * T:(y + 1) * T, x * T:(x + 1) * T] = 0
                if y + 1 < rows and cls[y + 1][x] != 'm':          # Fassade unter der Dachkante
                    boden[(y + 1) * T:(y + 1) * T + 28, x * T:(x + 1) * T] = 0
    for g in lay.get('gebaeude', []):
        x0, y0, x1, y1 = g['r']
        boden[y0 * T:(y1 + 1) * T, x0 * T:(x1 + 1) * T] = 0
    for m in lay.get('mauern', []):
        x0, y0, x1, y1 = m['r']
        boden[max(0, y0 * T - (14 if m['seite'] == 'vorne' else 0)):(y1 + 1) * T, x0 * T:(x1 + 1) * T] = 0
    # Gebaeude, Daecher, Fassaden, Mauern: hoeher als der Boden -> verdecken Objekte daneben (Regel Verdeckung)
    hoch_bau = boden == 0
    for k in ('foerderbaender', 'rohre'):
        for l in lay.get(k, []):
            pts = l['pfad'] if 'pfad' in l else [l['von'], l['bis']]
            breite = 2 if k == 'foerderbaender' else 1
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                if k == 'rohre':
                    q0, q1 = 4, 12
                    if ax == bx:
                        boden[min(ay, by) * T:(max(ay, by) + 1) * T, ax * T + q0:ax * T + q1] = 0
                    else:
                        boden[ay * T + q0:ay * T + q1, min(ax, bx) * T:(max(ax, bx) + 1) * T] = 0
                else:
                    if ax == bx:
                        boden[min(ay, by) * T:(max(ay, by) + 1) * T, ax * T:(ax + breite) * T] = 0
                    else:
                        boden[ay * T:(ay + breite) * T, min(ax, bx) * T:(max(ax, bx) + 1) * T] = 0
    if speichern:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))

    # --- Objekte
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = []
    if os.path.exists(pf):
        objs = sorted(json.load(open(pf)), key=lambda o: (o.get('ebene', 1), o['y'] + o.get('fuss', 0)))
        schatten = Image.new('L', img.size, 0)
        sd = ImageDraw.Draw(schatten)
        cache = {}
        for o in objs:
            if o['datei'] not in cache:
                cache[o['datei']] = Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA')
            if 'schatten' in o:
                w, h = o['schatten']
                cx, cy = o['x'] + cache[o['datei']].width // 2, o['y'] + o['fuss'] - 2
                sd.ellipse((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), fill=95)
        # Kante Boden/Objekt: entlang der Auflagekante Schmutzsaum, Sand-/Schlammspritzer und Unkraut
        import numpy as _np0, random as _rr
        rk = _rr.Random(11)
        for o in objs:
            b_ = o.get('basis', '')
            if b_ in ('schatten', 'abgeleitet/laterne', 'abgeleitet/leer') or 'kran' in b_:
                continue
            a = _np0.array(cache[o['datei']].getchannel('A')) >= 200
            zeilen = _np0.nonzero(a.any(axis=1))[0]
            if len(zeilen) == 0:
                continue
            gross = a.shape[0] > 40
            for xi in _np0.nonzero(a.any(axis=0))[0]:
                yu = int(_np0.nonzero(a[:, xi])[0].max())
                if yu < zeilen.max() - 4:
                    continue                                   # nur die tatsaechliche Auflagekante
                X, Y = o['x'] + int(xi), o['y'] + yu
                for d, f in ((1, 0.62), (2, 0.78), (3, 0.9)):    # Schmutzsaum direkt an der Kante
                    L.neutral(X, Y + d, f, waerme=3)
                r = rk.random()
                if r < (0.22 if gross else 0.12):              # Sand/Staub angeweht
                    for k in range(rk.randint(1, 3)):
                        L.p(X + rk.randint(-1, 1), Y + rk.randint(1, 3), ind.rgb('#9a8a6e') if k % 2 else ind.rgb('#b3a283'))
                elif r < (0.32 if gross else 0.18):            # Schlammspritzer
                    L.p(X, Y + rk.randint(1, 4), ind.SCHLAMM[2]); L.p(X + 1, Y + 2, ind.SCHLAMM[1])
                elif r < (0.40 if gross else 0.22):            # Unkraut in der Fuge
                    for k in range(rk.randint(2, 4)):
                        L.p(X + rk.randint(-1, 1), Y - k + 1, ind.rgb('#5f9a48') if k % 2 else ind.rgb('#43783a'))
        # Schmutz/Oel unter schweren Objekten (vor den Schatten, direkt auf den Boden)
        import random as _r
        rs = _r.Random(3)
        for o in objs:
            gruppe = o.get('basis', '').split('/')[0]
            if gruppe not in ('ortho', 'mittel', 'turm', 'hoch', 'reaktor', 'abgeleitet') or o.get('basis') in (
                    'schatten', 'abgeleitet/laterne'):
                continue
            w = cache[o['datei']].width
            by = o['y'] + o['fuss'] - 3
            for _ in range(max(2, w // 12)):
                fx, fy = o['x'] + rs.randint(0, w), by + rs.randint(-2, 4)
                rx, ry = rs.randint(3, 7), rs.randint(1, 3)
                for yy in range(-ry, ry + 1):
                    for xx in range(-rx, rx + 1):
                        if xx * xx / (rx * rx) + yy * yy / (ry * ry) <= 1 and rs.random() < 0.8:
                            L.neutral(fx + xx, fy + yy, 0.8, waerme=3)
                if 'container' in o.get('basis', '') and rs.random() < 0.6:
                    for _ in range(5):
                        L.p(fx + rs.randint(-4, 4), fy + rs.randint(-1, 2), ind.rgb('#8a5a3a'))
        # Schlagschatten aus der Silhouette: Licht oben links -> flach nach rechts unten auf den Boden
        import numpy as _np
        sm = _np.zeros((img.size[1], img.size[0]), _np.float32)
        for o in objs:
            if o.get('basis') in ('schatten',):
                continue
            sp = cache[o['datei']]
            a = _np.array(sp.getchannel('A')) >= 200
            zeilen = _np.nonzero(a.any(axis=1))[0]
            if len(zeilen) < 6:
                continue
            fuss_y = o['y'] + zeilen.max()
            hoehe = zeilen.max() - zeilen.min()
            flach = 0.42                                   # Schattenlaenge relativ zur Hoehe
            for zi in zeilen:
                k = zeilen.max() - zi                      # Hoehe ueber dem Fuss
                ty = int(fuss_y - 2 + k * flach * 0.55)    # Schatten liegt unterhalb/rechts des Fusses
                dx = int(3 + k * flach)
                if not (0 <= ty < sm.shape[0]):
                    continue
                xs = _np.nonzero(a[zi])[0] + o['x'] + dx
                xs = xs[(xs >= 0) & (xs < sm.shape[1])]
                sm[ty, xs] = 1.0
        sm_img = Image.fromarray((sm * 70).astype(_np.uint8)).filter(ImageFilter.MaxFilter(3))
        schatten = Image.fromarray(_np.maximum(_np.array(schatten.filter(ImageFilter.GaussianBlur(1.2))),
                                               _np.array(sm_img)).astype(_np.uint8))
        dunkel = Image.new('RGBA', img.size, (14, 22, 30, 255))
        schatten = Image.fromarray((_np.array(schatten).astype(_np.float32) * boden).astype(_np.uint8))
        dunkel.putalpha(schatten)
        img.alpha_composite(dunkel)
        vor_objekten = _np.array(img)
        for o in objs:
            sp = cache[o['datei']]
            ox, oy = o['x'], o['y']
            if frame is not None and o.get('anim') == 'wehen':
                sp = kb.wehen(sp, kb.wind(frame, o['x']))
            elif frame is not None and o.get('anim') == 'greifarm':
                sp = greifarm_pose(sp, frame, (o['x'] * 13 + o['y'] * 7) % 16)
            elif frame is not None and o.get('anim') == 'portal':
                sp = portal_pose(sp, frame, (o['x'] // 16) % 16)
            elif frame is not None and o.get('anim') == 'kran':
                sp = Image.open(os.path.join(OBJ, o['datei'].replace('abgeleitet-kran_', 'abgeleitet-kran_f%02d_' % frame))).convert('RGBA')
            img.alpha_composite(sp, (ox, oy))
        kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
        import karte04_bauen as _k4
        _k4.klippen_verdeckung(img, [o for o in objs if o.get('basis') not in ('schatten',) and 'kran' not in o.get('datei', '')],
                               cache, hoch_bau, ~hoch_bau, vor_objekten)
    # Vordergrund: suedliche Aussenmauer ueber Objekten und Schatten
    L2 = ind.Leinwand(img)
    for m in lay.get('mauern', []):
        if m['seite'] == 'vorne':
            ind.mauer_vorne(L2, m['r'])
        leitungen(img, os.path.join(OBJ, 'leitungen.json'), boden)
    if frame is not None:
        animation(img, objs, frame)
        return img
    if speichern:
        img.save(os.path.join(KARTE, 'terrain.png'))
        json.dump({'tile_size': T, 'cols': cols, 'rows': rows, 'klassen': [''.join(r) for r in cls],
                   'dellen': sorted(dellen),
                   'tilesets': {'k2_beton_gras': bg['id'] if bg else None}},
                  open(os.path.join(KARTE, 'tilemap.json'), 'w'))
    print('Karte 02 %dx%d gebaut' % (cols, rows))
    return img


def _linie(img, a, b, farbe, durchhang=0, maske=None):
    px = img.load()
    W, H = img.size
    (x0, y0), (x1, y1) = a, b
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / max(1, n)
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + durchhang * 4 * t * (1 - t)
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < W and 0 <= yi < H:
            if maske is not None and maske[yi, xi] == 0:
                continue
            if len(farbe) == 4 and farbe[3] < 255:
                r, g, b_, a_ = px[xi, yi]
                f = farbe[3] / 255
                px[xi, yi] = (int(r * (1 - f) + farbe[0] * f), int(g * (1 - f) + farbe[1] * f),
                              int(b_ * (1 - f) + farbe[2] * f), a_)
            else:
                px[xi, yi] = farbe[:3] + (255,)


def leitungen(img, pfad, boden=None):
    """Hochspannungsleitungen zwischen den Masten: Draehte mit leichtem Durchhang und ihr Schatten auf
    dem Boden (versetzt nach rechts unten wie die Schlagschatten)."""
    if not os.path.exists(pfad):
        return
    d = json.load(open(pfad))
    m = d['masten']
    h = d.get('hoehe', 84)
    for a, b in zip(m, m[1:]):
        for i in range(4):
            pa, pb = a[i], b[i]
            # Schatten auf dem Boden (Hoehe -> Versatz)
            _linie(img, (pa[0] + h * 0.42, pa[1] + h * 0.55 + h * 0.23), (pb[0] + h * 0.42, pb[1] + h * 0.55 + h * 0.23),
                   (14, 22, 30, 45), durchhang=3, maske=boden)
    for a, b in zip(m, m[1:]):
        for i in range(4):
            _linie(img, a[i], b[i], (35, 40, 47), durchhang=6)


def greifarm_pose(sp, frame, phase):
    """Fester Roboterarm: Sockel (untere 40 %) steht, Oberarm dreht um das Schultergelenk, die Hand
    (oberes Viertel) dreht zusaetzlich um das Ellbogengelenk -> Scherung in zwei Stufen, kein Auf und Ab."""
    import math
    h = sp.height
    a = 2.2 * math.sin(2 * math.pi * (frame + phase) / 16)
    b = 1.4 * math.sin(2 * math.pi * (frame + phase) / 16 + 1.4)
    out = Image.new('RGBA', sp.size)
    schulter, ellbogen = h * 0.6, h * 0.28
    for y in range(h):
        d = 0.0
        if y < schulter:
            d += a * (1 - y / schulter)
        if y < ellbogen:
            d += b * (1 - y / ellbogen)
        out.paste(sp.crop((0, y, sp.width, y + 1)), (round(d), y))
    return out


def portal_pose(sp, frame, phase):
    """Portal-Greifer: Rahmen und Traeger stehen, Laufkatze mit Klaue faehrt links/rechts."""
    import math
    w, h = sp.size
    dx = round(6 * math.sin(2 * math.pi * (frame + phase) / 16))
    bein = max(9, round(w * 0.15))        # Beine samt Innenkante bleiben stehen
    traeger = int(h * 0.24)
    out = sp.copy()
    teil = sp.crop((bein, traeger, w - bein, h))
    leer = Image.new('RGBA', teil.size)
    out.paste(leer, (bein, traeger))
    # Beine wieder einsetzen (falls im Ausschnitt) und Klaue verschoben einsetzen
    out.alpha_composite(teil, (bein + dx, traeger))
    out.alpha_composite(sp.crop((0, 0, bein + 1, h)), (0, 0))
    out.alpha_composite(sp.crop((w - bein - 1, 0, w, h)), (w - bein - 1, 0))
    return out


def animation(img, objs, frame):
    """Leuchten, Feuer und Rauch je Frame (Details in karte02_objekte.ANIM)."""
    kb.leuchten(img, frame, [])
    try:
        import karte02_objekte as ko
        ko.animieren(img, objs, frame)
    except ImportError:
        pass


def main():
    bauen()


if __name__ == '__main__':
    main()
