"""Handgezeichnete, nahtlose 16x16-Grundkacheln (Gras, Sand) als Stilanker.

  python3 tools/basis_kacheln.py

Die Kacheln werden PixelLab als exakte Referenz (lower/upper_reference_image)
uebergeben, so dass alle generierten Uebergaenge genau dieses Gras/diesen Sand
verwenden. Stil: sauberer Handheld-RPG-Look, Hue-Shifting, klare Bueschel.
Ausgabe: assets/basis/*.png (+ vorschau_basis.png, 4x4 gekachelt, 4x)
"""
import os
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'basis')

PAL = {
    # Gras: Schatten ins Blaugruen, Licht ins Gelbgruen
    'g0': '#1f6b45', 'g1': '#2f8d47', 'g2': '#4aad4e', 'g3': '#62c456', 'g4': '#8ddc68', 'g5': '#c4f08c',
    # Sand: Schatten ins Rotbraun, Licht ins Cremige
    's0': '#a87850', 's1': '#cfa56c', 's2': '#e6c68c', 's3': '#f2dba6', 's4': '#fbefcf',
}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in PAL.items()}

# Grasbueschel (Draufsicht): d = dunkle Halmbasis, m = Halm, l = Lichtspitze
BUESCHEL = [
    "l...l",
    "m.l.m",
    "dmmmd",
]
BUESCHEL_KLEIN = [
    ".l.",
    "dmd",
]
FARBE = {'d': 'g1', 'm': 'g2', 'l': 'g4'}


def setze(im, x, y, muster, farbe):
    for dy, zeile in enumerate(muster):
        for dx, ch in enumerate(zeile):
            if ch != '.':
                im.putpixel(((x + dx) % 16, (y + dy) % 16), RGB[farbe[ch]])


def gras(variante):
    im = Image.new('RGB', (16, 16), RGB['g3'])
    # dezente hellere/dunklere Einzelpixel fuer Lebendigkeit (wrap -> nahtlos)
    akzente = {0: [(2, 12, 'g4'), (9, 1, 'g4'), (13, 9, 'g2'), (6, 6, 'g2')],
               1: [(4, 3, 'g4'), (11, 12, 'g4'), (1, 8, 'g2'), (14, 2, 'g2')],
               2: [(7, 14, 'g4'), (12, 5, 'g4'), (3, 2, 'g2'), (9, 9, 'g2')]}[variante]
    for x, y, f in akzente:
        im.putpixel((x, y), RGB[f])
    if variante == 0:
        setze(im, 2, 3, BUESCHEL, FARBE); setze(im, 10, 10, BUESCHEL, FARBE)
    elif variante == 1:
        setze(im, 9, 4, BUESCHEL, FARBE); setze(im, 3, 11, BUESCHEL_KLEIN, FARBE)
    else:
        setze(im, 5, 8, BUESCHEL, FARBE)
    return im


def sand(variante):
    im = Image.new('RGB', (16, 16), RGB['s2'])
    punkte = {0: [(3, 4, 's3'), (4, 4, 's4'), (11, 2, 's1'), (12, 11, 's3'), (13, 11, 's4'), (6, 13, 's1'),
                  (8, 8, 's3')],
              1: [(2, 10, 's3'), (3, 10, 's4'), (9, 5, 's1'), (14, 14, 's3'), (12, 1, 's3'), (6, 2, 's1')],
              2: [(5, 6, 's3'), (6, 6, 's4'), (12, 9, 's1'), (1, 14, 's3'), (10, 13, 's3')]}[variante]
    for x, y, f in punkte:
        im.putpixel((x, y), RGB[f])
    if variante == 0:  # kleiner Kiesel mit Schatten
        for x, y, f in [(9, 12, 's0'), (10, 12, 's1'), (9, 11, 's4'), (10, 11, 's3')]:
            im.putpixel((x, y), RGB[f])
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    kacheln = {}
    for v in range(3):
        kacheln['gras_%d' % v] = gras(v)
        kacheln['sand_%d' % v] = sand(v)
    for n, im in kacheln.items():
        im.save(os.path.join(OUT, n + '.png'))
    # Vorschau: Gras- und Sandflaeche mit gemischten Varianten, 4x
    import random
    random.seed(1)
    v = Image.new('RGB', (16 * 12, 16 * 6))
    for y in range(6):
        for x in range(12):
            art = 'gras' if x < 6 else 'sand'
            v.paste(kacheln['%s_%d' % (art, random.choice([0, 0, 1, 2]))], (x * 16, y * 16))
    v.resize((v.width * 4, v.height * 4), Image.NEAREST).save(os.path.join(OUT, 'vorschau_basis.png'))


if __name__ == '__main__':
    main()
