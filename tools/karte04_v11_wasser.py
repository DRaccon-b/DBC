"""Karte 04 v1.1 - Wasser wie Karte 01 / Freezeland: groessere, runde Teiche mit zwei tieferen Stufen,
Felsen und Algen (wasser_vertieft + wasser_details).

  python3 tools/karte04_v11_wasser.py          # nach regeln_v11.py karte04 wege, vor karte04_bauen.py
  python3 tools/karte04_v11_wasser.py objekte  # nach regeln_v11.py karte04: Objekte mit Fuss auf/an der Ufermauer weg

Die Teiche der Vorlage (11x5 und 7x5 Kacheln) sind zu klein fuer Tiefenstufen. Sie werden als Ellipsen
vergroessert (nur auf Savanne/Erde, nie auf Wegen), ringsum bleibt der graue Uferboden (m).
"""
import json, os
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
LAY = os.path.join(ROOT, 'maps', 'karte04', 'layout.json')
# (Mitte x, Mitte y, Halbachse x, Halbachse y) in Kacheln
TEICHE = [(31.3, 34.0, 6.3, 3.9), (23.5, 67.0, 5.8, 4.2)]


def main():
    lay = json.load(open(LAY))
    g = np.array([list(r) for r in lay['klassen']])
    rows, cols = g.shape
    yy, xx = np.mgrid[0:rows, 0:cols] + 0.5
    n = 0
    for (cx, cy, rx, ry) in TEICHE:
        d = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2
        frei = np.isin(g, ['s', 'd', 'm', 'x'])
        teich = (d <= 1) & frei
        ring = (((xx - cx) / (rx + 1.6)) ** 2 + ((yy - cy) / (ry + 1.4)) ** 2 <= 1) & ~teich & np.isin(g, ['s', 'd'])
        n += int((teich & (g != 'x')).sum())
        g[teich] = 'x'
        g[ring] = 'm'
    lay['klassen'] = [''.join(r) for r in g]
    json.dump(lay, open(LAY, 'w'))
    print('Teiche vergroessert: %d neue Wasserkacheln' % n)


def objekte():
    """Wandregel am Teich: kein Objekt steht mit seinem Fuss im Wasser oder direkt auf der Nord-Ufermauer."""
    pf = os.path.join(ROOT, 'assets', 'objekte', 'karte04', 'platzierung.json')
    objs = json.load(open(pf))
    g = json.load(open(LAY))['klassen']
    rows, cols = len(g), len(g[0])

    def am_teich(o):
        bx, by, wt, ht = o['block']
        fy = by + ht - 1
        return any(0 <= y < rows and 0 <= x < cols and g[y][x] == 'x' and not (40 <= x <= 70)
                   for x in range(bx, bx + wt) for y in (fy, fy + 1))
    rest = [o for o in objs if not am_teich(o)]
    json.dump(rest, open(pf, 'w'), indent=0)
    print('Teichufer: %d Objekte mit Fuss an der Ufermauer entfernt' % (len(objs) - len(rest)))


if __name__ == '__main__':
    import sys
    objekte() if sys.argv[1:] == ['objekte'] else main()
