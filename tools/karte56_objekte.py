"""Objekte fuer Karte 56 (Golden Digimentals) -> assets/objekte/karte56/platzierung.json

  python3 tools/karte56_objekte.py && python3 tools/karte56_bauen.py

PixelLab (Objekt-Creator): k56_wiese, k56_verzerrt, k56_innen (48 px), k56_blumen (32 px, als Bodentextur gestempelt).
Raum 2 ist dieselbe Wiese wie Raum 1 - jedes Objekt steht an derselben Stelle als verzerrtes Gegenstueck (faellt
weg, wenn sein Fuss auf einem Riss laege). Raum 3: dunkle Kugeln schweben (Erinnerungsblasen entfernt, Nutzer) (ohne Schatten),
Laternenpaar spiegelsymmetrisch zur Ringmarke, Kristalle an den Abgruenden.
Guertel: Kronen ganz auf Guertelkacheln, Luecken mit Bueschen geschlossen (wie Karte 55).
Kampfflaeche um die Ringmarke bleibt frei.
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'assets', 'objekte')
OBJ = os.path.join(SRC, 'karte56')
LAYOUT = os.path.join(ROOT, 'maps', 'karte56', 'layout.json')
T = 16

# (Wiese, verzerrt, x, Fussreihe, Breite, Extra) - Raumkoordinaten; Paare Raum 1 / Raum 2
WIESE = [
    ('wiese/01', 'verzerrt/00', 7, 8, 3, {}),                      # Weide am See / toter Baum
    ('wiese/02', 'verzerrt/15', 12, 9, 2, {}),                     # Schilf am Ufer / violetter Farn
    ('wiese/02', 'verzerrt/15', 23, 8, 2, {'spiegeln': True}),
    ('wiese/11', 'verzerrt/07', 4, 12, 3, {}),                     # Birke (hinten) / toter Stumpfbaum
    ('wiese/00', 'verzerrt/04', 1, 13, 3, {}),                     # Sommerbaum / Pixel-Glitch-Baum
    ('wiese/04', 'verzerrt/03', 1, 14, 3, {}),                     # Moosfels vor dem Stumpf (5d) / Fels mit Adern
    ('wiese/03', 'verzerrt/01', 24, 12, 3, {}),                    # Bluetenbusch / verwelkter Busch
    ('wiese/05', 'verzerrt/05', 20, 21, 2, {}),                    # Sonnenblumen / verwelkte Sonnenblume
    ('wiese/10', 'verzerrt/06', 10, 22, 3, {}),                    # Blumenbusch / Dornbusch
    ('wiese/08', 'verzerrt/02', 16, 21, 3, {'liegend': True}),     # liegender Stamm / Kristallsplitter
]
INNEN = [
    ('innen/05', 13, 7, 3, {}),                                    # Runensockel hinter der Ringmarke (Achse)
    ('innen/10', 10, 7, 1, {}),                                    # Laternenpaar, gespiegelt zur Achse x = 14,5
    ('innen/10', 18, 7, 1, {'spiegeln': True}),
    ('innen/00', 6, 5, 2, {}),                                     # Kristalle an den Abgruenden
    ('innen/00', 20, 5, 2, {'spiegeln': True}),
    ('innen/00', 20, 21, 2, {}),
    ('innen/12', 16, 20, 3, {'liegend': True}),                    # Knochen
    ('innen/03', 5, 15, 2, {'schweben': True}),                    # dunkle Kugeln (schweben)
    ('innen/03', 24, 14, 2, {'schweben': True}),
]
WALD = {'h': ['wiese/00', 'wiese/11', 'karte35/varianten/k01-baum00', 'karte35/varianten/k01-baum01',
              'karte35/varianten/k01-baum04', 'karte35/varianten/k01-baum15'],
        'u': ['verzerrt/00', 'verzerrt/04', 'verzerrt/07', 'verzerrt/00'],
        'k': ['innen/01', 'innen/02', 'innen/08', 'innen/01']}
BUSCH = {'h': ['wiese/03', 'wiese/10', 'karte35/varianten/k01-baum12', 'karte35/varianten/k01-baum13'],
         'u': ['verzerrt/06', 'verzerrt/01', 'verzerrt/15'],
         'k': ['innen/06', 'innen/00', 'innen/09']}


def sprite(quelle, spiegeln=False):
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
    pfad = os.path.join(SRC, quelle + '.png') if quelle.startswith('karte') else os.path.join(OBJ, quelle + '.png')
    ziel = 'varianten/%s%s.png' % (quelle.replace('karte35/varianten/', '').replace('/', '-'), '_m' if spiegeln else '')
    if not os.path.exists(os.path.join(OBJ, ziel)):
        im = Image.open(pfad).convert('RGBA')
        im = im.crop(im.getbbox())
        if spiegeln:
            im = im.transpose(Image.FLIP_LEFT_RIGHT)
        im.save(os.path.join(OBJ, ziel))
    return ziel


def setzen(datei, tx, ty, breite=None, **extra):
    """Fuss auf Kachelreihe ty, waagerecht mittig im Block ab Spalte tx (Regel 1b)."""
    w, h = Image.open(os.path.join(OBJ, datei)).size
    b = breite or max(1, -(-w // T))
    o = {'datei': datei, 'basis': 'k56/' + os.path.basename(datei)[:-4], 'x': int(tx * T + (b * T - w) // 2),
         'y': int((ty + 1) * T - h), 'fuss': h - 1, 'kachel': [tx, ty], 'ebene': 2}
    if extra.pop('schweben', False):                              # schwebend: kein Schatten, 6 px ueber dem Boden
        o.update(schattenlos=True, ohne_wall=True)
        o['y'] -= 6
    o.update(extra)
    return o


def rechteck(o):
    w, h = Image.open(os.path.join(OBJ, o['datei'])).size
    return o['x'], o['y'], o['x'] + w, o['y'] + h


def frei(r, liste):
    return all(r[2] + 2 <= s[0] or s[2] + 2 <= r[0] or r[3] + 2 <= s[1] or s[3] + 2 <= r[1] for s in map(rechteck, liste))


def main():
    lay = json.load(open(LAYOUT))
    kl = np.array([list(r) for r in lay['klassen']])
    rows, cols = kl.shape
    L = []
    (x1, y1), (x2, y2), (x3, y3) = lay['raeume']
    for (w, v, tx, ty, b, ex) in WIESE:
        ex = dict(ex)
        sp = ex.pop('spiegeln', False)
        L.append(setzen(sprite(w, sp), x1 + tx, y1 + ty, b, **ex))
        if all(kl[y2 + ty, x2 + tx + i] not in 'RD' for i in range(b)):
            L.append(setzen(sprite(v, sp), x2 + tx, y2 + ty, b, **ex))
        else:
            print('Raum 2: faellt weg (Riss):', v, tx, ty)
    for (q, tx, ty, b, ex) in INNEN:
        ex = dict(ex)
        sp = ex.pop('spiegeln', False)
        L.append(setzen(sprite(q, sp), x3 + tx, y3 + ty, b, **ex))
    # ---------------------------------------------------------------- Guertel
    rs = np.random.RandomState(5657)
    deck = np.zeros((rows * T, cols * T), bool)
    fremd = list(L)

    def versuch(quelle, tx, ty, anim):
        o = setzen(sprite(quelle, bool(rs.randint(2))), tx, ty, 1, anim=anim)
        r = rechteck(o)
        if r[0] < 0 or r[1] < 0 or r[2] > cols * T or r[3] > rows * T:
            return None
        if any(kl[y, x] not in 'huk' for y in range(r[1] // T, (r[3] - 1) // T + 1)
               for x in range(r[0] // T, (r[2] - 1) // T + 1)):
            return None
        if not frei(r, fremd):
            return None
        L.append(o)
        deck[r[1]:r[3], r[0]:r[2]] = True
        return r
    nb = nbu = 0
    for ty in range(rows):
        for tx in range(cols):
            g = kl[ty, tx]
            if g in 'huk' and (tx + ty) % 2 == 0:
                nb += bool(versuch(WALD[g][rs.randint(len(WALD[g]))], tx, ty, 'baum'))
    for ty in range(rows):
        for tx in range(cols):
            g = kl[ty, tx]
            if g in 'huk' and deck[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].mean() < 0.7:
                nbu += bool(versuch(BUSCH[g][rs.randint(len(BUSCH[g]))], tx, ty, 'wehen'))
    json.dump(L, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 56: %d Objekte (Guertel %d Baeume, %d Buesche)' % (len(L), nb, nbu))


if __name__ == '__main__':
    main()
