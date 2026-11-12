"""Karte 33 - The World of Dreams: schwebende Traumobjekte in der Sternenleere -> platzierung.json

  python3 tools/karte33_objekte.py && python3 tools/karte33_bauen.py

Wiederverwendet (Regel 3): die PixelLab-Traumobjekte von Karte 32 (Taschenuhren, Fernseher, Spielkarte, Spiegel,
Sanduhren, Kristallkugeln, Saeckchen, Kristalle, Mond, Stern, Schluessel, Wuerfel). Wie in der Vorlage nur in der
Leere um die Plattform, mit Abstand zur Plattform und zueinander; jedes schwebt 1 px auf und ab (eigene Phase).
"""
import json, math, os, random, shutil
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte33')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte33')
T = 16
TRAUM = ['karte32/traum/%02d' % i for i in (0, 1, 2, 7, 9, 51, 38)]
SURREAL = ['karte33/surreal/%02d' % i for i in (0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 13, 14, 15)]   # Nutzer: surrealer


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    kl = lay['klassen']
    cols, rows = lay['groesse']
    os.makedirs(os.path.join(OBJ, 'fremd'), exist_ok=True)
    leer = np.array([[c == '.' for c in z] for z in kl])
    from PIL import ImageDraw, ImageFilter
    riss = Image.new('L', (cols, rows), 0)                            # Rissflaechen (+2 Kacheln) frei halten
    for r in lay.get('risse', []):
        ex, ey = r['ecke']
        ecke = [(0 if ex == 0 else cols, 0 if ey == 0 else rows)]
        ImageDraw.Draw(riss).polygon([(x - 0.5, y - 0.5) for (x, y) in [tuple(p) for p in r['kante']] + ecke], fill=255)
    rissnah = np.array(riss.filter(ImageFilter.MaxFilter(5))) > 0
    rnd = random.Random(3333)
    objekte, gesetzt, vorrat = [], [], []
    for _ in range(8000):
        if len(gesetzt) >= 30:
            break
        tx, ty = rnd.randrange(1, cols - 1), rnd.randrange(1, rows - 1)
        if not leer[max(0, ty - 2):ty + 3, max(0, tx - 2):tx + 3].all():
            continue
        if any(abs(tx - x) + abs(ty - y) < 5 for (x, y) in gesetzt):
            continue
        if rissnah[ty, tx]:
            continue
        if not vorrat:
            vorrat = SURREAL[:] + rnd.sample(TRAUM, 3)
            rnd.shuffle(vorrat)
        name = vorrat.pop()                                           # ohne Wiederholung, solange der Vorrat reicht
        if name.startswith('karte33/'):
            ziel = name[len('karte33/'):] + '.png'
        else:
            ziel = 'fremd/' + name.replace('/', '-') + '.png'
            if not os.path.exists(os.path.join(OBJ, ziel)):
                shutil.copy(os.path.join(ROOT, 'assets', 'objekte', name + '.png'), os.path.join(OBJ, ziel))
        sp = Image.open(os.path.join(OBJ, ziel))
        if rnd.random() < 0.25:                                       # surreal: manches schwebt kopfueber
            sp = sp.transpose(Image.FLIP_TOP_BOTTOM)
            ziel = ziel[:-4] + '_kopf.png'
            sp.save(os.path.join(OBJ, ziel))
        elif rnd.random() < 0.4:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            ziel = ziel[:-4] + '_m.png'
            sp.save(os.path.join(OBJ, ziel))
        bb = sp.getbbox()
        cx, fy = tx * T + 8, (ty + 1) * T - 1
        objekte.append({'datei': ziel, 'basis': name, 'x': cx - (bb[0] + bb[2]) // 2, 'y': fy - (bb[3] - 1),
                        'fuss': bb[3] - 1, 'kachel': [tx, ty], 'ebene': 1, 'schwebend': True, 'kein_schatten': True,
                        'phase': rnd.randrange(4)})
        gesetzt.append((tx, ty))
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 33: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
