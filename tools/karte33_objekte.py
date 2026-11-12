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
TRAUM = ['karte32/traum/%02d' % i for i in (0, 63, 33, 1, 2, 3, 7, 62, 9, 60, 28, 54, 47, 51, 38, 30, 5, 27, 0, 1, 2)]


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    kl = lay['klassen']
    cols, rows = lay['groesse']
    os.makedirs(os.path.join(OBJ, 'fremd'), exist_ok=True)
    leer = np.array([[c == '.' for c in z] for z in kl])
    rnd = random.Random(3333)
    objekte, gesetzt = [], []
    for _ in range(8000):
        if len(gesetzt) >= 30:
            break
        tx, ty = rnd.randrange(1, cols - 1), rnd.randrange(1, rows - 1)
        if not leer[max(0, ty - 2):ty + 3, max(0, tx - 2):tx + 3].all():
            continue
        if any(abs(tx - x) + abs(ty - y) < 6 for (x, y) in gesetzt):
            continue
        name = rnd.choice(TRAUM)
        ziel = 'fremd/' + name.replace('/', '-') + '.png'
        if not os.path.exists(os.path.join(OBJ, ziel)):
            shutil.copy(os.path.join(ROOT, 'assets', 'objekte', name + '.png'), os.path.join(OBJ, ziel))
        sp = Image.open(os.path.join(OBJ, ziel))
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
