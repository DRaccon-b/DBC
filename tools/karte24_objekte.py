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

def ohne_gleis(sp):
    """Loren-Sprite ohne das eingebaute Gleisstueck: nur Wagen und Raeder bleiben (Gleis kommt aus der Karte)."""
    a = np.array(sp)
    a[38:] = 0                                                   # Schiene und Schwellen unter den Raedern
    a[26:, :5] = 0; a[26:, 37:] = 0                              # seitliche Schwellenpfosten
    return Image.fromarray(a)

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
    (OBELISK_LIEGT, 43.5, 22, {'liegend': True, 'hinter_fels': True}),   # eine Kachel tiefer, Fels liegt darueber
    (NADEL, 27.5, 8, {}), (NADEL, 16, 13, {}), (NADEL, 45, 11, {}),           # weniger rote Steine (Nutzer)
    (TOTBAUM, 31, 12, {}), (TOTBAUM, 38, 20, {'spiegeln': True}),
    (BROCKEN, 21, 10, {}),
    (KNOCHEN, 21, 7, {'liegend': True}), (KNOCHEN, 15, 17, {'liegend': True}), (KNOCHEN, 23, 17, {'liegend': True}),
    (KNOCHEN, 43, 18, {'liegend': True}), (SCHAEDEL2, 35.5, 10, {}),
    (GRAS, 9, 9, {}), (GRAS, 34, 7, {}), (GRAS, 43, 8, {}), (GRAS, 19.5, 17, {}), (GRAS, 50, 20, {}),
]
THRON, BANNER, PULT = 'schrein/00', 'schrein/01', 'schrein/02'
AX = 70 * T                                                     # Achse des Schreins (Mitte der Treppe)
def _p(name, dx, reihe, opt=None):                              # Paar spiegelsymmetrisch zur Achse
    o = dict(opt or {})
    return [(name, (AX - dx) / T, reihe, dict(o, px=AX - dx)), (name, (AX + dx) / T, reihe, dict(o, px=AX + dx, spiegeln=True))]
SCHREIN_OBJ = (
    [(THRON, AX / T, 10, {'px': AX})]                           # Thron oben auf der Achse
    + _p(BANNER, 96, 12, {'anim': 'fahne'}) + _p(BANNER, 96, 16, {'anim': 'fahne'})
    + _p(LATERNE, 40, 19, {'anim': 'lampe'})                    # Laternen links und rechts der Treppe
    + [(PULT, 75, 9, {}), (SAECKE, 65, 9, {})]
)
AXA = 49 * T                                                   # Achse der Arena (Mitte der runden Flaeche)
def _pa(name, dx, reihe, opt=None):
    o = dict(opt or {})
    return [(name, (AXA - dx) / T, reihe, dict(o, px=AXA - dx)), (name, (AXA + dx) / T, reihe, dict(o, px=AXA + dx, spiegeln=True))]
ARENA_OBJ = (                                                   # reduziert (Nutzer): Tuerme, je ein Banner und eine Laterne
    _pa(OBELISK, 128, 37)                                       # zwei Obelisken oben, spiegelsymmetrisch
    + _pa(LATERNE, 80, 35, {'anim': 'lampe'})                   # Laternen neben den Obelisken
    + _pa(BANNER, 160, 41, {'anim': 'fahne'})                   # Banner an den Seiten
)
GOLD, RUBIN, SAPHIR = 'loren/00', 'loren/01', 'loren/02'
GL = 75                                                         # Gleisreihe (layout 'gleis')
LOREN = [(GOLD, 79.5, GL, {'px': 79 * T + 8, 'dy': -5, 'auf_gleis': True}),        # drei Loren hintereinander, rechts
         (RUBIN, 81.6, GL, {'px': 81 * T + 10, 'dy': -5, 'auf_gleis': True}),       # wie in der Vorlage
         (SAPHIR, 83.7, GL, {'px': 83 * T + 12, 'dy': -5, 'auf_gleis': True})]
UNTEN_LINKS = UNTEN_LINKS + LOREN + OBEN + SCHREIN_OBJ + ARENA_OBJ


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
            if name.startswith('loren/'):
                sp = ohne_gleis(sp)
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
        if 'px' in opt:                                              # pixelgenaue Mitte (Symmetrie zur Schreinachse)
            x = opt.pop('px') - (ux0 + bw // 2)
        y = (ty + 1) * T - 1 - uy1 + opt.pop('dy', 0)
        fuss_y = y + uy1
        if not opt.get('hinter_fels') and (lvl[fuss_y, x + ux0 + bw // 2] not in (1, 2) or wand[fuss_y - 2:fuss_y + 1, x + ux0:x + ux1 + 1].any()):
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
