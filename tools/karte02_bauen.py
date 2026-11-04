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
KLASSE = {'beton': 'b', 'asphalt': 'a', 'gehweg': 'w', 'platz': 'p', 'platz_hell': 'h', 'metall': 'm', 'gras': 'g'}
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
        if k == 'b':
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
                if a == b or 'g' in (a, b):
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
    ind.bodenflecken(L, [(x, y) for y in range(rows) for x in range(cols) if cls[y][x] == 'b'],
                     [(x, y) for y in range(rows) for x in range(cols) if cls[y][x] == 'a'])
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
    for r in lay.get('rohre', []):
        ind.rohr(L, r['von'], r['bis'])
    # --- Mauern und Gebaeude
    import random
    rnd = random.Random(5)
    for m in lay.get('mauern', []):
        ind.mauer(L, m['r'], m['seite'], rnd)
    for g in sorted(lay.get('gebaeude', []), key=lambda g: g['r'][3]):
        ind.gebaeude(L, g, rnd)
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
        schatten = schatten.filter(ImageFilter.GaussianBlur(1.2))
        dunkel = Image.new('RGBA', img.size, (14, 22, 30, 255))
        dunkel.putalpha(schatten)
        img.alpha_composite(dunkel)
        for o in objs:
            sp = cache[o['datei']]
            ox, oy = o['x'], o['y']
            if frame is not None and o.get('anim') == 'wehen':
                sp = kb.wehen(sp, kb.wind(frame, o['x']))
            img.alpha_composite(sp, (ox, oy))
        kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
    if frame is not None:
        animation(img, objs, frame)
        return img
    if speichern:
        img.save(os.path.join(KARTE, 'terrain.png'))
        json.dump({'tile_size': T, 'cols': cols, 'rows': rows, 'klassen': [''.join(r) for r in cls],
                   'tilesets': {'k2_beton_gras': bg['id'] if bg else None}},
                  open(os.path.join(KARTE, 'tilemap.json'), 'w'))
    print('Karte 02 %dx%d gebaut' % (cols, rows))
    return img


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
