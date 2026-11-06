"""Boden-Tileset von Karte 01 (Muster wie Karte 06): alles ausser den Objekten (Gras, Waldboden, Wege, Sand, Teich,
Kabel, Zaun, Steg, Teleporter ...), zerlegt in 16x16-Kacheln.

  python3 tools/karte01_tilesets_boden.py   ->  maps/karte01/tilesets/boden_* (+ karte01_tilesets.zip)

boden_tileset.png             jede Bodenkachel genau einmal. Oben (die ersten Reihen) stehen die animierten
                              Kacheln, darunter alle unbewegten.
boden_tileset_animiert.png    NUR die animierten Kacheln, exakt am selben Platz wie in boden_tileset.png,
                              16 Animationsbilder untereinander (Bild n beginnt bei y = n * hoehe_animationsbereich).
boden_animiert_frames/        dieselben 16 Bilder einzeln.
boden_raster.json             Karte als Raster (Zeilen x Spalten) mit dem Kachelindex je Feld
                              (Index = Reihe * breite_kacheln + Spalte im Tileset).
karte01_boden.tmx             Tiled-Karte mit der Bodenebene (Tileset boden_tileset.png, Animationen eingetragen).
vorschau_boden.png            die zusammengesetzte Karte aus den Kacheln (Kontrolle: identisch zum Boden).

Die Karte wird dafuer ohne Objekte gebaut (karte_bauen mit objekte=False: Boden, Klippen, Wasser, Bauwerke, Waldboden - ohne Objekte und Schatten).
Objektschatten gehoeren zu den Objekten und sind hier nicht enthalten.
"""
import json, os, shutil, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

import karte_bauen as kb

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte01')
OUT = os.path.join(KARTE, 'tilesets')
T = 16
N = kb.N_FRAMES
BREITE = 32
DAUER = 170


def boden(frame):
    return np.array(kb.bauen(frame=frame, speichern=False, objekte=False).convert('RGBA'))


def main():
    stand = boden(None)
    frames = [boden(f) for f in range(N)]
    Hh, W = stand.shape[:2]
    rows, cols = Hh // T, W // T

    def kachel(a, x, y):
        return a[y * T:(y + 1) * T, x * T:(x + 1) * T]
    # je Feld: Standkachel + (bei Animation) Folge der 16 Bilder
    felder = {}
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
    anim_liste = list(anim_keys)
    stat_liste = list(stat_keys)
    anim_reihen = (len(anim_liste) + BREITE - 1) // BREITE
    stat_reihen = (len(stat_liste) + BREITE - 1) // BREITE
    index = {}
    for i, k in enumerate(anim_liste):
        index[(True, k)] = i
    for i, k in enumerate(stat_liste):
        index[(False, k)] = anim_reihen * BREITE + i
    gesamt = anim_reihen + stat_reihen
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
               'karte_spalten': cols, 'karte_zeilen': rows, 'raster': raster},
              open(os.path.join(OUT, 'boden_raster.json'), 'w'))
    # Tiled: Animation als eigenes Tileset (Bilder untereinander), Standkachel verweist auf die Folge
    anim_tsx = ''.join(
        '   <tile id="%d"><animation>%s</animation></tile>\n'
        % (i, ''.join('<frame tileid="%d" duration="%d"/>' % (gesamt * BREITE + f * anim_reihen * BREITE + i, DAUER)
                      for f in range(N)))
        for i in range(len(anim_liste)))
    daten = '\n'.join(','.join(str(v + 1) for v in reihe) for reihe in raster)
    tmx = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<map version="1.10" orientation="orthogonal" renderorder="right-down" width="%d" height="%d" '
           'tilewidth="16" tileheight="16" infinite="0">\n'
           ' <tileset firstgid="1" name="boden" tilewidth="16" tileheight="16" tilecount="%d" columns="%d">\n'
           '  <image source="boden_tileset.png" width="%d" height="%d"/>\n%s </tileset>\n'
           ' <tileset firstgid="%d" name="boden_animiert" tilewidth="16" tileheight="16" tilecount="%d" columns="%d">\n'
           '  <image source="boden_tileset_animiert.png" width="%d" height="%d"/>\n </tileset>\n'
           ' <layer id="1" name="Boden" width="%d" height="%d">\n  <data encoding="csv">\n%s\n  </data>\n </layer>\n'
           '</map>\n') % (cols, rows, gesamt * BREITE, BREITE, BREITE * T, gesamt * T, anim_tsx,
                          gesamt * BREITE + 1, anim_reihen * BREITE * N, BREITE, BREITE * T, ah * N,
                          cols, rows, daten)
    open(os.path.join(OUT, 'karte01_boden.tmx'), 'w').write(tmx)
    # Vorschau-GIF der animierten Bodenkacheln
    vor = []
    for f in range(N):
        g = Image.new('RGBA', (BREITE * T, ah), (40, 44, 52, 255))
        g.alpha_composite(Image.open(os.path.join(fd, 'frame_%02d.png' % f)))
        vor.append(g.resize((g.width * 2, g.height * 2), Image.NEAREST).convert('RGB')
                   .quantize(colors=255, method=Image.Quantize.MAXCOVERAGE))
    vor[0].save(os.path.join(OUT, 'vorschau_boden_animiert.gif'), save_all=True, append_images=vor[1:],
                duration=DAUER, loop=0)
    with zipfile.ZipFile(os.path.join(KARTE, 'karte01_tilesets.zip'), 'w', zipfile.ZIP_DEFLATED) as z:
        for wurzel, _, dateien in os.walk(OUT):
            for d in dateien:
                p = os.path.join(wurzel, d)
                z.write(p, os.path.relpath(p, KARTE))
    print('Karte %dx%d: %d unbewegte + %d animierte Bodenkacheln, Tileset %dx%d Kacheln, Animationsbereich %d Reihen'
          % (cols, rows, len(stat_liste), len(anim_liste), BREITE, gesamt, anim_reihen))


if __name__ == '__main__':
    main()
