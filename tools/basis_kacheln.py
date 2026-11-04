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
    # Gras: hell und luftig, Schatten ins Blaugruen, Licht ins Gelbgruen
    'g0': '#2e7a4c', 'g1': '#45a052', 'g2': '#5fbb58', 'g3': '#78cc60', 'g4': '#93db70', 'g5': '#b6eb8a',
    # Sand: weich, Schatten ins Rotbraun, Licht ins Cremige
    's0': '#b08458', 's1': '#cfaa74', 's2': '#e2c48e', 's3': '#eed5a2', 's4': '#f8e8c4',
}
RGB = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in PAL.items()}

# Prinzipien (aus der Analyse hochwertiger 16px-Handheld-Tilesets):
# - Bodenkacheln ohne Outlines, kontrastarme Textur statt Muster-Stempel
# - Gras: kurze Halmstriche (Lichtspitze oben, dunklerer Fuss), gleichmaessig verteilt
# - Sand: weiche Flecken in hell/dunkel, selten ein Kiesel
# - alles mit Umbruch an den Raendern gesetzt -> nahtlos


def px(im, x, y, f):
    im.putpixel((x % 16, y % 16), RGB[f])


def gras(variante):
    im = Image.new('RGB', (16, 16), RGB['g3'])
    import random
    r = random.Random(100 + variante)
    # Halmstriche auf einem verrauschten Raster -> gleichmaessig, aber nicht starr
    for gy in range(0, 16, 4):
        for gx in range(0, 16, 4):
            if r.random() < 0.6:
                x, y = gx + r.randint(0, 2), gy + r.randint(0, 2)
                hell = r.random() < 0.6
                px(im, x, y, 'g4' if hell else 'g5')
                px(im, x, y + 1, 'g2')
                if r.random() < 0.3:
                    px(im, x + 1, y + 1, 'g2')
    for _ in range(3):  # ein paar einzelne dunklere Punkte fuer Tiefe
        px(im, r.randint(0, 15), r.randint(0, 15), 'g2')
    return im


def sand(variante):
    im = Image.new('RGB', (16, 16), RGB['s2'])
    import random
    r = random.Random(200 + variante)
    for f, n in (('s3', 2), ('s1', 1)):
        for _ in range(n):  # weiche, laengliche Flecken (4x3 mit runden Ecken)
            x, y = r.randint(0, 15), r.randint(0, 15)
            for dx, dy in ((1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (3, 1), (1, 2), (2, 2)):
                px(im, x + dx, y + dy, f)
    for _ in range(3):
        px(im, r.randint(0, 15), r.randint(0, 15), 's4')
    if variante == 0:  # kleiner Kiesel, Licht von oben links
        for dx, dy, f in ((0, 0, 's4'), (1, 0, 's3'), (0, 1, 's1'), (1, 1, 's0')):
            px(im, 10 + dx, 11 + dy, f)
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
