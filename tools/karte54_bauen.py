"""Karte 54 - D-Reaper Kernel (A03 Nr. 21), Gelaende nach maps/karte54/layout.json.

  python3 tools/karte54_layout.py && python3 tools/karte54_bauen.py && python3 tools/karte54_objekte.py && python3 tools/karte54_bauen.py

Dunkler violetter Metallplattenboden, erhoehter Gewebefels ringsum (gesperrt, Front nach Sueden, schmale Seitenkanten),
zwei massive Mauerringe (Abdeckung mit rosa Fugen, Wand mit Schattenfuge, Fusskante, Bodenschatten), rote Gewebebahnen als
flacher, begehbarer D-Reaper-Belag (pulsierende Adern, tools/dreaper.py), dunkles Becken mit Steinlippe und wandernden
Lichtstreifen (gesperrt), Teleporter-Ausgang durch den unteren Rand. Bodenkanten am 45-Grad-Raster.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20
import karte48_bauen as k48
import dreaper

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte54')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte54')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
kb.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.SCHATTEN = {'farbe': (18, 10, 22), 'dx': 0.3, 'dy': 0.15, 'kern': 100, 'wurf': (66, 52)}
k4.RASTER45 = True
k4.FELS['kern54'] = ['#1c1220', '#2a1a2e', '#3a2440', '#4c3052', '#5e3c64', '#744a78', '#8c5a8c']
LIPPE = ['#5a2a44', '#6c3050', '#80385c', '#943e66', '#a84a72', '#bc5a80']
FRONT = 16                               # Reihe 3 bleibt als Boden zwischen Rand und Mauerring sichtbar
SEITE = 6
faerben = k48.faerben


def texturen(cols, rows):
    basis = os.path.join(ROOT, 'assets', 'basis')
    kies = os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png')
    Hh, W = rows * T, cols * T                                        # Metallboden: 32er-Platten, feine Fugen, Rauschen
    n = dreaper._rauschen(Hh, W, 3, 540) - 0.5
    boden = np.zeros((Hh, W, 3), np.float32) + np.array((52, 38, 56), np.float32)
    boden += n[..., None] * 8
    yy, xx = np.mgrid[0:Hh, 0:W]
    boden[(yy % 32 == 0) | (xx % 32 == 0)] = (42, 30, 46)
    boden[(yy % 32 == 1) | (xx % 32 == 1)] += 5
    boden = np.clip(boden, 0, 255).astype(np.uint8)
    rs = np.random.RandomState(54)                                    # kleine Winkelmarken wie in der Vorlage
    for y in range(rows):
        for x in range(cols):
            if rs.rand() < 0.35:
                px, py = x * T + rs.randint(3, 11), y * T + rs.randint(3, 11)
                boden[py, px:px + 3] = (70, 54, 76)
                boden[py:py + 3, px] = (70, 54, 76)
    return {
        'g': boden,
        'h': flaeche(k6.kacheln(kies, 5, faerben((44, 28, 46), (92, 60, 90), 0.3, 0.6)), cols, rows),   # Gewebefels
    }


def mauern(a, kl, cols, rows):
    """Mauerringe: Abdeckung (Kachel) mit Licht-/Schattenkante und rosa Fugen, Wand (8 px) unter Suedkanten, Bodenschatten,
    schmaler Schatten rechts neben senkrechten Mauern. Gibt die gesperrte Pixelmaske zurueck."""
    Hh, W = a.shape[:2]
    m = np.kron(kl == 'm', np.ones((T, T), int)).astype(bool)
    sperre = m.copy()
    yy, xx = np.mgrid[0:Hh, 0:W]
    cap = np.array((92, 60, 96), np.float32)
    a[m] = cap
    a[m & ((yy % T) == 7) & ((xx % T) >= 5) & ((xx % T) <= 10)] = (168, 92, 124)        # rosa Fugenmarken
    a[m & ((xx % T) == 7) & ((yy % T) >= 5) & ((yy % T) <= 10) & ~((yy % T) == 7)] = (150, 84, 116)
    p_ = np.pad(m, 1)
    oben = m & ~p_[:-2, 1:-1]
    links = m & ~p_[1:-1, :-2]
    rechts = m & ~p_[1:-1, 2:]
    unten = m & ~p_[2:, 1:-1]
    a[oben | links] = (126, 88, 128)
    a[rechts] = (64, 40, 68)
    for y in range(Hh):                                              # Wand unter den Suedkanten
        xs = np.nonzero(unten[y])[0]
        if not len(xs):
            continue
        for d in range(1, 9):
            yy_ = y + d
            if yy_ >= Hh:
                break
            ok = xs[~m[yy_, xs]]
            if d == 1:
                a[yy_, ok] = (34, 20, 38)                            # Schattenfuge unter der Abdeckung
            elif d < 8:
                c = np.array((66, 42, 70), np.float32) * (1.0 - 0.04 * d)
                a[yy_, ok] = c
                a[yy_, ok[(ok % 8 == (0 if (d // 3) % 2 else 4))]] = (48, 30, 52)
                if d == 4:
                    a[yy_, ok] = (52, 32, 56)
            else:
                a[yy_, ok] = (28, 16, 32)                            # Fusskante
            sperre[yy_, ok] = True
        for d in range(9, 12):                                       # Bodenschatten
            yy_ = y + d
            if yy_ < Hh:
                ok = xs[~m[yy_, xs] & ~sperre[yy_, xs]]
                a[yy_, ok] = (a[yy_, ok] * (0.62 + 0.1 * (d - 9))).astype(np.uint8)
    for d in range(1, 4):                                            # Schatten rechts neben senkrechten Mauern
        sh = np.zeros_like(m)
        sh[:, d:] = rechts[:, :-d]
        sh &= ~sperre
        a[sh] = (a[sh] * (0.6 + 0.1 * d)).astype(np.uint8)
    return sperre


def becken(a, maske, frame):
    """Dunkles Becken: Steinlippe auf dem Boden, Tiefe zum Rand hin dunkler, wandernde Lichtstreifen (4 Bilder, nahtlos)."""
    f = (frame or 0) % 4
    Hh, W = maske.shape
    yy, xx = np.mgrid[0:Hh, 0:W]
    d = np.zeros((Hh, W), np.float32)
    inn = maske.copy()
    for i in range(1, 9):                                            # Abstand zum Ufer (bis 8 px)
        p_ = np.pad(inn, 1)
        inn = inn & p_[:-2, 1:-1] & p_[2:, 1:-1] & p_[1:-1, :-2] & p_[1:-1, 2:]
        d += inn
    farbe = np.array((22, 30, 48), np.float32)[None, None] * (1.0 - 0.025 * d[..., None]) + \
        np.array((40, 52, 74), np.float32)[None, None] * (0.25 * (8 - d[..., None]) / 8)
    zuf = ((xx // 20) * 7919 + (yy // 10) * 104729) % 13                   # unregelmaessig statt Raster
    welle = (yy % 10 == (zuf % 10)) & (((xx + 5 * f + zuf * 3) % 20) < 5) & (d >= 3) & (zuf % 3 != 0)
    farbe[welle] = (44, 58, 82)
    glanz = (yy % 10 == ((zuf + 5) % 10)) & (((xx + 5 * f + zuf * 7) % 40) < 3) & (d >= 5) & (zuf % 4 == 1)
    farbe[glanz] = (80, 46, 70)                                      # roter Widerschein der Masse
    a[maske] = np.clip(farbe[maske], 0, 255).astype(np.uint8)
    p_ = np.pad(maske, 3)
    lippe = np.zeros_like(maske)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if abs(dy) + abs(dx) <= 3:
                lippe |= p_[3 + dy:3 + dy + Hh, 3 + dx:3 + dx + W]
    lippe &= ~maske
    a[lippe] = (84, 66, 92)
    a[lippe & ~np.roll(lippe, -1, 0)] = (54, 40, 60)
    rand = maske & ~(np.pad(maske, 1)[:-2, 1:-1] & np.pad(maske, 1)[2:, 1:-1])
    a[rand] = (14, 18, 30)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    kl = np.array([list(r) for r in cls])
    Wp, Hp = cols * T, rows * T
    tex = texturen(cols, rows)
    a = tex['g'].copy()
    rand = weich(zell_maske(cls, 'h', cols, rows), 5, 0.0, 9, 0.5)
    a[rand] = tex['h'][rand]
    rs_ = np.random.RandomState(9)                                   # rote Adern im Gewebefels
    n3 = dreaper._rauschen(Hp, Wp, 14, 541)
    a[rand & (np.abs(n3 - 0.5) < 0.03)] = (96, 30, 52)
    wand = k4.hoehenkanten(a, rand, 'kern54', FRONT, SEITE, LIPPE, np.zeros((Hp, Wp), bool), 54, berg=False)
    gewebe = weich(zell_maske(cls, 'f', cols, rows), 5, 0.0, 7, 0.5)
    dreaper.masse(a, gewebe, frame, 54, flach=True)
    bk = weich(zell_maske(cls, 'w', cols, rows), 5, 0.0, 11, 0.5)
    becken(a, bk, frame)
    sperre_m = mauern(a, kl, cols, rows)
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = np.ones((Hp, Wp), np.uint8)
    lvl[rand] = 9                                                    # Felsrand: gesperrt (auch in der Kollision)
    lvl[wand] = 9
    lvl[sperre_m] = 9
    for tp in lay['teleporter']:
        lvl[tp['y'] * T:(tp['y'] + tp['h']) * T, tp['x'] * T:(tp['x'] + tp['b']) * T] = 1
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand | sperre_m))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(bk))
        np.save(os.path.join(KARTE, 'treppe.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.copy().astype(np.int16)
            k4.objekte_zeichnen(img, objs, cache, ~(wand | sperre_m), frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
            kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 54 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
