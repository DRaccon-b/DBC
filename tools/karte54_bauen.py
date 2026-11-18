"""Karte 54 - D-Reaper Kernel (A03 Nr. 21, letzte Bossarena von A03), Gelaende nach maps/karte54/layout.json.

  python3 tools/karte54_layout.py && python3 tools/karte54_bauen.py

Im Inneren der Kernkugel (Nutzer): Rundum die gewoelbte Innenwand aus pulsierenden D-Reaper-Blasenhaufen (Karte 52,
tools/dreaper.py, Originalgroesse), nach aussen dunkler (Woelbung, Licht kommt aus der Mitte), weicher Schatten der Wand auf
der Membran. Boden: rosa, durchscheinende Membran mit Zellwaenden und pulsierenden Adern, zur Mitte heller. Durch Fenster in
der Membran sieht man tief unten Shinjuku (Karte 52, aus deren Animation, halber Massstab, roter Dunst), mit dunkler
Tiefenkante innen und ausgefranster, gluehender Membranlippe. Zugang im Sueden durch einen Riss in der Kugelwand.
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte33_bauen as k33
import dreaper

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte54')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte54')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = kb.N_FRAMES = k33.N_FRAMES = N_FRAMES
H = k4.H
k4.SCHATTEN = {'farbe': (70, 16, 40), 'dx': 0.3, 'dy': 0.15, 'kern': 100, 'wurf': (66, 52)}
k4.RASTER45 = True
MASSSTAB = 2                                                          # Shinjuku liegt tief unten: halb so gross
DUNST = np.array((120, 50, 80), np.float32)                          # roter Dunst im Inneren des D-Reaper
_BLICK = {}


def maske45(cls, zeichen, cols, rows):
    """Kachelmaske am 45-Grad-Raster (weichgezeichnet, Schwelle 50 %, Regel 6b)."""
    return k4.weich(k4.zell_maske(cls, zeichen, cols, rows), 5, 0.0, 7, 0.5)


def abstand(m, n):
    """Abstand (Pixel, bis n) jedes Pixels ausserhalb von m zur Maske m (Kartenrand fortgesetzt)."""
    d = np.full(m.shape, n + 1, np.int16)
    cur = m.copy()
    for i in range(1, n + 1):
        p_ = np.pad(cur, 1, mode='edge')
        nb = cur | p_[:-2, 1:-1] | p_[2:, 1:-1] | p_[1:-1, :-2] | p_[1:-1, 2:]
        d[nb & ~cur] = i
        cur = nb
    d[m] = 0
    return d


def membran(Hh, W, mitte_px, radius_px, frame):
    """Rosa Membran: Grundton zur Mitte heller, Zellwaende (Rauschbaender), feine Adern, die im Takt pulsieren."""
    f = (frame or 0) % N_FRAMES
    yy, xx = np.mgrid[0:Hh, 0:W].astype(np.float32)
    r = np.clip(np.hypot(xx - mitte_px[0], yy - mitte_px[1]) / radius_px, 0, 1.2)
    innen, aussen = np.array((214, 124, 152), np.float32), np.array((150, 62, 96), np.float32)
    a = innen[None, None] * (1 - r[..., None] ** 1.6) + aussen[None, None] * r[..., None] ** 1.6
    n0 = dreaper._rauschen(Hh, W, 3, 5401) - 0.5
    a += n0[..., None] * 10
    n1 = dreaper._rauschen(Hh, W, 7, 5402)
    zelle = np.abs(n1 - 0.5) < 0.02                                   # Zellwaende
    a[zelle] *= 0.9
    a[np.roll(zelle, 1, 0) & ~zelle] += 14                            # Lichtkante unter jeder Wand (Licht von oben)
    puls = 0.5 + 0.5 * math.sin(2 * math.pi * f / N_FRAMES)
    # Nutzer: zur Mitte hin staerker pulsieren - eine Welle laeuft von der Mitte nach aussen (4 Bilder, nahtlos)
    welle = 0.5 + 0.5 * np.sin(2 * math.pi * (f / N_FRAMES - r * 0.9))
    nah = np.clip(1 - r, 0, 1) ** 1.8
    a += (welle * nah)[..., None] * np.array((46, 12, 24), np.float32)
    n2 = dreaper._rauschen(Hh, W, 16, 5403)
    ader = np.abs(n2 - 0.5) < 0.016
    st = (welle * (0.4 + 0.6 * nah))[ader][:, None]
    a[ader] = np.array((140, 26, 58)) + st * np.array((110, 60, 60))
    kern = np.abs(n2 - 0.5) < 0.005
    a[kern] = np.array((220, 100, 130)) + (welle * (0.4 + 0.6 * nah))[kern][:, None] * np.array((35, 70, 60))
    rs = np.random.RandomState(5404)                                  # kleine Glanzpunkte (feuchte Oberflaeche)
    for _ in range(Hh * W // 900):
        y, x = rs.randint(1, Hh - 1), rs.randint(1, W - 1)
        a[y, x] = a[y, x] * 0.4 + np.array((255, 220, 230)) * 0.6
    return np.clip(a, 0, 255).astype(np.uint8)


def blick(karte, frame):
    """Shinjuku tief unten: Bild aus der Animation der Quellkarte, halber Massstab, entsaettigt, roter Dunst."""
    s = (karte, frame)
    if s not in _BLICK:
        q = Image.fromarray(k33.quellbild(karte, frame))
        q = q.resize((q.width // MASSSTAB, q.height // MASSSTAB), Image.BOX)
        b = np.array(q).astype(np.float32)
        b = b * 0.7 + b.mean(-1, keepdims=True) * 0.3
        b = b * 0.5 + DUNST * 0.5
        b *= 0.85
        _BLICK[s] = np.clip(b, 0, 255).astype(np.uint8)
    return _BLICK[s]


def komponenten(m):
    """Zusammenhaengende Teile einer Maske (4er-Nachbarschaft), sortiert nach (oben, links) -> [(ys, xs), ...]."""
    seen = np.zeros_like(m)
    teile = []
    for y0, x0 in zip(*np.nonzero(m)):
        if seen[y0, x0]:
            continue
        st, pts = [(y0, x0)], []
        seen[y0, x0] = True
        while st:
            y, x = st.pop()
            pts.append((y, x))
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < m.shape[0] and 0 <= xx < m.shape[1] and m[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True
                    st.append((yy, xx))
        p_ = np.array(pts)
        teile.append((p_[:, 0], p_[:, 1]))
    return teile


def fenster(a, lay, fm, frame):
    """Fenster in der Membran: unten Shinjuku, innen dunkle Tiefenkante, aussen eine ausgefranste, gluehende Lippe."""
    f = (frame or 0) % N_FRAMES
    teile = komponenten(fm)
    b = blick(lay['blick']['karte'], frame)
    for i, (ys, xs) in enumerate(teile):
        vx, vy = lay['blick']['versatz'][i % len(lay['blick']['versatz'])]
        x0, y0 = xs.min(), ys.min()
        sy = np.clip(vy + ys - y0, 0, b.shape[0] - 1)
        sx = np.clip(vx + xs - x0, 0, b.shape[1] - 1)
        a[ys, xs] = b[sy, sx]
    innen = abstand(~fm, 6)                                           # Tiefe: zum Rand hin dunkler
    for k_ in range(1, 6):
        m_ = fm & (innen == k_)
        a[m_] = (a[m_] * (0.35 + 0.12 * k_)).astype(np.uint8)
    aussen = abstand(fm, 5)
    puls = 0.6 + 0.4 * math.sin(2 * math.pi * f / N_FRAMES)
    rs = np.random.RandomState(5405)
    zack = rs.rand(*fm.shape) < 0.35                                  # ausgefranste Lippe
    for k_, (farbe, st) in enumerate((((120, 20, 50), 0.85), ((255, 210, 225), 0.95), ((250, 140, 170), 0.75),
                                      ((215, 80, 120), 0.5), ((180, 50, 90), 0.3)), 1):
        m_ = (aussen == k_) & (zack if k_ >= 4 else True)          # dunkle Schnittkante, dann gluehende Lippe
        al = st * puls
        a[m_] = np.clip(a[m_] * (1 - al) + np.array(farbe) * al, 0, 255).astype(np.uint8)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    mitte = (lay['mitte'][0] * T, lay['mitte'][1] * T)
    rad = lay['radius'] * T
    wand = maske45(cls, 'o', cols, rows)
    fm = maske45(cls, 'f', cols, rows)
    boden = ~wand
    a = membran(Hp, Wp, mitte, rad, frame)
    # Schatten der Kugelwand auf der Membran (weich, oben staerker: Licht aus der Mitte faellt nach aussen ab)
    dw = abstand(wand, 10)
    for k_ in range(1, 11):
        m_ = boden & (dw == k_)
        a[m_] = (a[m_] * (0.55 + 0.045 * k_)).astype(np.uint8)
    fenster(a, lay, fm & boden, frame)
    a[wand] = (60, 8, 22)                                             # Tiefe zwischen den Blasen
    dreaper.masse(a, wand, frame, 54)                                 # Kugelwand: ganze Blasenhaufen, pulsierend
    yy, xx = np.mgrid[0:Hp, 0:Wp].astype(np.float32)
    rr = np.hypot(xx - mitte[0], yy - mitte[1])
    dunkel = np.clip((rr - rad) / (9.0 * T), 0, 1)                    # Woelbung: nach aussen dunkler
    a[wand] = (a[wand] * (1 - 0.55 * dunkel[wand])[..., None]).astype(np.uint8)
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[wand] = 9                                                     # Kugelwand gesperrt
    lvl[fm & boden] = 0                                               # Fenster: Leere (gesperrt)
    for tp in lay['teleporter']:
        lvl[tp['y'] * T:(tp['y'] + tp['h']) * T, tp['x'] * T:(tp['x'] + tp['b']) * T] = 1
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'leere.npy'), np.packbits(fm & boden))
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
        np.save(os.path.join(KARTE, 'treppe.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            k4.objekte_zeichnen(img, objs, cache, boden & ~fm, frame, ebenen=lvl.astype(np.int16))
            k4.animieren(img, objs, cache, frame or 0)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 54 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
