"""Karte 01 v1.1 - Wege nach Regel 6: natuerliche Boegen und Diagonalen statt eckiger, gerader Wege.

  python3 tools/karte01_v11_wege.py      # liest terrain_grid_v1.0.json (Original), schreibt terrain_grid.json

Die Wegzellen (R = oberer Weg, P = unterer Weg) werden mit einem weichen, niederfrequenten Verschiebungsfeld
verbogen (Amplitude ~2 Kacheln) und danach geglaettet (runde Kurven, diagonale Abschnitte). An Treppen,
Bruecken, Klippen, Wasser und am Kartenrand laeuft die Verschiebung auf 0 aus - dort bleiben die Anschluesse
exakt erhalten. Wasser, Klippen, Bruecken, Strand und Teichufer werden nie veraendert.
"""
import json, os, shutil
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte01')
SUB = 4                     # Unterraster je Kachel fuer die Verformung


def glatt(feld, sigma):
    """Gauss-Glaettung fuer Felder im Bereich 0..1."""
    im = Image.fromarray((np.clip(feld, 0, 1) * 255).astype(np.uint8))
    return np.array(im.filter(ImageFilter.GaussianBlur(sigma))).astype(np.float32) / 255.0


def rauschen(rows, cols, zelle, seed):
    rs = np.random.RandomState(seed)
    n = rs.rand(rows // zelle + 3, cols // zelle + 3).astype(np.float32) * 2 - 1
    im = Image.fromarray(n, mode='F').resize(((cols // zelle + 3) * zelle * SUB, (rows // zelle + 3) * zelle * SUB),
                                             Image.BICUBIC)
    return np.array(im)[:rows * SUB, :cols * SUB]


def main():
    alt = os.path.join(KARTE, 'terrain_grid_v1.0.json')
    if not os.path.exists(alt):
        shutil.copy(os.path.join(KARTE, 'terrain_grid.json'), alt)
    d = json.load(open(alt))
    grid = [list(r) for r in d['grid']]
    rows, cols = len(grid), len(grid[0])
    plan = json.load(open(os.path.join(KARTE, 'hoehenplan.json')))
    g = np.array(grid)
    weg = np.isin(g, ['R', 'P'])
    fest = np.isin(g, ['W', 'B', 'C', 'D', 'h', 'S', 's', 'p'])          # nie veraendern
    # Anker: Treppen, Bruecken, Stege, Kartenrand -> keine Verschiebung
    anker = np.zeros((rows, cols), bool)
    tcol = {}
    for s in plan['segmente']:
        for vx in range(s['von'], s['bis'] + 1):
            tcol[vx] = (s['t'], s.get('h', 3))
    for tr in plan['treppen']:
        t, h = tcol[tr['x']]
        anker[max(0, t - h - 3):t + 4, max(0, tr['x'] - 2):tr['x'] + tr['breite'] + 2] = True
    for br in plan.get('bruecken', []) + plan.get('stege', []):
        anker[max(0, br['y'] - 3):br['y'] + br['hoehe'] + 3, max(0, br['x'] - 3):br['x'] + br['breite'] + 3] = True
    anker[:, :3] = anker[:, -3:] = True
    anker[:3, :] = anker[-3:, :] = True
    anker |= fest
    # Abstand zu Ankern (in Kacheln, grob) -> Gewicht der Verschiebung
    dist = np.full((rows, cols), 99.0)
    dist[anker] = 0
    for _ in range(8):
        dist = np.minimum(dist, np.minimum.reduce([np.roll(dist, 1, 0) + 1, np.roll(dist, -1, 0) + 1,
                                                   np.roll(dist, 1, 1) + 1, np.roll(dist, -1, 1) + 1]))
    gew = np.clip((dist - 1) / 5.0, 0, 1)
    gew_f = np.kron(gew, np.ones((SUB, SUB)))
    gew_f = glatt(gew_f, SUB * 1.5)
    # Verschiebungsfeld (Kacheln), niederfrequent
    A = 3.4
    dx = rauschen(rows, cols, 11, 3) * A * gew_f
    dy = rauschen(rows, cols, 11, 7) * A * gew_f
    m = np.kron(weg, np.ones((SUB, SUB))).astype(np.float32)
    H, W = m.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    sy = np.clip(np.round(yy + dy * SUB), 0, H - 1).astype(int)
    sx = np.clip(np.round(xx + dx * SUB), 0, W - 1).astype(int)
    verbogen = m[sy, sx]
    # runde Kurven: glaetten und schwellen
    verbogen = glatt(verbogen, SUB * 0.9) > 0.42
    # zurueck aufs Kachelraster (Mehrheit)
    neu = verbogen.reshape(rows, SUB, cols, SUB).mean(axis=(1, 3)) > 0.4
    # an Ankern exakt das Original
    neu[anker] = weg[anker]
    geaendert = 0
    for y in range(rows):
        for x in range(cols):
            if fest[y, x]:
                continue
            if neu[y, x] and not weg[y, x]:
                # Wegklasse vom naechsten Originalweg uebernehmen
                best, bd = 'P', 99
                for r in range(1, 6):
                    for yy_ in range(max(0, y - r), min(rows, y + r + 1)):
                        for xx_ in range(max(0, x - r), min(cols, x + r + 1)):
                            if grid[yy_][xx_] in 'RP' and abs(yy_ - y) + abs(xx_ - x) < bd:
                                best, bd = grid[yy_][xx_], abs(yy_ - y) + abs(xx_ - x)
                    if bd < 99:
                        break
                g[y, x] = best
                geaendert += 1
            elif not neu[y, x] and weg[y, x]:
                g[y, x] = 'G'
                geaendert += 1
    # Regel 2: an jeder Treppe ist der Weg oben und unten mindestens so breit wie die Treppe (+1 Kachel je Seite)
    for tr in plan['treppen']:
        t, h = tcol[tr['x']]
        for (y0, y1) in ((t - h - 3, t - h), (t + 1, t + 4)):
            klasse = [g[y, x] for y in range(y0, y1) for x in range(tr['x'], tr['x'] + tr['breite'])
                      if g[y, x] in ('R', 'P')]
            k = max(set(klasse), key=klasse.count) if klasse else 'P'
            for y in range(y0, y1):
                for x in range(tr['x'] - 1, tr['x'] + tr['breite'] + 1):
                    if 0 <= y < rows and not fest[y, x]:
                        g[y, x] = k
    d['grid'] = [''.join(r) for r in g]
    d['_v11'] = 'Wege nach Regel 6 gebogen (tools/karte01_v11_wege.py), Original: terrain_grid_v1.0.json'
    json.dump(d, open(os.path.join(KARTE, 'terrain_grid.json'), 'w'), indent=1)
    print('%d Wegzellen geaendert' % geaendert)
    # Kontrollbild: alt (links) / neu (rechts)
    farbe = {'R': (200, 160, 100), 'P': (220, 190, 130), 'W': (60, 110, 200), 'B': (120, 80, 40), 'C': (90, 90, 110),
             'F': (30, 100, 50), 'G': (90, 170, 80), 'D': (20, 50, 140), 'h': (80, 140, 200), 'S': (230, 210, 150),
             's': (240, 220, 170), 'p': (230, 200, 140)}
    bild = np.zeros((rows, cols * 2 + 2, 3), np.uint8)
    for y in range(rows):
        for x in range(cols):
            bild[y, x] = farbe.get(grid[y][x], (255, 0, 255))
            bild[y, cols + 2 + x] = farbe.get(g[y, x], (255, 0, 255))
    Image.fromarray(bild).resize(((cols * 2 + 2) * 4, rows * 4), Image.NEAREST).save(
        os.path.join(KARTE, 'v1.1', 'wege_vorher_nachher.png'))


if __name__ == '__main__':
    os.makedirs(os.path.join(KARTE, 'v1.1'), exist_ok=True)
    main()
