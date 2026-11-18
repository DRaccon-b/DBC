"""Karte 55 (Hurricane Landing): zwei schwebende Plattformen in der Leere des Netzes (Stil Karte 16/17/19).

Links New York: Gehwegplatten und Asphalt wie Karte 18/35 (Bordsteine, gelbe Doppel-Mittellinie, Zebrastreifen,
Kanaldeckel), am Nordrand stehen Fassaden (Objekte) mit dem Fuss auf Reihe 9. Rechts Colorado: trockene Praerie
(Graskacheln gelbgruen umgefaerbt), Landstrasse in Boegen mit 45-Grad-Kanten (Regel 6b, k4.RASTER45), Bankett aus
Schotter, gelbe Mittellinie. Beide Raeume mit Randring (dunkler), cyan Kante, Metallfront mit Lichtfaeden, Aufstell-
feld, Ankunfts-/Goldpfeilen und Ringmarke (Funktionen Karte 16/17). Animation folgt erst am Ende (Nutzer).

  python3 tools/karte55_layout.py && python3 tools/karte55_bauen.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte04_bauen as k4
import karte06_bauen as k6
import karte08_bauen as k8
import karte16_bauen as k16
import karte17_bauen as k17
import karte18_bauen as k18
import karte20_bauen as k20
import karte30_bauen as k30

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte55')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte55')
T = 16
N_FRAMES = k16.N_FRAMES
BILDDAUER = k16.BILDDAUER
CYAN, LEER = k16.CYAN, k16.LEER
kontur, mischen, puls = k16.kontur, k16.mischen, k16.puls
H = k4.H
GELB = np.array(H('#d8b048'), np.uint8)
WEISS = np.array(H('#e4e8ee'), np.uint8)
k4.RASTER45 = True


def faerben(lo, hi, a0=0.35, a1=0.5):
    def f(a):
        l = a.mean(axis=2, keepdims=True) / 255.0
        return np.array(lo, np.float32) + (np.array(hi, np.float32) - np.array(lo, np.float32)) * np.clip((l - a0) / a1, 0, 1)
    return f


def texturen(cols, rows):
    basis = os.path.join(ROOT, 'assets', 'basis')
    kies = os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png')
    return {
        'geh': k18.textur('g', cols, rows),
        'asph': k18.textur('s', cols, rows),
        'praerie': k20.flaeche(k6.kacheln(os.path.join(basis, 'gras_%d.png'), 5,
                                          faerben((132, 124, 64), (206, 190, 112), 0.3, 0.5)), cols, rows),
        'schotter': k20.flaeche(k6.kacheln(kies, 5, faerben((122, 104, 82), (184, 164, 128), 0.25, 0.6)), cols, rows),
    }


def mittellinie_polylinie(a, frei, pts, x0, y0, farbe, s=10, l=8):
    """Gestrichelte Mittellinie (2 px) entlang der Strassenachse; Boegen exakt 45 Grad (Treppe 1:1 im Pixelraster)."""
    v = 0
    for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
        Xa, Ya = int(round((x0 + xa) * T)), int(round((y0 + ya) * T)) - 1
        Xb, Yb = int(round((x0 + xb) * T)), int(round((y0 + yb) * T)) - 1
        n = max(abs(Xb - Xa), abs(Yb - Ya))
        for i in range(n):
            X = Xa + (Xb - Xa) * i // n
            Y = Ya + (Yb - Ya) * i // n
            if v % (s + l) < s:
                for d in (0, 1):
                    if 0 <= Y + d < a.shape[0] and 0 <= X < a.shape[1] and frei[Y + d, X]:
                        a[Y + d, X] = farbe
            v += 1


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    cls = lay['klassen']
    gross = lambda m: np.kron(m, np.ones((T, T), int)).astype(bool)
    a = np.zeros((Hp, Wp, 3), np.uint8)
    a[:] = LEER
    land = gross(kl != '.')
    ring = gross(kl == 'r')
    leer = ~land
    k16.leere(a, leer, frame)
    tex = texturen(cols, rows)
    (nx, ny), (cx_, cy_) = lay['raeume']
    RW, RH = lay['raum']
    links = np.zeros((Hp, Wp), bool); links[:, :(nx + RW + 2) * T] = True
    rechts = ~links
    # ------------------------------------------------------------------ New York
    ny_land = land & links
    a[ny_land] = tex['geh'][ny_land]
    av0, av1 = lay['avenue']
    asph_k = np.zeros_like(kl, bool)
    asph_k[ny + av0:ny + av1 + 1, nx + 1:nx + RW - 1] = True
    asphalt = gross(asph_k)
    a[asphalt] = tex['asph'][asphalt]
    k18.bordsteine(a, asphalt, ny_land & ~ring)
    z0, z1 = lay['zebra']
    zebra = np.zeros((Hp, Wp), bool)
    zebra[(ny + av0) * T:(ny + av1 + 1) * T, (nx + z0) * T:(nx + z1 + 1) * T] = True
    for y in range((ny + av0) * T + 3, (ny + av1 + 1) * T - 3):          # Zebrastreifen: Balken quer zur Fahrbahn
        for x in range((nx + z0) * T + 2, (nx + z1 + 1) * T - 2):
            if (x - (nx + z0) * T - 2) % 8 < 5:
                a[y, x] = WEISS
    sperre = np.array(Image.fromarray((zebra * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(17))) > 0
    marken = gross(np.isin(kl, list('ogz')))
    frei = asphalt & ~sperre & ~(np.array(Image.fromarray((marken * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0)
    ym = (ny + (av0 + av1 + 1) / 2) * T                               # gelbe Doppellinie exakt auf der Fahrbahnmitte
    for yy in (int(ym) - 3, int(ym) + 1):
        k30.striche(a, frei, (nx + 1) * T, (nx + RW - 1) * T, yy, GELB, s=10 ** 6, l=0)
    for xs in ((nx + 1) * T, (nx + z1 + 1) * T):                         # weisse Spurstriche je Fahrtrichtung
        pass
    for yy in (int((ny + av0 + 1.5) * T) - 1, int((ny + av1 - 0.5) * T) - 1):
        k30.striche(a, frei, (nx + 1) * T + 4, (nx + RW - 1) * T, yy, WEISS, s=12, l=12)
    # Kanaldeckel (fest), nie auf Markierungen
    for (tx, ty) in ((nx + 5, ny + av0 + 1), (nx + 21, ny + av1 - 1)):
        cx, cy = tx * T + 8, ty * T + 8
        yy, xx = np.ogrid[-5:6, -5:6]
        d = np.sqrt(yy ** 2 + xx ** 2)
        sub = a[cy - 5:cy + 6, cx - 5:cx + 6]
        sub[d <= 5] = H('#2a2e38'); sub[d <= 4] = H('#4a505e')
        sub[(d <= 4) & ((yy + xx) % 3 == 0)] = H('#3a3f4c')
        sub[(d > 3.4) & (d <= 4) & (yy < 0)] = H('#6a7080')
    # ------------------------------------------------------------------ Colorado
    co_land = land & rechts
    a[co_land] = tex['praerie'][co_land]
    # Strasse und Bankett laufen bis an die Plattformkante (der Weg ist ein Stueck Landstrasse, das im Netz schwebt):
    # Kachelmaske direkt aus der Achse, auch unter dem Randring und darueber hinaus, dann 45-Grad-Raster
    yy_, xx_ = np.mgrid[0:rows, 0:cols].astype(float)
    import karte55_layout as k55l
    d = k55l.abstand_polylinie(xx_ - cx_ + 0.5, yy_ - cy_ + 0.5, lay['strasse'])
    nahe = (xx_ >= cx_ - 2) & (xx_ <= cx_ + RW + 1)
    strasse_k = np.kron(((d <= 2.0) & nahe).astype(np.float32), np.ones((T, T), np.float32))
    bank_k = np.kron(((d <= 3.0) & nahe).astype(np.float32), np.ones((T, T), np.float32))
    ring_co = ring & rechts
    a[ring_co] = (tex['schotter'][ring_co] * 0.8).astype(np.uint8)        # Randring: Erdkante statt Gras
    bank = k4.weich(bank_k, 5, 0, 55) & co_land
    a[bank] = tex['schotter'][bank]
    strasse = k4.weich(strasse_k, 5, 0, 56) & co_land
    a[strasse] = tex['asph'][strasse]
    innen_co = co_land
    # Schotter- und Asphaltkante: 1 px dunkle Fuge auf der Strasse, Bankett mit hellem Saum (Licht oben links)
    rand_s = strasse & ~(np.roll(strasse, 1, 0) & np.roll(strasse, -1, 0) & np.roll(strasse, 1, 1) & np.roll(strasse, -1, 1))
    k18.dunkeln(a, rand_s & innen_co, 0.72)
    rand_b = bank & ~strasse & ~(np.roll(bank, 1, 0) & np.roll(bank, -1, 0) & np.roll(bank, 1, 1) & np.roll(bank, -1, 1))
    k18.dunkeln(a, rand_b & innen_co, 0.85)
    innen = k4.weich(strasse_k, 5, 0, 56) & ~gross(np.isin(kl, list('o')))
    for _ in range(6):                                                  # Linie nur weit innen (nicht am Rand)
        innen = innen & np.roll(innen, 1, 0) & np.roll(innen, -1, 0) & np.roll(innen, 1, 1) & np.roll(innen, -1, 1)
    mittellinie_polylinie(a, innen & co_land & ~ring, lay['strasse'], cx_, cy_, GELB)
    # ------------------------------------------------------------------ Randring, Marken
    a[ring] = (a[ring] * 0.72).astype(np.uint8)
    innen_l = land & ~ring
    a[innen_l & np.roll(ring, -1, 0)] = (18, 26, 46)
    a[innen_l & np.roll(ring, 1, 0)] = (a[innen_l & np.roll(ring, 1, 0)] * 1.15).clip(0, 255).astype(np.uint8)
    for i, (x0, y0) in enumerate(lay['raeume']):
        fy, fx = np.nonzero(kl[y0:y0 + RH, x0:x0 + RW] == 'f')
        k17.feld_marken(a, x0 + fx.min(), y0 + fy.min(), fx.max() - fx.min() + 1, fy.max() - fy.min() + 1, frame)
        mx, my = lay['ringmarken'][i]
        k17.ringmarke(a, x0 + mx, y0 + my, frame)
    n = 0
    for y in range(rows):
        for x in range(cols):
            if kl[y, x] in 'zg':
                k16.pfeil_marke(a, x, y, (110, 225, 250) if kl[y, x] == 'z' else (250, 200, 90), frame, n * 0.25)
                n += 1
    # ------------------------------------------------------------------ Kanten, Front, Leere
    front = k16.front_und_faeden(a, land, frame)
    ak = kontur(land)
    a[ak] = (8, 14, 30)
    mischen(a, kontur(land & ~ak), CYAN, 0.4 + 0.3 * puls(frame, 0.6))
    nah = np.array(Image.fromarray(((land | front) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25))) > 0
    rest = leer & ~front
    k16.straenge(a, rest & ~nah, frame, seed=5555, zonen=((8, 88), (552, 664), (1128, 1208), (100, 1100)), n=6,
                 y_bereich=(60, 440))
    stellen = [(20, 40), (40, 300), (16, 500), (300, 18), (720, 30), (1000, 20), (556, 140), (560, 330),
               (556, 500), (1172, 150), (1172, 340), (1160, 540), (220, 540), (860, 545)]
    k16.fragmente(a, rest & ~nah, frame, seed=5556, stellen=stellen)
    lvl = np.zeros((Hp, Wp), np.uint8)
    lvl[land] = 2
    lvl[front] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
        np.save(os.path.join(KARTE, 'leere.npy'), np.packbits(rest))
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf_ = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf_):
        objs = sorted((o for o in json.load(open(pf_)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.astype(np.int16)
            k4.objekte_zeichnen(img, objs, cache, land, frame, ebenen=ebenen)
            if frame is not None:
                k4.animieren(img, objs, cache, frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 55 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
