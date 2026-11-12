"""Dunkle Waldbaeume fuer Karte 28 (Tower Forest, Nutzer: dunkler Wald) - umgefaerbt aus den Baeumen von Karte 01.

  python3 tools/karte28_baeume.py   -> assets/objekte/karte28/wald_dunkel/NN.png + uebersicht.png

Laub dunkler und kuehler (blaugruen, weniger gesaettigt), Lichtkante oben links bleibt erhalten (Kontrast etwas
erhoeht), Staemme dunkler. Bluetenpunkte werden gedaempft.
"""
import os
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
QUELLE = os.path.join(ROOT, 'assets', 'objekte', 'karte01', 'baeume')
ZIEL = os.path.join(ROOT, 'assets', 'objekte', 'karte28', 'wald_dunkel')
NUMMERN = (0, 1, 2, 3, 6, 7, 8, 9, 12, 13, 14)


def dunkel(im):
    a = np.array(im.convert('RGBA')).astype(np.float32)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    laub = (g > r) & (al > 0)                                        # Laub und Nadeln (auch blaugruen)
    l = (r + g + b) / 3.0
    m = l[laub].mean() if laub.any() else 100
    f = np.clip(((l - m) * 1.12 + m) / np.maximum(l, 1), 0.6, 1.4)  # Kontrast leicht erhoehen
    for k, fk in enumerate((0.50, 0.58, 0.66)):
        a[..., k] = np.where(laub, a[..., k] * f * fk + (4 if k == 2 else 0), a[..., k])
    sonst = ~laub & (al > 0)                                         # Staemme, Bluetenpunkte
    for k in range(3):
        a[..., k] = np.where(sonst, a[..., k] * 0.6, a[..., k])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def main():
    os.makedirs(ZIEL, exist_ok=True)
    ims = []
    for i, n in enumerate(NUMMERN):
        im = dunkel(Image.open(os.path.join(QUELLE, '%02d.png' % n)))
        im.save(os.path.join(ZIEL, '%02d.png' % i))
        ims.append((n, Image.open(os.path.join(QUELLE, '%02d.png' % n)).convert('RGBA'), im))
    w = sum(max(a.width, b.width) + 12 for _, a, b in ims)
    h = max(a.height for _, a, _ in ims) * 2 + 40
    c = Image.new('RGBA', (w, h), (40, 56, 40, 255)); d = ImageDraw.Draw(c)
    x = 0
    for i, (n, a, b) in enumerate(ims):
        c.alpha_composite(a, (x, 14)); c.alpha_composite(b, (x, 26 + a.height)); d.text((x, 0), '%02d' % i, fill='white')
        x += max(a.width, b.width) + 12
    c.resize((c.width * 2, c.height * 2), Image.NEAREST).save(os.path.join(ZIEL, 'uebersicht.png'))
    print(len(ims), 'dunkle Baeume ->', ZIEL)


if __name__ == '__main__':
    main()
