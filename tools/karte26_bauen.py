"""Karte 26 - The Kaiser's Fortress (A02): das Innere des Kaiser-Flaggschiffs (Karte 25).

Boden aus den genieteten Stahlplatten von Karte 13 (m_*), in das Blaugrau der Vorlage umgefaerbt; Gitterboden aus den
Gitterkacheln von Karte 13 (z_*); Thronpodest heller mit Stufe; Huelle aus dunklen Stahlbloecken (Karte 13, g_*)
mit Mauerkrone und Kontaktschatten (Licht von oben links); Rueckwaende als Paneelwand mit lila Zierleiste oben,
Fugen, roten Statuslichtern und Sockelleiste; roter Warnstreifen (schwarz/rot schraffiert); Teleporter (Karte 18).

  python3 tools/karte26_layout.py && python3 tools/karte26_bauen.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte18_bauen as k18
import karte22_bauen as k22

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte26')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte26')
B13 = os.path.join(ROOT, 'assets', 'karte13', 'basis')
T = 16
N_FRAMES = 4
H = k4.H


def textur(art, cols, rows, faktor=(1, 1, 1), plus=(0, 0, 0)):
    ks = [np.array(Image.open(os.path.join(B13, '%s_%d.png' % (art, v))).convert('RGB')).astype(np.float32) for v in range(5)]
    t = np.zeros((rows * T, cols * T, 3), np.float32)
    for y in range(rows):
        for x in range(cols):
            t[y * T:(y + 1) * T, x * T:(x + 1) * T] = ks[kb.variante(x, y)]
    return np.clip(t * np.array(faktor) + np.array(plus), 0, 255).astype(np.uint8)


def maske(cls, arten):
    return np.kron(np.array([[c in arten for c in z] for z in cls]), np.ones((T, T), bool))


def paneelwand(a, wm, frame):
    """Rueckwand: je zusammenhaengendes Wandstueck einer Spalte von oben nach unten: lila Zierleiste, Paneele mit
    senkrechten Fugen alle 32 px, Lichtkante oben links, rote Statuslichter (pulsieren), Sockelleiste, Schatten."""
    Hh, W = wm.shape
    f = frame or 0
    PAN, PAN_H, PAN_D, FUGE = H('#3c4258'), H('#4c546c'), H('#2c3144'), H('#1c2030')
    LILA, LILA_H, SOCKEL, SOCKEL_H = H('#4a2c66'), H('#7a4ca0'), H('#22263a'), H('#3a4058')
    for x in range(W):
        col = wm[:, x]
        y = 0
        while y < Hh:
            if not col[y]:
                y += 1; continue
            y0 = y
            while y < Hh and col[y]:
                y += 1
            y1 = y                                                   # [y0, y1)
            for yy in range(y0, y1):
                d = yy - y0
                rest = y1 - 1 - yy
                if d < 3:
                    c = LILA_H if d == 0 else LILA
                elif rest < 4:
                    c = SOCKEL_H if rest == 3 else SOCKEL
                else:
                    c = PAN_H if (d - 3) % 12 == 0 else (PAN_D if (d - 3) % 12 == 11 else PAN)
                    if x % 32 in (0, 31):
                        c = FUGE
                    elif x % 32 == 1:
                        c = PAN_H
                a[yy, x] = c
            mitte = y0 + 3 + max(1, (y1 - y0 - 7) // 2)              # rote Statuslichter
            if x % 64 in (14, 15) and y1 - y0 > 10:
                p = (0.7, 1.0, 1.25, 1.0)[f % 4]
                a[mitte:mitte + 2, x] = np.clip(np.array(H('#c02838'), np.float32) * p, 0, 255).astype(np.uint8)
            if x % 64 in (40, 41, 42, 43, 44, 45) and y1 - y0 > 12:  # kleine Anzeige
                a[mitte - 1:mitte + 2, x] = H('#1e4a52') if (x + f) % 3 else H('#3aa0a8')
            if y1 < Hh and not wm[y1, x]:                            # Schatten der Wand auf dem Boden
                for s in range(1, 5):
                    if y1 + s - 1 < Hh and not wm[y1 + s - 1, x]:
                        a[y1 + s - 1, x] = (a[y1 + s - 1, x] * (0.55 + 0.1 * s)).astype(np.uint8)


def huelle_kanten(a, hm, boden):
    """Mauerkrone der Huelle an jedem Boden-Rand (heller Rand, dunkle Kontur) und Kontaktschatten auf dem Boden
    (Licht von oben links: Schatten unter Nord- und rechts neben West-Kanten)."""
    nb = lambda m, dy, dx: np.roll(np.roll(m, dy, 0), dx, 1)
    rand = hm & (nb(boden, 1, 0) | nb(boden, -1, 0) | nb(boden, 0, 1) | nb(boden, 0, -1))
    rand2 = hm & ~rand & (nb(rand, 1, 0) | nb(rand, -1, 0) | nb(rand, 0, 1) | nb(rand, 0, -1))
    a[rand2] = H('#4c5470')
    a[rand] = H('#151824')
    for d in range(1, 6):
        sch = boden & (nb(hm, d, 0) | nb(hm, 0, d))
        a[sch] = (a[sch] * (0.6 + 0.07 * d)).astype(np.uint8)


def warnstreifen(a, sm):
    ys, xs = np.nonzero(sm)
    for y, x in zip(ys, xs):
        a[y, x] = H('#a8202c') if ((x + y) // 6) % 2 == 0 else H('#1a1418')
    y0, y1 = ys.min(), ys.max()
    a[y0, xs] = H('#d03a44'); a[y1, xs] = H('#5a1018')


def podest(a, pm):
    """Thronpodest: Stufe nach Sueden (6 px Front mit Lichtkante, Schatten darunter)."""
    Hh, W = pm.shape
    unten = pm & ~np.roll(pm, -1, 0)
    ys, xs = np.nonzero(unten)
    for y, x in zip(ys, xs):
        for d in range(1, 10):
            yy = y + d
            if yy >= Hh or pm[yy, x]:
                break
            if d == 1:
                a[yy, x] = H('#8a94b0')
            elif d < 7:
                a[yy, x] = H('#3a4058') if x % 32 not in (0, 31) else H('#262a3c')
            else:
                a[yy, x] = (a[yy, x] * 0.6).astype(np.uint8)


TEPPICHE = [(272, 150, 336, 238)]       # Thronsaal: x 272..336 (4 Kacheln, Mitte 304), vom Podest bis vor den Holo-Tisch


# Zellentrakt Mitte links (Nutzer: Zellen mit Gittern). Waagerecht: (x0, x1, Fusslinie y in px, Tuer-Mitte x | None);
# senkrecht: (x, y0, y1) in px - Gitter von der Seite (Pfostenreihe).
GITTER_W = [(5 * T, 13 * T, 35 * T, 9 * T), (15 * T, 23 * T, 35 * T, 19 * T), (25 * T, 33 * T, 35 * T, 29 * T),
            (5 * T, 13 * T, 42 * T, 9 * T), (25 * T, 33 * T, 42 * T, 29 * T)]
GITTER_S = []                                    # Seiten der Eckzellen sind jetzt Wand mit Decke (Nutzer)


def zellengitter(a, frame):
    """Eisengitter frontal: Stangen 2 px alle 6 px, 26 px hoch, Ober-/Mittel-/Unterholm, Tuer mit Rahmen und
    rot blinkendem Schloss; Licht von links (helle Kante), Kontaktschatten am Boden. Seitliche Gitter als
    Pfostenreihe von oben (schmal)."""
    D, M, L, HL = H('#1a1c26'), H('#3a3e52'), H('#5a6078'), H('#8a90a8')
    hoch = 26
    f = frame or 0
    for (x0, x1, yb, tuer) in GITTER_W:
        y0 = yb - hoch
        a[yb:yb + 3, x0:x1] = (a[yb:yb + 3, x0:x1] * 0.6).astype(np.uint8)          # Kontaktschatten
        for x in range(x0 + 1, x1 - 1, 6):
            a[y0:yb, x] = L; a[y0:yb, x + 1] = D
            a[y0:yb, x - 1] = (a[y0:yb, x - 1] * 0.8).astype(np.uint8) if x > x0 + 1 else a[y0:yb, x - 1]
        for yy in (y0, y0 + hoch // 2, yb - 3):
            a[yy:yy + 3, x0:x1] = M; a[yy, x0:x1] = HL; a[yy + 2, x0:x1] = D
        a[y0:yb, x0:x0 + 2] = M; a[y0:yb, x1 - 2:x1] = D                          # Endpfosten
        if tuer is not None:
            t0, t1 = tuer - 14, tuer + 14
            a[y0 - 2:yb, t0:t0 + 3] = M; a[y0 - 2:yb, t0] = HL
            a[y0 - 2:yb, t1 - 3:t1] = D
            a[y0 - 2:y0 + 1, t0:t1] = M; a[y0 - 2, t0:t1] = HL
            ly = y0 + hoch // 2 - 3                                                  # Schloss mit Statuslicht
            a[ly:ly + 7, t1 - 9:t1 - 3] = H('#2a2e3e')
            a[ly + 2:ly + 4, t1 - 7:t1 - 5] = H('#e03040') if f % 2 == 0 else H('#801820')
    for (x, y0, y1) in GITTER_S:
        a[y0:y1, x - 1:x + 2] = M; a[y0:y1, x - 1] = HL; a[y0:y1, x + 1] = D
        for y in range(y0, y1, 6):
            a[y:y + 2, x - 2:x + 3] = L
        a[y0:y1, x + 2:x + 4] = (a[y0:y1, x + 2:x + 4] * 0.65).astype(np.uint8)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Hp, Wp = rows * T, cols * T
    boden = textur('m', cols, rows, (0.86, 0.8, 0.86), (2, 0, 10))          # Stahlplatten, blaugrau wie die Vorlage
    hell = textur('m', cols, rows, (1.2, 1.1, 1.15), (10, 8, 16))           # Podest
    gitter = textur('z', cols, rows, (0.62, 0.62, 0.72), (0, 0, 6))
    huelle = textur('g', cols, rows, (0.36, 0.38, 0.46), (0, 0, 0))
    a = boden.copy()
    hm, gm, pm = maske(cls, '#'), maske(cls, 'g'), maske(cls, 'p')
    a[gm] = gitter[gm]
    a[pm] = hell[pm]
    a[hm] = huelle[hm]
    bm = ~hm
    huelle_kanten(a, hm, bm)
    podest(a, pm)
    tm = np.zeros((Hp, Wp), bool)                                    # roter Teppich vom Saal zum Thron (Achse x=304)
    for (x0, y0, x1, y1) in TEPPICHE:
        tm[y0:y1, x0:x1] = True
    k22.teppich(a, tm)
    stufe = tm & np.roll(pm, 1, 0) & ~pm                             # Stufe des Podests auch auf dem Teppich sichtbar
    for d in range(1, 8):
        st = tm & np.roll(pm, d, 0) & ~pm
        a[st] = (a[st] * (0.62 if d > 1 else 1.25)).clip(0, 255).astype(np.uint8)
    wm = maske(cls, 'W')
    paneelwand(a, wm, frame)
    warnstreifen(a, maske(cls, 'r'))
    zellengitter(a, frame)
    for tp in lay['teleporter']:
        k18.teleporter(a, tp, frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = np.where(hm | wm, 9, 1).astype(np.uint8)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(hm | wm))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            k4.objekte_zeichnen(img, objs, cache, ~(hm | wm), frame, ebenen=lvl.astype(np.int16))
            k4.animieren(img, objs, cache, frame or 0)
            kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 26 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
