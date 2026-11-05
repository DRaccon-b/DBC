"""Boden-Tileset der Startkarte (Karte 06): alles ausser den Objekten (Gras, Waldboden, Wege, Sand, Teich,
Kabel, Zaun, Steg, Teleporter ...), zerlegt in 16x16-Kacheln.

  python3 tools/karte06_boden_export.py   ->  maps/karte06/tileset/boden_* (+ karte06_tileset.zip)

boden_tileset.png             jede Bodenkachel genau einmal. Oben (die ersten Reihen) stehen die animierten
                              Kacheln, darunter alle unbewegten.
boden_tileset_animiert.png    NUR die animierten Kacheln, exakt am selben Platz wie in boden_tileset.png,
                              16 Animationsbilder untereinander (Bild n beginnt bei y = n * hoehe_animationsbereich).
boden_animiert_frames/        dieselben 16 Bilder einzeln.
boden_raster.json             Karte als Raster (Zeilen x Spalten) mit dem Kachelindex je Feld
                              (Index = Reihe * breite_kacheln + Spalte im Tileset).
karte06_boden.tmx             Tiled-Karte mit der Bodenebene (Tileset boden_tiled.png = Tileset + Animationsbilder,
                              Kachelanimationen eingetragen).
vorschau_boden_gruppen.png    Tileset mit Gruppennamen (Wasser, Steg, Gras, Wege, Plaetze, Zaun ...).
vorschau_boden.png            die zusammengesetzte Karte aus den Kacheln (Kontrolle: identisch zum Boden).

Die Karte wird dafuer ohne Objekte gebaut (karte06_bauen unveraendert, nur die Objektliste ausgeblendet).
Objektschatten gehoeren zu den Objekten und sind hier nicht enthalten.
"""
import json, math, os, shutil, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

import karte06_bauen as k6

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte06')
OUT = os.path.join(KARTE, 'tileset')
T = 16
N = k6.N_FRAMES
BREITE = 32
DAUER = 170


def boden(frame):
    alt = k6.OBJ
    k6.OBJ = os.path.join(OUT, '_keine_objekte')              # Objektliste nicht vorhanden -> nur Boden
    try:
        return np.array(k6.bauen(frame=frame, speichern=False).convert('RGBA'))
    finally:
        k6.OBJ = alt


def main():
    stand = boden(None)
    frames = [boden(f) for f in range(N)]
    Hh, W = stand.shape[:2]
    rows, cols = Hh // T, W // T

    def kachel(a, x, y):
        return a[y * T:(y + 1) * T, x * T:(x + 1) * T]
    # je Feld: Standkachel + (bei Animation) Folge der 16 Bilder
    felder, erste = {}, {}
    anim_keys, stat_keys = {}, {}
    for y in range(rows):
        for x in range(cols):
            s = kachel(stand, x, y)
            folge = [kachel(fr, x, y) for fr in frames]
            animiert = any(not np.array_equal(f, s) for f in folge) and \
                any(not np.array_equal(f, folge[0]) for f in folge[1:])
            if animiert:
                key = s.tobytes() + b''.join(f.tobytes() for f in folge)
                if key not in anim_keys:
                    anim_keys[key] = (s, folge)
            else:
                key = s.tobytes()
                if key not in stat_keys:
                    stat_keys[key] = s
            felder[(x, y)] = (animiert, key)
            erste.setdefault((animiert, key), (x, y))
    anim_liste = list(anim_keys)
    stat_liste = list(stat_keys)
    # --- sauber geordnet: Kacheln nach Material in Gruppen, jede Gruppe ab einer neuen Reihe ---
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    zm = lambda k: k6.zell_maske(cls, k, cols, rows)
    mat = {'h': k6.weich(zm('h'), 5, 0.4, 3),
           'w': k6.weich(zm('w'), 7.0, 0.5, 4, 0.36), 's': k6.weich(zm('s'), 4.0, 0.4, 5, 0.36),
           'p': k6.weich(zm('p'), 4, 0.12, 6), 'c': k6.weich(zm('c'), 2.5, 0, 7),
           'x': k6.weich(zm('x'), 6, 0.2, 8, 0.45)}
    pm = mat['p']
    mat['p'] = pm | np.roll(pm, 1, 0) | np.roll(pm, 2, 0)                   # Schattenkante unter dem Bordstein
    xm = mat['x']
    for _ in range(4):                                                       # Erdrand ums Wasser
        xm = xm | np.roll(xm, 1, 0) | np.roll(xm, -1, 0) | np.roll(xm, 1, 1) | np.roll(xm, -1, 1)
    mat['x'] = xm
    px0, py0, px1, py1 = lay['pension']
    sx0, sy0, sx1, sy1 = lay['steg']
    tp = lay['teleporter'][0]
    NAMEN = {'x': 'Wasser', 'c': 'Cyber-Platz', 'p': 'Steinplatz', 's': 'Spielplatz-Sand', 'w': 'Sandweg',
             'h': 'Waldboden'}

    def gruppe(x, y):
        if tp['x'] - 1 <= x <= tp['x'] + tp['b'] and tp['y'] - 1 <= y <= tp['y'] + tp['h']:
            return 'Teleporter'
        if sx0 <= x <= sx1 and sy0 - 1 <= y <= sy1 + 1:
            return 'Steg'
        if (px0 <= x <= px1 and y in (py0, py1, py0 - 1, py1 - 1)) or (py0 - 1 <= y <= py1 and x in (px0, px1)):
            return 'Zaun'
        feld = (slice(y * T, (y + 1) * T), slice(x * T, (x + 1) * T))
        da = {k: m[feld].mean() for k, m in mat.items() if m[feld].any()}
        for k in ('x', 'c', 'p', 's', 'w'):
            if k in da:
                return NAMEN[k] if da[k] >= 0.999 else NAMEN[k] + ' - Rand'
        if 'h' in da:
            return 'Waldboden' if da['h'] >= 0.999 else 'Gras - Waldrand'
        return 'Gras'
    REIHENFOLGE = ['Wasser', 'Wasser - Rand', 'Steg', 'Cyber-Platz', 'Cyber-Platz - Rand', 'Teleporter',
                   'Gras', 'Waldboden', 'Gras - Waldrand', 'Sandweg', 'Sandweg - Rand', 'Spielplatz-Sand',
                   'Spielplatz-Sand - Rand', 'Steinplatz', 'Steinplatz - Rand', 'Zaun']

    def sortierwert(t, x, y, g):
        """In Randgruppen: nach Richtung des Materials (oben, rechts, unten, links ...), sonst nach Helligkeit."""
        hell = float(t[..., :3].mean())
        k = next((kk for kk, n in NAMEN.items() if g.startswith(n)), None)
        if k and g.endswith('Rand'):
            m = mat[k][y * T:(y + 1) * T, x * T:(x + 1) * T]
            ys, xs = np.nonzero(m)
            w = math.atan2(ys.mean() - 7.5, xs.mean() - 7.5) if len(xs) and m.mean() < 0.999 else 0.0
            return (round((w + math.pi) / (math.pi / 4)) % 8, -m.mean(), hell)
        return (0, 0, hell)
    gruppen = []                                       # (animiert, name, [keys])
    for animiert, liste, quelle in ((True, anim_liste, anim_keys), (False, stat_liste, stat_keys)):
        g_ = {}
        for k in liste:
            x, y = erste[(animiert, k)]
            g = gruppe(x, y)
            t = quelle[k][0] if animiert else quelle[k]
            g_.setdefault(g, []).append((sortierwert(t, x, y, g), k))
        for name in REIHENFOLGE + sorted(set(g_) - set(REIHENFOLGE)):
            if name in g_:
                gruppen.append((animiert, name, [k for _, k in sorted(g_[name], key=lambda v: v[0])]))
    index, reihe, gruppen_info = {}, 0, []
    for animiert, name, keys in gruppen:
        for i, k in enumerate(keys):
            index[(animiert, k)] = (reihe + i // BREITE) * BREITE + i % BREITE
        n_r = (len(keys) + BREITE - 1) // BREITE
        gruppen_info.append({'name': name, 'animiert': animiert, 'erste_reihe': reihe, 'reihen': n_r,
                             'kacheln': len(keys)})
        reihe += n_r
    anim_reihen = sum(g['reihen'] for g in gruppen_info if g['animiert'])
    gesamt = reihe
    os.makedirs(OUT, exist_ok=True)
    ts = np.zeros((gesamt * T, BREITE * T, 4), np.uint8)

    def setze(ziel, i, t, y_off=0):
        r, c = divmod(i, BREITE)
        ziel[y_off + r * T:y_off + (r + 1) * T, c * T:(c + 1) * T] = t
    for k in anim_liste:
        setze(ts, index[(True, k)], anim_keys[k][0])
    for k in stat_liste:
        setze(ts, index[(False, k)], stat_keys[k])
    Image.fromarray(ts).save(os.path.join(OUT, 'boden_tileset.png'))
    fd = os.path.join(OUT, 'boden_animiert_frames')
    if os.path.isdir(fd):
        shutil.rmtree(fd)
    os.makedirs(fd)
    ah = max(1, anim_reihen) * T
    sheet = np.zeros((ah * N, BREITE * T, 4), np.uint8)
    for f in range(N):
        fr = np.zeros((ah, BREITE * T, 4), np.uint8)
        for k in anim_liste:
            setze(fr, index[(True, k)], anim_keys[k][1][f])
        Image.fromarray(fr).save(os.path.join(fd, 'frame_%02d.png' % f))
        sheet[f * ah:(f + 1) * ah] = fr
    Image.fromarray(sheet).save(os.path.join(OUT, 'boden_tileset_animiert.png'))
    raster = [[index[felder[(x, y)]] for x in range(cols)] for y in range(rows)]
    # Kontrolle: aus den Kacheln zusammensetzen
    probe = np.zeros_like(stand)
    for y in range(rows):
        for x in range(cols):
            r, c = divmod(raster[y][x], BREITE)
            probe[y * T:(y + 1) * T, x * T:(x + 1) * T] = ts[r * T:(r + 1) * T, c * T:(c + 1) * T]
    assert np.array_equal(probe, stand), 'Zusammensetzung weicht ab'
    Image.fromarray(probe).save(os.path.join(OUT, 'vorschau_boden.png'))
    json.dump({'kachel': T, 'breite_kacheln': BREITE, 'tileset_reihen': gesamt,
               'animierte_kacheln': len(anim_liste), 'animationsbereich_hoehe_kacheln': anim_reihen,
               'animationsbilder': N, 'bilddauer_ms': DAUER, 'unbewegte_kacheln': len(stat_liste),
               'karte_spalten': cols, 'karte_zeilen': rows, 'gruppen': gruppen_info, 'raster': raster},
              open(os.path.join(OUT, 'boden_raster.json'), 'w'))
    # Tiled: Animation als eigenes Tileset (Bilder untereinander), Standkachel verweist auf die Folge
    anim_tsx = ''.join(
        '   <tile id="%d"><animation>%s</animation></tile>\n'
        % (i, ''.join('<frame tileid="%d" duration="%d"/>' % (gesamt * BREITE + f * anim_reihen * BREITE + i, DAUER)
                      for f in range(N)))
        for i in sorted(index[(True, k)] for k in anim_liste))
    daten = '\n'.join(','.join(str(v + 1) for v in reihe) for reihe in raster)
    # fuer Tiled: ein Bild = Tileset + darunter die 16 Animationsbilder (Animation nur innerhalb eines Tilesets)
    tiled = np.concatenate([ts, sheet], axis=0)
    Image.fromarray(tiled).save(os.path.join(OUT, 'boden_tiled.png'))
    tmx = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<map version="1.10" orientation="orthogonal" renderorder="right-down" width="%d" height="%d" '
           'tilewidth="16" tileheight="16" infinite="0">\n'
           ' <tileset firstgid="1" name="boden" tilewidth="16" tileheight="16" tilecount="%d" columns="%d">\n'
           '  <image source="boden_tiled.png" width="%d" height="%d"/>\n%s </tileset>\n'
           ' <layer id="1" name="Boden" width="%d" height="%d">\n  <data encoding="csv">\n%s\n  </data>\n </layer>\n'
           '</map>\n') % (cols, rows, tiled.shape[0] // T * BREITE, BREITE, BREITE * T, tiled.shape[0], anim_tsx,
                          cols, rows, daten)
    open(os.path.join(OUT, 'karte06_boden.tmx'), 'w').write(tmx)
    # beschriftete Vorschau (2x, Kachelgitter, Gruppennamen links)
    from PIL import ImageDraw
    rand_l = 170
    v = Image.new('RGBA', (rand_l + BREITE * T * 2, gesamt * T * 2), (40, 44, 52, 255))
    v.alpha_composite(Image.fromarray(ts).resize((BREITE * T * 2, gesamt * T * 2), Image.NEAREST), (rand_l, 0))
    dr = ImageDraw.Draw(v)
    for g in gruppen_info:
        y = g['erste_reihe'] * T * 2
        dr.line((0, y, v.width, y), fill=(255, 210, 90, 255), width=1)
        dr.text((6, y + 4), g['name'] + (' (animiert)' if g['animiert'] else ''), fill=(255, 255, 255, 255))
        dr.text((6, y + 16), '%d Kacheln' % g['kacheln'], fill=(180, 190, 200, 255))
    v.save(os.path.join(OUT, 'vorschau_boden_gruppen.png'))
    # Vorschau-GIF der animierten Bodenkacheln
    vor = []
    for f in range(N):
        g = Image.new('RGBA', (BREITE * T, ah), (40, 44, 52, 255))
        g.alpha_composite(Image.open(os.path.join(fd, 'frame_%02d.png' % f)))
        vor.append(g.resize((g.width * 2, g.height * 2), Image.NEAREST).convert('RGB')
                   .quantize(colors=255, method=Image.Quantize.MAXCOVERAGE))
    vor[0].save(os.path.join(OUT, 'vorschau_boden_animiert.gif'), save_all=True, append_images=vor[1:],
                duration=DAUER, loop=0)
    with zipfile.ZipFile(os.path.join(KARTE, 'karte06_tileset.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        for wurzel, _, dateien in os.walk(OUT):
            for d in dateien:
                p = os.path.join(wurzel, d)
                z.write(p, os.path.relpath(p, KARTE))
    print('Karte %dx%d: %d unbewegte + %d animierte Bodenkacheln, Tileset %dx%d Kacheln, Animationsbereich %d Reihen'
          % (cols, rows, len(stat_liste), len(anim_liste), BREITE, gesamt, anim_reihen))


if __name__ == '__main__':
    main()
