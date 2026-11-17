# Grundgeruest aus karte49 (tools/neue_karte.py) - an die Vorlage von karte54 "D-Reaper Kernel" anpassen!
"""Karte 54 - The Broken Promise (A03 Nr. 16), Bossarena von Beelzemon, Layout nach der Vorlage -> maps/karte54/layout.json

  python3 tools/karte54_layout.py

Vorlage assets/vorlagen/karte54_vorlage.png (768x576 = 48x36 Kacheln), Kacheln wie Karte 47: graublauer Felsboden,
erhoehter heller Felsrand ringsum (gesperrt) mit Felsfronten nach Sueden, Pflasterflecken mit Felsbrocken, tote Baeume,
erhoehtes Plateau unten rechts mit Treppe, Teleporter unten links.

Klassen:  g Felsboden  w Pflaster  h Felsrand (Hoehe 1, gesperrt)  q Plateau (Hoehe 1, begehbar, Buehne des Bosses)
          t Treppe (Frontreihe)  T Teleporter
Korrekturen der Vorlage:
  - zwei halbe Treppen nebeneinander -> eine Steintreppe in voller Breite, davor/dahinter 2 Reihen frei
  - Teleporter lag halb im Felsrand -> Ausgang in Teleporterbreite durch den Rand, kein Kerben-Rest daneben
  - Plateau-Stufe (zwei Hoehen) und 1-Spalten-Kerben am Felsrand geglaettet, Plateau mit Felsrand-Textur abgesetzt
  - Felsrand und Plateau gleich hell in der Vorlage -> Plateau als begehbare Steinflaeche (andere Textur, eigene Ebene)
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw
import karte43_layout as k43

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte54')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte54_vorlage.png')
C, R, T = 48, 36, 16
REF = {'g': (101, 118, 138), 'h': (137, 151, 165), 'w': (128, 134, 136), 'k': (118, 125, 127)}
PLATEAU = (20, 25, 43, 29)               # Plateau unten rechts (x0, y0, x1, y1), Treppe in der Frontreihe darunter
TREPPE = (31, 34)                        # Treppenspalten (Vorlage: zwei halbe Treppen 31-32 und 33-34)
TELEPORTER = [(6, 33, 4, 3)]
k43.R, k43.C = R, C


def main():
    os.makedirs(KARTE, exist_ok=True)
    a = np.array(Image.open(VORLAGE).convert('RGB')).astype(int)
    M = np.median(a.reshape(R, T, C, T, 3).transpose(0, 2, 1, 3, 4).reshape(R, C, T * T, 3), 2)
    ks = list(REF)
    ref = np.array([REF[c] for c in ks], float)
    k = np.array(ks)[((M[:, :, None, :] - ref[None, None]) ** 2).sum(-1).argmin(-1)].astype('<U1')
    k[k == 'k'] = 'w'
    for teil in k43.flaechen(k == 'w'):                               # Einzelsteine/Zweige der Vorlage -> Boden
        if len(teil) < 4:
            for (y, x) in teil:
                k[y, x] = 'g'
    # Plateau: rechteckig auf einer Hoehe (Vorlage: zweistufig), Rand ringsum geschlossen
    x0, y0, x1, y1 = PLATEAU
    k[(k == 'h') & (np.arange(R)[:, None] >= y0 - 1) & (np.arange(C)[None, :] >= x0 - 1) & (np.arange(C)[None, :] <= x1 + 1)
      & (np.arange(R)[:, None] <= y1 + 1)] = 'g'
    k[y0:y1 + 1, x0 + 5:x1 + 1] = 'q'
    k[y0 + 2:y1 + 1, x0:x0 + 5] = 'q'
    k[0:3, :] = 'h'; k[-2:, :] = 'h'; k[:, 0:2] = 'h'; k[:, -2:] = 'h'
    k = k43.zipfel_weg(k, 'gwhq')
    for _ in range(3):
        for y in range(1, R - 1):                                     # 1-Spalten-Kerben/-Vorspruenge am Rand
            for x in range(1, C - 1):
                if k[y, x] != 'h' and k[y, x - 1] == 'h' and k[y, x + 1] == 'h':
                    k[y, x] = 'h'
                elif k[y, x] == 'h' and k[y, x - 1] not in 'h' and k[y, x + 1] not in 'h' and 2 <= x < C - 2:
                    k[y, x] = 'g'
                if k[y, x] == 'h' and k[y - 1, x] != 'h' and k[y + 1, x] != 'h' and 3 <= y < R - 2:
                    k[y, x] = 'g'
        for y in range(R - 1):                                        # Schachbrett-Ecken
            for x in range(C - 1):
                q = k[y:y + 2, x:x + 2]
                if q[0, 0] == q[1, 1] and q[0, 1] == q[1, 0] and q[0, 0] != q[0, 1]:
                    k[y + 1, x] = q[0, 0]
    # Treppe in voller Breite, 2 Reihen Boden davor, 2 Reihen Plateau dahinter
    ry = y1 + 1
    k[ry:ry + 3, TREPPE[0] - 1:TREPPE[1] + 2] = np.where(k[ry:ry + 3, TREPPE[0] - 1:TREPPE[1] + 2] == 'h', 'g',
                                                          k[ry:ry + 3, TREPPE[0] - 1:TREPPE[1] + 2])
    k[ry, TREPPE[0]:TREPPE[1] + 1] = 't'
    # Teleporter: Ausgang durch den unteren Rand in Teleporterbreite
    for (tx, ty, b, hh) in TELEPORTER:
        k[ty:R, tx:tx + b] = 'g'
        k[ty:ty + hh, tx:tx + b] = 'T'
        k[ty - 2:ty, tx:tx + b] = np.where(k[ty - 2:ty, tx:tx + b] == 'h', 'g', k[ty - 2:ty, tx:tx + b])
    h = np.isin(k, list('hq')).astype(int)
    lay = {'groesse': [C, R], 'klassen': [''.join(z) for z in k], 'hoehe': [''.join(str(c) for c in z) for z in h],
           'treppen': [[TREPPE[0], TREPPE[1], ry]], 'plateau': list(PLATEAU), 'bruecken': [], 'stege': [],
           'teleporter': [{'x': tx, 'y': ty, 'b': b, 'h': hh} for (tx, ty, b, hh) in TELEPORTER]}
    json.dump(lay, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=0)
    F = {'g': (101, 118, 138), 'w': (170, 170, 165), 'h': (190, 200, 215), 'q': (150, 130, 170), 't': (240, 170, 60),
         'T': (80, 220, 240)}
    S_ = 8
    im = Image.new('RGB', (C * S_, R * S_))
    dr = ImageDraw.Draw(im)
    for y in range(R):
        for x in range(C):
            dr.rectangle((x * S_, y * S_, x * S_ + S_ - 1, y * S_ + S_ - 1), fill=F[k[y, x]])
    vg = Image.open(VORLAGE).convert('RGB').resize((C * S_, R * S_))
    both = Image.new('RGB', (C * S_ * 2 + 8, R * S_))
    both.paste(vg, (0, 0)); both.paste(im, (C * S_ + 8, 0))
    both.save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 54 Layout %dx%d' % (C, R))


if __name__ == '__main__':
    main()
