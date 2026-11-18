"""Karte 54 - D-Reaper Kernel (A03 Nr. 21, letzte Bossarena von A03): Kachelraster -> maps/karte54/layout.json

  python3 tools/karte54_layout.py && python3 tools/karte54_bauen.py

Neu (Nutzer): Die Arena liegt IM INNEREN der Kernkugel des D-Reaper - bewusst anders als die Plattformen der anderen
Bossmaps. Der Kartenrand ist die gewoelbte Innenwand der Kugel aus Blasenhaufen (Karte 52, Originalgroesse), der Boden eine
rosa, durchscheinende Membran mit Zellen und pulsierenden Adern. Durch duenne Stellen der Membran (Fenster, gesperrt) sieht
man tief unten Shinjuku (Karte 52). Zugang im Sueden durch einen Riss in der Kugelwand zum Teleporter. Die Mitte bleibt frei
(Nutzer: der Boss ist beim Betreten schon da). Alle Bodenkanten am 45-Grad-Raster (Kachelmaske weichgezeichnet).

Klassen:  o Kugelwand (Blasen, gesperrt)  i Membran  f Fenster nach Shinjuku (Leere)  p Riss/Zugang (Membran)
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte54')
T, C, R = 16, 44, 44
MX, MY = 22, 21                                # Kugelmitte (Kachelkante)
RADIUS = 18.6                                  # Innenradius der Kugel in Kacheln
# Fenster als unregelmaessige Loecher (Mitte in Kacheln, Halbachsen, Zacken) - paarweise gespiegelt zur Achse MX,
# dazu eines im Norden auf der Achse; am 45-Grad-Raster durch die Kachelmaske
FENSTER = [(22.0, 7.6, 3.4, 1.9, 1), (10.4, 18.6, 2.9, 2.4, 2), (33.6, 18.6, 2.9, 2.4, 2), (12.8, 29.2, 2.2, 1.7, 3),
           (31.2, 29.2, 2.2, 1.7, 3)]


def main():
    yy, xx = np.mgrid[0:R, 0:C]
    d = np.hypot(xx + 0.5 - MX, yy + 0.5 - MY)
    k = np.where(d < RADIUS, 'i', 'o')
    for (cx, cy, rx, ry, z) in FENSTER:
        w = np.arctan2(yy + 0.5 - cy, (xx + 0.5 - cx) * (1 if cx <= MX else -1))      # gespiegelte Zacken
        rr = 1.0 + 0.16 * np.sin(3 * w + z) + 0.08 * np.sin(5 * w + 2 * z)
        k[((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2 < rr ** 2] = 'f'
    for _ in range(3):                                     # keine 1-Kachel-Zipfel/-Kerben an den Fenstern (Pruefliste)
        f_ = k == 'f'
        p_ = np.pad(f_, 1)
        nb = p_[:-2, 1:-1].astype(int) + p_[2:, 1:-1] + p_[1:-1, :-2] + p_[1:-1, 2:]
        k[f_ & (nb <= 1)] = 'i'
        k[~f_ & (k == 'i') & (nb >= 3)] = 'f'
    k[(yy >= 36) & (xx >= 20) & (xx <= 23)] = 'p'          # Riss in der Kugelwand nach Sueden (Stegbreite 4)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'mitte': [MX, MY], 'radius': RADIUS,
           'teleporter': [{'x': 20, 'y': 41, 'b': 4, 'h': 3}],
           # Blick hinunter: Ausschnitt von Karte 52 (halber Massstab) je Fenster, linke obere Pixelecke in der Quelle
           'blick': {'karte': 'karte52', 'versatz': [[205, 298], [36, 40], [688, 150], [108, 528], [606, 470]]}}
    os.makedirs(KARTE, exist_ok=True)
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'o': (150, 20, 40), 'i': (200, 110, 140), 'f': (60, 70, 90), 'p': (170, 90, 120)}
    out = np.zeros((R, C, 3), np.uint8)
    for kk, c in F.items():
        out[k == kk] = c
    Image.fromarray(out).resize((C * 8, R * 8), 0).save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 54 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
