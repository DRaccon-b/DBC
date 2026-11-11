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
    lo, hi = np.array([46, 47, 58], np.float32), np.array([88, 90, 106], np.float32)   # dunkler (dunkler Wald)
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


# Spinnen-Arena (Nutzer): wo in der Vorlage der Netzring liegt, steht eine 2 Kacheln dicke Steinmauer um die Arena,
# 2 Kacheln hohe Front nach Sueden; unten in der Mitte die Torluecke. An der Mauer haengen die Spinnweben.
MAUER_MITTE = (1136, 280, 164, 140)                              # cx, cy, rx, ry (px): organische Ringform (Nutzer)
MAUER_DICKE = 32
MAUER_FRONT = 32
MAUER_TOR = (1104, 1184)                                           # Torluecke unten (px)


def rr(xx, yy, x0, y0, x1, y1, r):                                  # abgerundetes Rechteck: < 0 innen
    dx = np.maximum(np.maximum(x0 + r - xx, xx - (x1 - r)), 0)
    dy = np.maximum(np.maximum(y0 + r - yy, yy - (y1 - r)), 0)
    return np.hypot(dx, dy) - r


def mauer_rand(t):                                                  # unregelmaessiger Radius je Winkel (natuerlich)
    links = np.clip(-np.cos(t), 0, 1) ** 2                          # linke Seite staerker nach aussen gewoelbt (Nutzer)
    return 1 + 0.06 * np.sin(3 * t + 1.1) * (1 - links) + 0.035 * np.sin(5 * t + 2.3) * (1 - links) + 0.12 * links


def mauer_maske(Hh, W):
    """Organische Ringform, aber am 16er-Raster (Nutzer): eine Kachel gehoert zur Mauer, wenn ihre Mitte im Ring liegt."""
    rows, cols = Hh // T, W // T
    ty, tx = np.mgrid[0:rows, 0:cols]
    cx, cy, rx, ry = MAUER_MITTE
    d = MAUER_DICKE
    dx, dy = tx * T + 8 - cx, ty * T + 8 - cy
    e = mauer_rand(np.arctan2(dy / ry, dx / rx))
    aussen = np.hypot(dx / (rx * e), dy / (ry * e)) < 1
    innen = np.hypot(dx / ((rx - d - 6) * e), dy / ((ry - d - 6) * e)) < 1
    ring_t = aussen & ~innen
    for _ in range(2):                                               # Diagonalen: Treppenstufen schliessen (mind. 2 Kacheln)
        luecke = ~ring_t & ~innen & aussen
        ring_t |= luecke
        voll = ring_t.copy()
        voll[1:-1, 1:-1] |= (ring_t[:-2, 1:-1] & ring_t[1:-1, 2:]) | (ring_t[:-2, 1:-1] & ring_t[1:-1, :-2])
        ring_t = voll & ~innen
    ring_t &= ~((tx * T >= MAUER_TOR[0]) & (tx * T < MAUER_TOR[1]) & (ty * T > cy))
    return np.kron(ring_t, np.ones((T, T), bool))


def mauer(a, ring, stein):
    """Mauerkrone aus dunklen Steinbloecken (8x8, versetzt, Fugen, Licht oben links), dann Fronten und Seiten."""
    Hh, W = ring.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    krone = stein.astype(np.float32) * 0.92
    reihe = yy // 8
    fuge_h = (yy % 8) == 7
    fuge_v = ((xx + (reihe % 2) * 4) % 8) == 7
    licht = ((yy % 8) == 0) | (((xx + (reihe % 2) * 4) % 8) == 0)
    krone[fuge_h | fuge_v] *= 0.62
    krone[licht & ~(fuge_h | fuge_v)] = np.clip(krone[licht & ~(fuge_h | fuge_v)] * 1.18, 0, 255)
    a[ring] = krone[ring].astype(np.uint8)
    kontur = ring & ~(np.roll(ring, 1, 0) & np.roll(ring, -1, 0) & np.roll(ring, 1, 1) & np.roll(ring, -1, 1))
    a[kontur] = (36, 37, 46)
    return k4.hoehenkanten(a, ring, 'stein', MAUER_FRONT, 6, k4.LIPPE['a'], np.zeros((Hh, W), bool), 33, berg=False)


def netz_ring(a, frame, maske, teiler=30):
    """Dichter Spinnweben-Teppich als Ring um die Mitte des Steinplatzes (Vorlage): viele feine, gerade Faeden in
    hellem Grauweiss (halbtransparent), dazu Knotenpunkte; zum Rand hin lichter (weich auslaufend)."""
    Hh, W = a.shape[:2]
    ring = maske
    rs = np.random.RandomState(281)
    over = np.zeros((Hh, W), np.float32)

    def faden(x0, y0, x1, y1, st):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for t in np.linspace(0, 1, n):
            X, Y = int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t))
            if 0 <= X < W and 0 <= Y < Hh and ring[Y, X]:
                over[Y, X] = max(over[Y, X], st)
    ys, xs = np.nonzero(ring)
    zentren = []
    for i in rs.permutation(len(ys))[:len(ys) // teiler]:                 # kleine Netze mit Mindestabstand
        y, x = ys[i], xs[i]
        if all((x - cx) ** 2 + (y - cy) ** 2 > 13 ** 2 for cx, cy in zentren):
            zentren.append((x, y))
    for (cx, cy) in zentren:
        r = rs.randint(8, 13)
        n = rs.randint(6, 9)
        a0 = rs.rand() * np.pi
        ends = [(cx + np.cos(a0 + k * 2 * np.pi / n) * r * (0.8 + 0.3 * rs.rand()),
                 cy + np.sin(a0 + k * 2 * np.pi / n) * r * (0.8 + 0.3 * rs.rand())) for k in range(n)]
        for (ex, ey) in ends:                                        # Speichen
            faden(cx, cy, ex, ey, 0.7)
        for f in (0.4, 0.72, 1.0):                                   # Ringfaeden
            pts = [(cx + (ex - cx) * f, cy + (ey - cy) * f) for (ex, ey) in ends]
            for k in range(n):
                faden(pts[k][0], pts[k][1], pts[(k + 1) % n][0], pts[(k + 1) % n][1], 0.55 if f < 1 else 0.45)
    for (cx, cy) in zentren:                                         # lose Verbindungsfaeden zum Nachbarnetz
        nb = sorted(zentren, key=lambda q: (q[0] - cx) ** 2 + (q[1] - cy) ** 2)[1:2]
        for (qx, qy) in nb:
            faden(cx, cy, qx, qy, 0.4)
    farbe = np.array([214, 218, 228], np.float32)
    m = over > 0
    a[m] = (a[m] * (1 - over[m, None] * 0.6) + farbe * over[m, None] * 0.6).astype(np.uint8)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = np.kron(np.array([[int(c) for c in z] for z in lay['hoehe']]), np.ones((T, T), int))
    basis = os.path.join(ROOT, 'assets', 'basis')
    # dunkler Wald (Nutzer): Kacheln von Karte 01 (GBA-Stil wie die anderen Karten), nur dunkler und kuehler gefaerbt
    def dunkelgruen(a_):
        return a_ * np.array([0.5, 0.6, 0.58], np.float32)
    def walddunkel(a_):
        return a_ * np.array([0.42, 0.52, 0.5], np.float32)
    def pfad(a_):
        return k23.braun(a_) * np.array([0.72, 0.68, 0.64], np.float32)
    def walderde(a_):
        return k23.braun(a_) * np.array([0.62, 0.56, 0.52], np.float32)
    gras = flaeche(k6.kacheln(os.path.join(basis, 'gras_%d.png'), 5, dunkelgruen), cols, rows)
    waldboden = flaeche(k6.kacheln(os.path.join(basis, 'gras_%d.png'), 5, walddunkel), cols, rows)
    sand = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, pfad), cols, rows)
    erde = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, walderde), cols, rows)
    stein = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, grau), cols, rows)
    a = gras.copy()
    wm = weich(zell_maske(cls, 'h', cols, rows), 5, 0.4, 3)          # Waldboden (Baeume sind Objekte)
    a[wm] = waldboden[wm]
    # Steinplatz rechts: grauer Boden, Erdflecken mit weichem Rand
    km = weich(zell_maske(cls, 'k', cols, rows), 5.0, 0.4, 11)
    a[km] = stein[km]
    em = weich(zell_maske(cls, 'e', cols, rows), 5.0, 0.5, 12) & (hp < 2)
    a[em] = erde[em]
    # Schlamm-Arena: dunkle nasse Erde, Risse, hellere Erdflecken
    arena = hp == 2
    fm = weich(zell_maske(cls, 'ft', cols, rows), 5.0, 0.5, 9) & arena   # Schlamm (weicher Rand); der Plateaurand bleibt Gras
    k23.schlamm(a, fm, erde)
    a[fm] = (a[fm] * np.array([0.82, 0.84, 0.86])).astype(np.uint8)
    risse(a, fm)
    eam = weich(zell_maske(cls, 'e', cols, rows), 4.0, 0.5, 13) & arena
    a[eam] = (erde[eam] * 1.08).clip(0, 255).astype(np.uint8)
    # Feldwege
    roh = zell_maske(cls, 'wT', cols, rows)
    m = weich(roh, 7.0, 0.5, 4) & (hp < 2)
    a[m] = sand[m]
    saum = weich(roh, 7.0, 0.5, 4, 0.36) & ~m & (hp < 2)
    a[saum] = (a[saum] * 0.9).astype(np.uint8)
    # Arena = ERHOEHUNG (Nutzer: nur eine Ebene): Arena und der Wald dahinter liegen gleich hoch (keine zweiten Waende
    # im Norden); im Sueden niedrige Steinfront mit den zwei frontalen Steintreppen hinauf.
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
    # Plateaukante im Norden und an den Seiten (Nutzer: Verlauf oben sichtbar): 2 px dunkle Abbruchkante aussen,
    # 1 px helle Graslippe innen; die Suedfront (Waende, Treppen) bleibt unberuehrt
    aussen = _dehnen(arena, 5) & ~arena & ~_dehnen(wand, 7)
    innen = arena & _dehnen(~arena, 3) & ~_dehnen(wand, 7)
    a[aussen] = (a[aussen] * np.array([0.5, 0.52, 0.5])).astype(np.uint8)
    a[innen] = np.clip(a[innen] * np.array([1.18, 1.2, 1.12]), 0, 255).astype(np.uint8)
    ring = mauer_maske(Hp, Wp)
    w_m = mauer(a, ring, stein)
    netz_ring(a, frame, ring | w_m, teiler=70)                       # Spinnweben haengen an Mauerkrone und Fronten
    wand |= w_m | ring
    for tp in lay['ausgaenge']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = np.where(arena | (hp >= 3), 2, 1).astype(np.uint8)       # Arena und Wald dahinter: obere Ebene
    lvl[ring] = 3                                                    # Mauerkrone
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
