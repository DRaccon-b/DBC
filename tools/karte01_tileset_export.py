"""Tileset-Export fuer Karte 01.

  python3 tools/karte01_tileset_export.py   ->  maps/karte01/tileset/ (+ karte01_tileset.zip)

1. Bausteine (bausteine.png): die Grundkacheln, aus denen der Boden gebaut wird - Gras, Sand, Wasser, Meer
   (je 5 Varianten) und die Wang-Uebergangssets (gras_weg, wasser_gras, wasser_sand, meer_sand, meer_wasser,
   je 16 Kacheln). Namen und Positionen in bausteine.json.
2. Exakter Export der fertigen Karte, 16x16, doppelte Kacheln zusammengefasst:
     boden_tiles.png          alle Kacheln der Boden-Ebene (unter dem Spieler)
     ueberlagerung_tiles.png  alle Kacheln der Ueberlagerung (ueber dem Spieler)
     kollision_tiles.png      3 Kacheln: begehbar / gesperrt / verdeckt
     karte01.tmx              Tiled-Karte mit den Ebenen Boden, Spieler (Objektebene), Ueberlagerung, Kollision
     karte01_raster.json      dieselben Raster als Index-Listen (fuer eigene Engines)
3. objekte/  alle Objekt-Sprites der Karte einzeln (falls Objekte als Sprites statt Kacheln gesetzt werden).
"""
import json, os, shutil, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte01')
EBENEN = os.path.join(KARTE, 'ebenen')
OUT = os.path.join(KARTE, 'tileset')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
T = 16
SPALTEN = 64


def zerlegen(bild):
    """-> (Liste einzigartiger Kacheln als Arrays, Raster mit Index+1, 0 = leer)."""
    a = np.array(bild.convert('RGBA'))
    H, W = a.shape[:2]
    rows, cols = H // T, W // T
    index, kacheln = {}, []
    raster = np.zeros((rows, cols), np.int32)
    for y in range(rows):
        for x in range(cols):
            t = a[y * T:(y + 1) * T, x * T:(x + 1) * T]
            if t[..., 3].max() == 0:
                continue
            key = t.tobytes()
            if key not in index:
                index[key] = len(kacheln)
                kacheln.append(t)
            raster[y, x] = index[key] + 1
    return kacheln, raster


def atlas(kacheln, pfad):
    n = len(kacheln)
    zeilen = (n + SPALTEN - 1) // SPALTEN
    im = Image.new('RGBA', (SPALTEN * T, max(1, zeilen) * T), (0, 0, 0, 0))
    for i, t in enumerate(kacheln):
        im.paste(Image.fromarray(t), ((i % SPALTEN) * T, (i // SPALTEN) * T))
    im.save(pfad)
    return im.size


def bausteine():
    basis = os.path.join(ROOT, 'assets', 'basis')
    import karte_bauen
    teile, namen = [], []
    for art in ('gras', 'sand', 'wasser', 'meer'):
        for v in range(5):
            teile.append(Image.open(os.path.join(basis, '%s_%d.png' % (art, v))).convert('RGBA'))
            namen.append('%s_%d' % (art, v))
    for s in ('gras_weg', 'wasser_gras', 'wasser_sand', 'meer_sand', 'meer_wasser'):
        st = karte_bauen.lade_set(s)
        if not st:
            continue
        for t in st['tiles']:
            teile.append(t['img'].resize((T, T), Image.NEAREST) if t['img'].size != (T, T) else t['img'])
            namen.append('%s:%s' % (s, t['name']))
    spalten = 16
    zeilen = (len(teile) + spalten - 1) // spalten
    im = Image.new('RGBA', (spalten * T, zeilen * T), (0, 0, 0, 0))
    eintraege = []
    for i, t in enumerate(teile):
        x, y = (i % spalten) * T, (i // spalten) * T
        im.paste(t, (x, y))
        eintraege.append({'name': namen[i], 'x': x, 'y': y})
    im.save(os.path.join(OUT, 'bausteine.png'))
    im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(os.path.join(OUT, 'bausteine_vorschau_3x.png'))
    json.dump({'tile_size': T, 'kacheln': eintraege}, open(os.path.join(OUT, 'bausteine.json'), 'w'), indent=1)
    return len(teile)


def tmx(cols, rows, boden_raster, oben_raster, koll, n_boden, n_oben, groessen):
    def csv(raster, first):
        zeilen = []
        for r in raster:
            zeilen.append(','.join(str(v + first - 1) if v else '0' for v in r))
        return ',\n'.join(zeilen)
    g_b, g_o, g_k = 1, 1 + n_boden, 1 + n_boden + n_oben
    kr = np.array([[int(c) for c in r] for r in koll])
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" orientation="orthogonal" renderorder="right-down" width="{cols}" height="{rows}" tilewidth="{T}" tileheight="{T}" infinite="0" nextlayerid="5" nextobjectid="1">
 <tileset firstgid="{g_b}" name="boden" tilewidth="{T}" tileheight="{T}" tilecount="{n_boden}" columns="{SPALTEN}">
  <image source="boden_tiles.png" width="{groessen[0][0]}" height="{groessen[0][1]}"/>
 </tileset>
 <tileset firstgid="{g_o}" name="ueberlagerung" tilewidth="{T}" tileheight="{T}" tilecount="{n_oben}" columns="{SPALTEN}">
  <image source="ueberlagerung_tiles.png" width="{groessen[1][0]}" height="{groessen[1][1]}"/>
 </tileset>
 <tileset firstgid="{g_k}" name="kollision" tilewidth="{T}" tileheight="{T}" tilecount="3" columns="3">
  <image source="kollision_tiles.png" width="{3 * T}" height="{T}"/>
 </tileset>
 <layer id="1" name="Boden" width="{cols}" height="{rows}">
  <data encoding="csv">
{csv(boden_raster, g_b)}
</data>
 </layer>
 <objectgroup id="2" name="Spieler"/>
 <layer id="3" name="Ueberlagerung" width="{cols}" height="{rows}">
  <data encoding="csv">
{csv(oben_raster, g_o)}
</data>
 </layer>
 <layer id="4" name="Kollision" width="{cols}" height="{rows}" opacity="0.45" visible="0">
  <data encoding="csv">
{csv(kr, g_k)}
</data>
 </layer>
</map>
'''


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    n_bau = bausteine()
    boden = Image.open(os.path.join(EBENEN, 'ebene1_boden.png'))
    oben = Image.open(os.path.join(EBENEN, 'ebene3_ueberlagerung.png'))
    kb, rb = zerlegen(boden)
    ko, ro = zerlegen(oben)
    g1 = atlas(kb, os.path.join(OUT, 'boden_tiles.png'))
    g2 = atlas(ko, os.path.join(OUT, 'ueberlagerung_tiles.png'))
    k = Image.new('RGBA', (3 * T, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(k)
    for i, c in enumerate(((60, 200, 90, 160), (230, 40, 40, 200), (40, 110, 255, 180))):
        d.rectangle((i * T, 0, i * T + T - 1, T - 1), fill=c)
    k.save(os.path.join(OUT, 'kollision_tiles.png'))
    koll = json.load(open(os.path.join(EBENEN, 'kollision.json')))['raster']
    rows, cols = rb.shape
    open(os.path.join(OUT, 'karte01.tmx'), 'w').write(tmx(cols, rows, rb, ro, koll, len(kb), len(ko), (g1, g2)))
    json.dump({'tile_size': T, 'cols': cols, 'rows': rows,
               'hinweis': 'Index 0 = leer, sonst Kachelnummer+1 im jeweiligen Atlas (64 Kacheln je Zeile)',
               'boden': rb.tolist(), 'ueberlagerung': ro.tolist(),
               'kollision': koll, 'kollision_legende': {'1': 'begehbar', '2': 'gesperrt', '3': 'begehbar, verdeckt'}},
              open(os.path.join(OUT, 'karte01_raster.json'), 'w'))
    # Kontrolle: aus Atlas + Raster wieder zusammengesetzt == Ebene
    for kach, rast, ref in ((kb, rb, boden), (ko, ro, oben)):
        neu = np.zeros((rows * T, cols * T, 4), np.uint8)
        for y in range(rows):
            for x in range(cols):
                if rast[y, x]:
                    neu[y * T:(y + 1) * T, x * T:(x + 1) * T] = kach[rast[y, x] - 1]
        assert (neu == np.array(ref.convert('RGBA'))).all(), 'Rekonstruktion weicht ab'
    # Objekt-Sprites
    od = os.path.join(OUT, 'objekte')
    os.makedirs(od)
    gesehen = set()
    for o in json.load(open(os.path.join(OBJ, 'platzierung.json'))):
        if o['basis'] in gesehen:
            continue
        gesehen.add(o['basis'])
        quelle = os.path.join(OBJ, o['basis'] + '.png') if os.path.exists(os.path.join(OBJ, o['basis'] + '.png')) else os.path.join(OBJ, o['datei'])
        shutil.copy(quelle, os.path.join(od, o['basis'].replace('/', '_') + '.png'))
    open(os.path.join(OUT, 'README.md'), 'w').write(f'''# Karte 01 – Tileset

16 × 16 px, Karte {cols} × {rows} Kacheln.

| Datei | Inhalt |
|---|---|
| `bausteine.png` / `.json` | {n_bau} Grundkacheln: Gras, Sand, Wasser, Meer (je 5 Varianten) und die Wang-Übergänge |
| `boden_tiles.png` | {len(kb)} Kacheln der Boden-Ebene (unter dem Spieler), 64 je Zeile |
| `ueberlagerung_tiles.png` | {len(ko)} Kacheln der Überlagerung (über dem Spieler), 64 je Zeile |
| `kollision_tiles.png` | 3 Kacheln: grün begehbar, rot gesperrt, blau verdeckt |
| `karte01.tmx` | Tiled-Karte: Boden → Spieler (Objektebene) → Überlagerung, dazu Kollision (ausgeblendet) |
| `karte01_raster.json` | dieselben Raster als Listen (0 = leer, sonst Index + 1) |
| `objekte/` | {len(gesehen)} Objekt-Sprites einzeln |

Boden und Überlagerung sind ein exakter Export der fertigen Karte: Atlas + Raster ergeben Pixel für Pixel
`ebenen/ebene1_boden.png` und `ebenen/ebene3_ueberlagerung.png`. Weil Schatten, Kiesel, Gras, Wasserdetails
und Felsen gemalt sind, sind viele Kacheln Unikate. Animationen (Wasser, Wind, Laternen) sind nicht enthalten,
dafür gibt es `animation/`.
''')
    z = os.path.join(KARTE, 'karte01_tileset.zip')
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for wurzel, _, dateien in os.walk(OUT):
            for f in dateien:
                p = os.path.join(wurzel, f)
                zf.write(p, os.path.relpath(p, OUT))
    print('Bausteine %d, Boden %d, Ueberlagerung %d, Objekte %d -> %s' % (n_bau, len(kb), len(ko), len(gesehen), z))


if __name__ == '__main__':
    main()
