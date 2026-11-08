"""Karte 16 (The Network), Neuaufbau Schritt 1: Kachelraster nach der Vorlage -> maps/karte16/layout.json

  python3 tools/karte16_layout.py

Vorlage assets/vorlagen/karte16_vorlage.png: 1024x640 px = 64x40 Kacheln a 16 px (echtes 16er-Raster,
Plattenfugen alle 16 px gemessen). Netzwerkraum: eine flache Bodenflaeche, ringsum die Leere.

Klassen:  .  Leere (dunkler Datenraum)     b  Bodenplatten (60x36 Kacheln, x 2-61, y 2-37)
Marken (Vorlage, Kachelkoordinaten):
  tor      Firewall-Tor   x 30-32, y 5-6   (3x2)
  pfeile   Pfeilfeld oben x 30-32, y 7     (3x1, zeigt nach Norden zum Tor)
  start    Pfeilfeld unten x 30-33, y 35   (4x1, Eingang/Teleporter)
  item     Datenchip      x 35, y 9
"""
import json, os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte16')
VORLAGE = os.path.join(ROOT, 'assets', 'vorlagen', 'karte16_vorlage.png')
C, R, T = 64, 40, 16
MARKEN = {'tor': (30, 5, 3, 2), 'pfeile': (30, 7, 3, 1), 'start': (30, 35, 4, 1), 'item': (35, 9, 1, 1)}


def main():
    os.makedirs(KARTE, exist_ok=True)
    k = np.full((R, C), '.')
    k[2:38, 2:62] = 'b'
    json.dump({'spalten': C, 'zeilen': R, 'kachel': T, 'raster': [''.join(z) for z in k], 'marken': MARKEN},
              open(os.path.join(KARTE, 'layout.json'), 'w'), indent=1)
    # Kontrollbild: Vorlage mit Raster, Klassen und Marken
    im = Image.open(VORLAGE).convert('RGB')
    d = ImageDraw.Draw(im, 'RGBA')
    for y in range(R):
        for x in range(C):
            if k[y, x] == '.':
                d.rectangle((x * T, y * T, x * T + 15, y * T + 15), fill=(120, 0, 160, 50))
    for i in range(C + 1):
        d.line((i * T, 0, i * T, R * T), fill=(255, 255, 255, 40))
    for i in range(R + 1):
        d.line((0, i * T, C * T, i * T), fill=(255, 255, 255, 40))
    farben = {'tor': (255, 60, 60), 'pfeile': (60, 220, 255), 'start': (60, 255, 120), 'item': (255, 210, 60)}
    for n, (x, y, w, h) in MARKEN.items():
        d.rectangle((x * T, y * T, (x + w) * T - 1, (y + h) * T - 1), outline=farben[n] + (255,), width=2)
        d.text((x * T, (y + h) * T + 1), n, fill=farben[n] + (255,))
    im.resize((C * T * 2, R * T * 2), Image.NEAREST).save(os.path.join(KARTE, 'layout_vergleich.png'))
    print('Karte 16: %dx%d Kacheln, Boden %d Kacheln' % (C, R, int((k == 'b').sum())))


if __name__ == '__main__':
    main()
