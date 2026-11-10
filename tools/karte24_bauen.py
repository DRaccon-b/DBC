"""Karte 24 - The Kaiser's Canyon (A02), Gelaende im Kachelstil der vorigen A02-Karten.

Canyonboden und Wege aus den Sandkacheln von Karte 01 (rot bzw. hell eingefaerbt), Sandflecken in Originalfarbe,
Felsmassen oben aus den Kieselkacheln von Karte 03 (rot eingefaerbt, wie die Felsbuckel der Vorlage), Felsfronten mit
hoehenkanten (Karte 04) in rotem Sandstein, erhoehte Arena und Schrein mit Treppen (Karte 04), Gruben, Lorenbahn,
Teleporter.

  python3 tools/karte24_layout.py && python3 tools/karte24_bauen.py
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte24')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte24')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.FELS['rot'] = ['#3e1e12', '#5c2c1a', '#7c3e24', '#9a5230', '#b8683e', '#cf8452', '#e2a270']
LIPPE_ROT = ['#5c2c1a', '#7c3e24', '#9a5230', '#b0623a', '#c47448', '#d68a5a']
FRONT = 32


def faerben(lo, hi, a0=0.35, a1=0.5):
    def f(a):
        l = a.mean(axis=2, keepdims=True) / 255.0
        return np.array(lo, np.float32) + (np.array(hi, np.float32) - np.array(lo, np.float32)) * np.clip((l - a0) / a1, 0, 1)
    return f


def grube(a, m):
    """Grube: dunkle Tiefe, oben (Nordkante) eine sichtbare Erdwand, Rand mit dunkler Kontur."""
    Hh, W = m.shape
    d = np.zeros((Hh, W), np.int32)
    for y in range(1, Hh):
        d[y] = np.where(m[y], np.where(m[y - 1], d[y - 1] + 1, 0), 0)
    W_ = [np.array(H(c), np.float32) for c in ('#7c3e24', '#5c2c1a', '#44200f', '#2e160b')]
    a[m] = (26, 12, 8)
    for k, c in enumerate(W_):
        a[m & (d == k)] = c.astype(np.uint8)
    rand = m & ~(np.roll(m, 1, 1) & np.roll(m, -1, 1))
    a[rand] = (40, 18, 10)


def gleis(a, x0, x1, y):
    """Lorenbahn waagerecht: Holzschwellen alle 8 px, zwei Stahlschienen mit Lichtkante."""
    Y = y * T
    for x in range(x0 * T, (x1 + 1) * T):
        if x % 8 < 4:
            a[Y + 3:Y + 13, x] = H('#6a4428') if x % 8 else H('#4a2e1a')
    for ys in (Y + 4, Y + 10):
        a[ys - 1, x0 * T:(x1 + 1) * T] = H('#2a2a34')
        a[ys, x0 * T:(x1 + 1) * T] = H('#a8b0bc')
        a[ys + 1, x0 * T:(x1 + 1) * T] = H('#5a6070')
        a[ys + 2, x0 * T:(x1 + 1) * T] = (a[ys + 2, x0 * T:(x1 + 1) * T] * 0.7).astype(np.uint8)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = np.kron(np.array([[int(c) for c in z] for z in lay['hoehe']]), np.ones((T, T), int))
    basis = os.path.join(ROOT, 'assets', 'basis')
    boden = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, faerben((150, 82, 50), (214, 140, 96))), cols, rows)
    weg = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, faerben((160, 118, 76), (214, 172, 120))), cols, rows)
    sand = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5), cols, rows)
    fels = flaeche(k6.kacheln(os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png'), 5,
                              faerben((120, 58, 32), (214, 132, 84), 0.25, 0.6)), cols, rows)
    a = boden.copy()
    m = weich(zell_maske(cls, 'wtT', cols, rows), 7.0, 0.5, 4)
    a[m] = weg[m]
    s = weich(zell_maske(cls, 's', cols, rows), 6.0, 0.5, 5)
    a[s] = sand[s]
    saum = weich(zell_maske(cls, 's', cols, rows), 6.0, 0.5, 5, 0.36) & ~s
    a[saum] = (a[saum] * 0.92).astype(np.uint8)
    hoch2 = weich((hp >= 2).astype(np.float32), 5, 0.0, 7, 0.5)       # Felskanten rund statt Kachelstufen
    h1m = weich((hp >= 1).astype(np.float32), 5, 0.0, 7, 0.5)
    a[hoch2] = fels[hoch2]
    hoch1 = (hp == 1)
    a[hoch1] = (boden[hoch1] * 1.04).clip(0, 255).astype(np.uint8)
    a[hoch1 & s] = sand[hoch1 & s]
    # Kanten: erst Arena/Schrein (+Fels) gegen den Boden, dann der Fels gegen alles
    frei = np.zeros((Hp, Wp), bool)
    for (x0, x1) in lay['arena_treppen'] + [tuple(lay['schrein_treppe'])]:
        col = np.nonzero(hp[:, ((x0 + x1 + 1) * T) // 2] == 1)[0]
        frei[:, x0 * T:(x1 + 1) * T] |= False
    tmask = zell_maske(cls, 't', cols, rows) > 0.5
    frei_t = np.kron(np.array([[c == 't' for c in z] for z in cls]), np.ones((T, T), bool))
    frei_t = frei_t | np.roll(frei_t, -T, 0) | np.roll(frei_t, -2 * T, 0)
    wand = k4.hoehenkanten(a, h1m, 'rot', 24, 8, LIPPE_ROT, frei_t, 71, berg=False)
    wand |= k4.hoehenkanten(a, hoch2, 'rot', FRONT, 10, LIPPE_ROT, frei_t & ~h1m, 72, berg=True)   # Seitenwaende sichtbar (Nutzer)
    # Treppen der Arena und des Schreins (frontal nach Sueden)
    for (x0, x1) in lay['arena_treppen']:
        xc = ((x0 + x1 + 1) * T) // 2
        col = np.nonzero(hp[:, xc] == 1)[0]
        ye = int(col.max())
        k4.treppe(a, x0 * T, (x1 + 1) * T, ye, 's', 24, 'rot', weg)
    # Aufgang links: der Weg laeuft als Rampe hinauf
    ya, yb = lay['arena_links']
    rm = np.zeros((Hp, Wp), bool)
    tl = [(y, x) for y in range(rows) for x in range(cols) if cls[y][x] == 't' and ya <= y <= yb]
    if tl:
        xs = [x for _, x in tl]
        x0, x1 = min(xs) * T, (max(xs) + 3) * T
        rm[ya * T:(yb + 1) * T, x0:x1] = True
        rm = weich(rm.astype(np.float32), 5, 0.4, 9)                  # Weg laeuft weich in die Arena hinauf
        a[rm] = weg[rm]
    # Gruben, Gleis, Teleporter
    xm = zell_maske(cls, 'x', cols, rows) > 0.5
    xm[:30 * T] = False                                           # oben: liegender Obelisk der Vorlage, keine Grube
    xm &= (hp == 0) & ~wand                                       # Becken im Boden, nie auf Fels oder Wand (Nutzer)
    from PIL import ImageFilter as _IF
    xm = np.array(Image.fromarray((xm * 255).astype(np.uint8)).filter(_IF.MinFilter(5))) > 0      # Abstand zur Wand
    grube(a, xm)
    gx0, gx1, gy = lay['gleis']
    gleis(a, gx0, gx1, gy)
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = hp.astype(np.uint8) + 1
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(xm))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.copy().astype(np.int16)
            ebenen[wand] = 9
            ebenen[xm] = 7
            k4.objekte_zeichnen(img, objs, cache, ~xm & ~wand, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
            kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 24 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
