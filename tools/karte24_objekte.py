"""Objekte fuer Karte 24 (The Kaiser's Canyon, A02) - Platzierung am 16x16-Raster nach der Vorlage.

  python3 tools/karte24_bauen.py   (einmal -> wand.npy)
  python3 tools/karte24_objekte.py && python3 tools/karte24_bauen.py

Schritt 1: unten links (Lager mit Feuerstelle, Zelte, zwei Gefangenen-Pferche mit Eisenzaun und Kaefigen, Obelisken,
Laternen, Erzkristalle, Kleinkram). Neue Objekte: PixelLab k24_lager, k24_obelisk. Der Eisenzaun wird in
karte24_bauen.py gezeichnet (Rechtecke in ZAEUNE).
Kein Bodenfuss (der Canyonboden ist rot, die Bodenfuss-Varianten sind fuer Gras/Sand).
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from karte04_objekte import saeubern


def ohne_runen(sp):
    """Obelisk ohne leuchtende Schrift (Nutzer): rosa/lila Pixel durch den dunklen Stein daneben ersetzen."""
    a = np.array(sp).astype(np.int16)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    run = (al > 0) & (r > g + 40) & (r > 110)
    stein = (al > 0) & ~run
    for _ in range(6):
        ys, xs = np.nonzero(run)
        for y, x in zip(ys, xs):
            nb = [(y + dy, x + dx) for dy, dx in ((0, -1), (0, 1), (-1, 0), (1, 0))
                  if 0 <= y + dy < a.shape[0] and 0 <= x + dx < a.shape[1] and stein[y + dy, x + dx]]
            if nb:
                a[y, x, :3] = a[nb[0]][:3]; run[y, x] = False; stein[y, x] = True
    return Image.fromarray(a.astype(np.uint8))

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte24')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte24')
T = 16
ZELT, KAEFIG, FEUER, ERZ, LATERNE, HOCKER = 'lager/00', 'lager/01', 'lager/02', 'lager/03', 'lager/04', 'lager/05'
KISTEN, SAECKE, DORN, SCHAEDEL, SCHILD, OBELISK = 'lager/08', 'lager/10', 'lager/11', 'lager/14', 'lager/15', 'obelisk2/00'
# Eisenzaun der Pferche: (x0, y0, x1, y1, offene Seiten) - nach der Vorlage, Pferch A links, Pferch B rechts
ZAEUNE = [(9, 68, 18, 73, 'unten_rechts'), (28, 68, 39, 73, 'unten_links')]   # ganz auf dem Canyonboden   # auf den freien Boden verschoben
# (sprite, Kachel-x der Fussmitte, Fusszeile, Optionen) - Anordnung nach der Vorlage, auf unseren Canyonboden gelegt
UNTEN_LINKS = [
    # Lager oben links: Feuerstelle mit Hockern, Kisten und Saecke
    (FEUER, 9, 49, {'anim': 'feuer'}),
    (HOCKER, 6.5, 48, {}), (HOCKER, 11.5, 48, {}), (HOCKER, 6.5, 51, {}), (HOCKER, 11.5, 51, {}),
    (KISTEN, 13.5, 54, {}), (SAECKE, 14.5, 47, {}), (ERZ, 5.5, 54, {}),
    # Zelte
    (ZELT, 7.5, 56, {}), (ZELT, 11.5, 61, {'spiegeln': True}), (FEUER, 7.5, 59, {'anim': 'feuer'}),
    # Pferch A (links) und Pferch B (rechts): Kaefige, Laternen
    (KAEFIG, 11.5, 71, {}), (KAEFIG, 15, 71, {}),
    (KAEFIG, 31.5, 71, {}), (KAEFIG, 35, 71, {'spiegeln': True}),
    (LATERNE, 20, 72, {'anim': 'lampe'}), (LATERNE, 38, 71, {'anim': 'lampe'}),
    (ERZ, 10.5, 66, {'spiegeln': True}),
    # Obelisken auf dem Sandplatz zwischen den Pferchen
    (OBELISK, 21.5, 74, {}), (OBELISK, 42.5, 73, {}),
    # unten: Zelte und Feuerstellen
    (ZELT, 27.5, 79, {}), (FEUER, 31, 79, {'anim': 'feuer'}), (ZELT, 13.5, 79, {'spiegeln': True}),
    (FEUER, 17, 80, {'anim': 'feuer'}),
    # Kleinkram (sparsam)
    (SCHAEDEL, 23, 80, {}), (DORN, 5.5, 73, {}), (SCHILD, 21, 46, {}),
]


NADEL, TOTBAUM, KNOCHEN, BROCKEN, GRAS, LORE, SCHAEDEL2 = 'oben/00', 'oben/01', 'oben/02', 'oben/03', 'oben/04', 'oben/07', 'oben/12'
OBELISK_LIEGT = 'obelisk_liegend/00'
OBEN = [                                                        # oberer Canyon nach der Vorlage (sparsam verteilt)
    (OBELISK, 10.5, 18, {}), (OBELISK, 27.5, 18, {}),              # zwei stehende Obelisken
    (OBELISK_LIEGT, 43.5, 21, {'liegend': True}),                 # umgestuerzter Obelisk unten rechts
    (NADEL, 10.5, 8, {}), (NADEL, 27.5, 8, {}), (NADEL, 39, 7, {}), (NADEL, 16, 13, {}), (NADEL, 13, 16, {}),
    (NADEL, 33.5, 14, {}), (NADEL, 45, 11, {}),
    (TOTBAUM, 31, 12, {}), (TOTBAUM, 38, 20, {'spiegeln': True}),
    (BROCKEN, 21, 10, {}), (BROCKEN, 15, 18, {}), (BROCKEN, 45, 19, {}),
    (KNOCHEN, 21, 6, {'liegend': True}), (KNOCHEN, 15, 17, {'liegend': True}), (KNOCHEN, 23, 17, {'liegend': True}),
    (KNOCHEN, 43, 18, {'liegend': True}), (SCHAEDEL2, 35.5, 10, {}),
    (GRAS, 9, 9, {}), (GRAS, 34, 7, {}), (GRAS, 43, 8, {}), (GRAS, 19.5, 17, {}), (GRAS, 50, 20, {}),
]
UNTEN_LINKS = UNTEN_LINKS + OBEN


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    objekte, cache = [], {}
    for (name, fx, fy, opt) in UNTEN_LINKS:
        opt = dict(opt)
        spiegeln = opt.pop('spiegeln', False)
        key = (name, spiegeln)
        if key not in cache:
            sp = saeubern(Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA'))   # PixelLab-Splitter weg
            if name == OBELISK:
                sp = ohne_runen(sp)
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            datei = 'varianten/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            sp.save(os.path.join(OBJ, datei))
            a = np.array(sp.getchannel('A')) > 0
            ys, xs = np.nonzero(a)
            cache[key] = (datei, sp.height, int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
        datei, h, ux0, uy0, ux1, uy1 = cache[key]
        bw = ux1 - ux0 + 1
        wt = math.ceil(bw / T)
        tx, ty = int(math.floor(fx)), int(fy)
        bx = int(round(fx + 0.5 - wt / 2.0))
        x = bx * T + (wt * T - bw) // 2 - ux0
        y = (ty + 1) * T - 1 - uy1
        fuss_y = y + uy1
        if lvl[fuss_y, x + ux0 + bw // 2] != 1 or wand[fuss_y - 2:fuss_y + 1, x + ux0:x + ux1 + 1].any():
            print('  uebersprungen (nicht auf dem Canyonboden):', name, fx, fy)
            continue
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [tx, ty],
             'block': [bx, ty - math.ceil((uy1 - uy0 + 1) / T) + 1, wt, math.ceil((uy1 - uy0 + 1) / T)],
             'ebene': 1, 'an_wand': True}
        o.update(opt)
        objekte.append(o)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    json.dump(ZAEUNE, open(os.path.join(OBJ, 'zaeune.json'), 'w'))
    print('Karte 24: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
