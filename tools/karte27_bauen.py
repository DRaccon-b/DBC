"""Karte 27 - Destiny Lake (A02), Gelaende im Stil von Karte 23 / 25 (Bausteine Karte 01/04/06).

Gras und Sand aus Karte 01, Waldboden dunkler (die Baeume des Waldrands sind Objekte), Moor aus Erdkacheln (Karte 23)
mit Schlamm, Feldweg, Steinweg-Pflaster, See mit Ufer und Tiefenstufen (wasser_vertieft), Plateaus mit grauen
Steinmauer-Fronten (3 Kacheln, Karte 23 'stein'), Wasserfaelle wo die Baeche des Plateaus ueber die Front fallen,
Holzstege (Karte 25), Teleporter.

  python3 tools/karte27_layout.py && python3 tools/karte27_bauen.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20
import karte23_bauen as k23
import karte25_bauen as k25
import klippen

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte27')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte27')
T = 16
N_FRAMES = 4
k4.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
FRONT = 48                                       # Mauerfronten der Vorlage sind 3 Kacheln hoch


def maske(cls, arten):
    return np.kron(np.array([[c in arten for c in z] for z in cls]), np.ones((T, T), bool))


def pflaster(cols, rows):
    """Steinweg: graue Pflastersteine (je Kachel 2x2 Steine, versetzt), Fugen dunkel, Lichtkante oben links."""
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    rng = np.random.RandomState(27)
    for y in range(0, rows * T, 8):
        off = 4 if (y // 8) % 2 else 0
        for x in range(-8, cols * T, 8):
            c = np.array((128, 134, 138)) + rng.randint(-10, 10)
            x0, x1 = max(0, x + off), min(cols * T, x + off + 8)
            if x1 <= x0:
                continue
            t[y:y + 8, x0:x1] = c
            t[y, x0:x1] = np.clip(c + 22, 0, 255)
            t[y:y + 8, x0] = np.clip(c + 12, 0, 255)
            t[y + 7, x0:x1] = (70, 74, 80)
            t[y:y + 8, x1 - 1] = (78, 82, 88)
    return t


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = np.kron(np.array([[int(c) for c in z] for z in lay['hoehe']]), np.ones((T, T), int))
    basis = os.path.join(ROOT, 'assets', 'basis')
    gras = flaeche(k6.kacheln(os.path.join(basis, 'gras_%d.png'), 5), cols, rows)
    sand = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5), cols, rows)
    erde = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, k23.braun), cols, rows)
    a = gras.copy()
    wm = weich(zell_maske(cls, 'h', cols, rows), 5, 0.4, 3)          # Waldboden (Baeume sind Objekte)
    a[wm] = (gras[wm] * np.array([0.62, 0.7, 0.66])).astype(np.uint8)
    fm = weich(zell_maske(cls, 'f', cols, rows), 6.0, 0.5, 9)        # Moor: Erde, nass und dunkel
    a[fm] = erde[fm]
    k23.schlamm(a, fm, erde)
    roh = zell_maske(cls, 'wT', cols, rows)                          # Feldweg
    m = weich(roh, 7.0, 0.5, 4)
    a[m] = sand[m]
    saum = weich(roh, 7.0, 0.5, 4, 0.36) & ~m
    a[saum] = (a[saum] * 0.9).astype(np.uint8)
    sm = weich(zell_maske(cls, 's', cols, rows), 6.0, 0.4, 5)        # Sandstrand
    a[sm] = sand[sm]
    pm = maske(cls, 'p')                                             # Steinweg / Platz (Kachelraster, gerade Kanten)
    pf = pflaster(cols, rows)
    a[pm] = pf[pm]
    # Plateaus mit grauen Steinmauer-Fronten
    lippe = k20.lippe_aus_gras(gras)
    hoch = hp >= 2
    hoch_k = k23.nach_oben(hoch)
    wand = k4.hoehenkanten(a, hoch_k, 'stein', FRONT, 8, lippe, np.zeros((Hp, Wp), bool), 27, berg=False)
    # Wasser: See (Grundebene) und Baeche auf dem Plateau, Ufer und Tiefenstufen
    import wasser_vertieft
    x_t = np.array([[ch == 'x' for ch in z] for z in cls])
    xm = weich(np.kron(x_t, np.ones((T, T))).astype(np.float32), 4, 0.15, 8, 0.45) & ~wand
    steg_t = np.array([[ch == 'b' for ch in z] for z in cls])
    xm |= np.kron(steg_t, np.ones((T, T), bool))                    # Stege stehen ueber dem Wasser
    a = np.array(wasser_vertieft.vertiefen(Image.fromarray(a), np.ones_like(xm), frame, maske=xm).convert('RGB'))
    a[pm & xm] = pf[pm & xm]                                         # Steinbruecken ueber dem Wasser
    img = Image.fromarray(a).convert('RGBA')
    # Wasserfaelle: Baeche des Plateaus, die an der Front enden
    for (x0, y0, x1, y1) in lay['plateaus']:
        reihe = y1
        if reihe + 1 >= rows:
            continue
        xs = [x for x in range(x0, x1 + 1) if cls[reihe][x] == 'x']
        laeufe, cur = [], []
        for x in xs:
            if cur and x != cur[-1] + 1:
                laeufe.append(cur); cur = []
            cur.append(x)
        if cur:
            laeufe.append(cur)
        for l in laeufe:
            klippen.zeichne_wasserfall(img, l[0] * T, (l[-1] + 1) * T, (reihe + 1) * T, (reihe + 1) * T + FRONT + 6,
                                       seed=l[0], frame=frame or 0)
    a = np.array(img.convert('RGB'))
    # Holzstege (wie Karte 25): Rechtecke der zusammenhaengenden 'b'-Kacheln
    stege = []
    gesehen = set()
    for y in range(rows):
        for x in range(cols):
            if cls[y][x] == 'b' and (y, x) not in gesehen:
                x1 = x
                while x1 + 1 < cols and cls[y][x1 + 1] == 'b':
                    x1 += 1
                y1 = y
                while y1 + 1 < rows and all(cls[y1 + 1][xx] == 'b' for xx in range(x, x1 + 1)):
                    y1 += 1
                for yy in range(y, y1 + 1):
                    for xx in range(x, x1 + 1):
                        gesehen.add((yy, xx))
                stege.append((x, y, x1, y1))
    steg_m = k25.stege(a, {'stege': stege}, xm) if stege else np.zeros((Hp, Wp), bool)
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = hp.astype(np.uint8) + 1
    wasser = xm & ~steg_m & ~pm
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(wasser))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand))
    pfj = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pfj):
        objs = sorted((o for o in json.load(open(pfj)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.copy().astype(np.int16)
            ebenen[wand] = 9
            ebenen[wasser] = 7
            k4.objekte_zeichnen(img, objs, cache, ~wasser & ~wand, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
            k6.animieren_k6(img, objs, cache, frame or 0)
            kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 27 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
