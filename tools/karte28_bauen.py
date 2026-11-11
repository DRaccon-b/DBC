"""Karte 28 - Tower Forest (A02), Gelaende im Stil von Karte 23 / 27 (Bausteine Karte 01/04/06/23).

Gras aus Karte 01, Waldboden dunkler (die Baeume des Waldrands sind Objekte), Feldwege (Sand), Schlamm-Arena als
Hochflaeche (dunkle, nasse Erde mit helleren Erdflecken) mit niedriger Front und zwei Steintreppen im Sueden, im
Norden 3 Kacheln hohe graue Steinwaende des hoeheren Waldes, rechts grauer Steinboden (umgefaerbte Kacheln) mit
Erdflecken, Ausgaenge als Teleporter.

  python3 tools/karte28_layout.py && python3 tools/karte28_bauen.py
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

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte28')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte28')
T = 16
N_FRAMES = 4
k4.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
FRONT_WALD = 48                                  # Steinwaende im Norden der Arena: 3 Kacheln
FRONT_ARENA = 28                                 # niedrige Front der Arena im Sueden (Treppen)


def maske(cls, arten):
    return np.kron(np.array([[c in arten for c in z] for z in cls]), np.ones((T, T), bool))


def grau(a):                                     # Sandkacheln von Karte 01 -> dunkler, kuehler Steinboden
    l = a.mean(axis=2, keepdims=True) / 255.0
    lo, hi = np.array([60, 61, 74], np.float32), np.array([112, 114, 132], np.float32)
    return lo + (hi - lo) * np.clip((l - 0.45) / 0.45, 0, 1)


def risse(a, m, seed=28, farbe=(38, 34, 30), n_div=900):
    """Feine verzweigte Risse/Wurzeln im Arena-Schlamm (wie die Vorlage), nur innerhalb der Maske."""
    rs = np.random.RandomState(seed)
    Hh, W = m.shape
    ys, xs = np.nonzero(m)
    for i in rs.choice(len(ys), max(1, len(ys) // n_div), replace=False):
        y, x = ys[i], xs[i]
        dx, dy = rs.choice([-1, 1]), rs.choice([-1, 0, 1])
        for _ in range(rs.randint(5, 12)):
            if 0 <= y < Hh and 0 <= x < W and m[y, x]:
                a[y, x] = farbe
                if 0 <= y - 1 and m[y - 1, x]:
                    a[y - 1, x] = np.clip(a[y - 1, x].astype(int) + 10, 0, 255)
            x += dx
            y += dy if rs.rand() < 0.5 else 0
            if rs.rand() < 0.25:
                dy = rs.choice([-1, 0, 1])


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
    stein = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, grau), cols, rows)
    a = gras.copy()
    wm = weich(zell_maske(cls, 'h', cols, rows), 5, 0.4, 3)          # Waldboden (Baeume sind Objekte)
    a[wm] = (gras[wm] * np.array([0.62, 0.7, 0.66])).astype(np.uint8)
    # Steinplatz rechts: grauer Boden, Erdflecken mit weichem Rand
    km = weich(zell_maske(cls, 'k', cols, rows), 5.0, 0.4, 11)
    a[km] = stein[km]
    em = weich(zell_maske(cls, 'e', cols, rows), 5.0, 0.5, 12) & (hp < 2)
    a[em] = erde[em]
    # Schlamm-Arena: dunkle nasse Erde, Risse, hellere Erdflecken
    arena = hp == 2
    fm = arena & ~maske(cls, 'm')
    k23.schlamm(a, fm, erde)
    a[fm] = (a[fm] * np.array([0.82, 0.84, 0.86])).astype(np.uint8)
    risse(a, fm)
    eam = weich(zell_maske(cls, 'e', cols, rows), 4.0, 0.5, 13) & arena
    a[eam] = (erde[eam] * np.array([0.8, 0.74, 0.7])).astype(np.uint8)
    # Feldwege
    roh = zell_maske(cls, 'wT', cols, rows)
    m = weich(roh, 7.0, 0.5, 4) & (hp < 2)
    a[m] = sand[m]
    saum = weich(roh, 7.0, 0.5, 4, 0.36) & ~m & (hp < 2)
    a[saum] = (a[saum] * 0.9).astype(np.uint8)
    # Hoehen: zuerst die Arena (niedrige Front, Treppen), dann die Steinwaende des hoeheren Waldes in die Arena
    lippe = k20.lippe_aus_gras(gras)
    frei = np.zeros((Hp, Wp), bool)
    treppen = []
    for tp in lay['treppen']:
        x0, x1 = tp['x'] * T, (tp['x'] + tp['b']) * T
        ye = int(np.nonzero(arena[:, x0 + 8])[0].max())
        frei[ye - 14:ye + FRONT_ARENA + 8, x0:x1] = True
        treppen.append((x0, x1, ye))
    vor2 = a.copy()
    wand = k4.hoehenkanten(a, arena | (hp >= 3), 'stein', FRONT_ARENA, 6, lippe, frei, 28, berg=False)
    from PIL import ImageFilter as _IF
    def _dehnen(mm, n):
        return np.array(Image.fromarray(mm.astype(np.uint8) * 255).filter(_IF.MaxFilter(n))) > 0
    unter_arena = np.zeros_like(arena)                               # Suedfront der Arena (unterhalb) bleibt
    for d in range(1, FRONT_ARENA + 8):
        unter_arena[d:] |= arena[:-d]
    nur_wald = (hp != 2) & ~_dehnen(arena, 13) & ~_dehnen(unter_arena, 5)   # Kante hoher Wald / Wald: unsichtbar
    a[nur_wald] = vor2[nur_wald]
    wand &= ~nur_wald
    for (x0, x1, ye) in treppen:
        k4.treppe(a, x0, x1, ye, 's', FRONT_ARENA, 'stein', a.copy())
        yf = ye + FRONT_ARENA + 5                                    # Weg setzt genau in Treppenbreite an (Regel 2)
        for y in range(yf, yf + 10):                                 # seitlich davon kein Weg (sonst breiter als Treppe)
            for xs_ in (slice(x0 - 14, x0 + 1), slice(x1 - 1, x1 + 14)):
                sel = (a[y, xs_] == sand[y, xs_]).all(axis=1)
                a[y, xs_][sel] = gras[y, xs_][sel]
        rs = np.random.RandomState(x0)
        for y in range(yf, yf + 22):
            ein = max(0, (y - yf - 12) // 3)                         # nach unten weich in den Feldweg uebergehen
            l = x0 + 1 + ein + rs.randint(0, 2) * (y > yf + 10)
            r = x1 - 1 - ein - rs.randint(0, 2) * (y > yf + 10)
            a[y, l:r] = sand[y, l:r]
    vor3 = a.copy()
    w3 = k4.hoehenkanten(a, k23.nach_oben(hp >= 3), 'stein', FRONT_WALD, 8, lippe, np.zeros((Hp, Wp), bool), 29, berg=False)
    im_wald = (hp != 2)                                              # Seitenkanten des hohen Waldes im Wald nicht zeigen
    a[im_wald] = vor3[im_wald]
    wand |= w3 & ~im_wald
    for tp in lay['ausgaenge']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = hp.astype(np.uint8)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
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
            k4.objekte_zeichnen(img, objs, cache, ~wand, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
            k6.animieren_k6(img, objs, cache, frame or 0)
            kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 28 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
