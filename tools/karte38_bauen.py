"""Karte 38 - Deva Transit (A03 Nr. 5), Gelaende + Objekte + Animation (4 Bilder).

  python3 tools/karte38_layout.py && python3 tools/karte38_bauen.py && python3 tools/karte38_objekte.py && python3 tools/karte38_bauen.py

Bahnhof nach der Vorlage: helle Ziegelwege (Karte 18 'k'), glatte Bahnsteigplatten mit feiner Kante, dunkles Pflaster
um die Bahnhofsgebaeude, zwei Gleisbaender mit je zwei Gleisen (Schotter, Schwellen, Schienen) quer ueber die ganze
Karte und durch den Baumguertel bis an den Rand. Die Bahnsteige liegen hoeher als das Gleisbett: an der Suedkante eines
Bahnsteigs sieht man die Bahnsteigfront, an der Nordkante nur die Kante mit Schatten; auf jeder Bahnsteigkante eine
weisse Sicherheitslinie und gelbe Noppen. Drei Bahnuebergaenge mit Betonplatten in voller Breite der Ziegelwege (dort
keine Front, die Platten liegen auf Bahnsteighoehe). Leitstreifen auf den Bahnsteigen wie in der Vorlage. Gleise und
Baumguertel sind nicht begehbar (leere.npy), Bahnuebergaenge schon.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte18_bauen as k18

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte38')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte38')
T = 16
N_FRAMES = 4                     # Regel: hoechstens 4 Animationsbilder
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
kb.N_FRAMES = N_FRAMES
k6.N_FRAMES = N_FRAMES
H = k4.H
gross = k18.gross
GELB = np.array(H('#d8b448'), np.uint8)
WEISS = np.array(H('#e6eaee'), np.uint8)


def kontur(m):
    """Randpixel einer Maske, ohne Umlauf ueber den Kartenrand (Pruefliste: kein np.roll)."""
    p = np.pad(m, 1, mode='edge')
    innen = p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return m & ~innen


def verschieben(m, dy, dx):
    out = np.zeros_like(m)
    h, w = m.shape
    out[max(0, dy):h + min(0, dy), max(0, dx):w + min(0, dx)] = m[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
    return out


def gleisbett(a, lay, cols):
    """Schotter, Schwellen und Schienen je Gleis (Mittelzeile aus dem Layout), ueber die ganze Kartenbreite."""
    W = cols * T
    rs = np.random.RandomState(38)
    for (y0, y1) in lay['gleisbaender']:
        Y0, Y1 = y0 * T, (y1 + 1) * T
        bett = a[Y0:Y1].astype(np.float32)
        rausch = rs.randint(-10, 11, bett.shape[:2])[..., None]
        a[Y0:Y1] = np.clip(np.array(H('#3a404c'), np.float32) + rausch * 0.9, 0, 255).astype(np.uint8)
        steine = rs.rand(Y1 - Y0, W) < 0.08
        a[Y0:Y1][steine] = H('#525866')
    for g in lay['gleise']:
        m = g * T + 8                                             # Gleismitte
        for x in range(0, W - 3, 6):                              # Schwellen (Beton) - 3 px breit, 16 px lang
            a[m - 8:m + 8, x:x + 3] = H('#6c6c72')
            a[m - 8:m + 8, x + 2] = H('#4c4c54')
            a[m - 8, x:x + 3] = H('#80808a')
        for ry in (m - 5, m + 4):                                 # Schienen: heller Kopf, dunkler Fuss
            a[ry - 1, :] = H('#9aa0aa')
            a[ry, :] = H('#d6dae2')
            a[ry + 1, :] = H('#4a4e58')


def uebergaenge(a, lay):
    """Bahnuebergaenge: Betonplatten quer ueber das Gleisbett in Breite der Ziegelwege; Schienen laufen sichtbar
    mit Spurrille hindurch."""
    for (y0, y1) in lay['gleisbaender']:
        for (x0, x1) in lay['uebergaenge']:
            X0, X1, Y0, Y1 = x0 * T, (x1 + 1) * T, y0 * T, (y1 + 1) * T
            sub = a[Y0:Y1, X0:X1]
            sub[:] = H('#b4b2c4')
            for y in range(0, Y1 - Y0, 8):                         # Plattenfugen
                sub[y] = H('#8e8ca0')
                sub[y + 1] = H('#c8c6d6')
            sub[:, 0] = H('#6e6c80'); sub[:, -1] = H('#6e6c80')
            for g in lay['gleise']:
                if not (y0 <= g <= y1):
                    continue
                m = g * T + 8 - Y0
                for ry in (m - 5, m + 4):
                    sub[ry - 2] = H('#3a3c48')                     # Spurrille
                    sub[ry - 1] = H('#9aa0aa')
                    sub[ry] = H('#d6dae2')
                    sub[ry + 1] = H('#3a3c48')


def bahnsteigkanten(a, lay, kl):
    """Bahnsteige liegen hoeher als das Gleisbett: Suedkante mit sichtbarer Front (6 px) auf dem Gleisbett, Nordkante
    mit Kantenschatten; auf jeder Kante 2 px heller Kantenstein, weisse Sicherheitslinie, gelbe Noppenreihe.
    An den Bahnuebergaengen keine Front (Platten auf Bahnsteighoehe)."""
    cols = kl.shape[1]
    ueb = np.zeros(cols * T, bool)
    for (x0, x1) in lay['uebergaenge']:
        ueb[x0 * T:(x1 + 1) * T] = True
    stadt_x0, stadt_x1 = lay['stadt'][0] * T, (lay['stadt'][2] + 1) * T
    for (y0, y1) in lay['gleisbaender']:
        for seite, ky in (('nord', y0 * T - 1), ('sued', (y1 + 1) * T)):
            xs = np.arange(cols * T)
            auf = (kl[ky // T, xs // T] != 'h') & (kl[ky // T, xs // T] != 'a')
            gras = kl[ky // T, xs // T] == 'h'                     # Baumguertel: Grasboeschung auf Bahnsteighoehe
            if seite == 'nord':
                for d in range(6):
                    c = np.array(H('#4e7a3a'), np.float32) * (1 - 0.07 * d)
                    a[y0 * T + d, gras] = c.astype(np.uint8)
                a[y0 * T + 6, gras] = (a[y0 * T + 6, gras] * 0.6).astype(np.uint8)
                a[y0 * T - 1, gras] = H('#3c6a2c')
            else:
                a[(y1 + 1) * T - 3:(y1 + 1) * T, gras] = (a[(y1 + 1) * T - 3:(y1 + 1) * T, gras] * 0.7).astype(np.uint8)
                a[(y1 + 1) * T, gras] = H('#3c6a2c')
            for xe in np.nonzero(np.diff(auf.astype(int)) != 0)[0]:  # Bahnsteigende: senkrechte Abschlusskontur
                xk = xe + 1 if auf[xe + 1] else xe
                if seite == 'nord':
                    a[ky - 9:y0 * T + 6, xk] = H('#5a606a')
                else:
                    a[(y1 + 1) * T - 3:ky + 10, xk] = H('#5a606a')
            if seite == 'nord':                                    # Bahnsteig oberhalb: Front faellt nach Sueden ab
                for d in range(6):
                    f = auf & ~ueb
                    c = np.array(H('#7c828e'), np.float32) * (1 - 0.06 * d)
                    if d == 0:
                        c = np.array(H('#c8ccd2'), np.float32)
                    a[y0 * T + d, f] = c.astype(np.uint8)
                a[y0 * T + 6, auf & ~ueb] = (a[y0 * T + 6, auf & ~ueb] * 0.6).astype(np.uint8)
                kante = ky
                richt = -1
            else:                                                  # Bahnsteig unterhalb: Kante wirft Schatten
                a[(y1 + 1) * T - 3:(y1 + 1) * T, auf & ~ueb] = (a[(y1 + 1) * T - 3:(y1 + 1) * T, auf & ~ueb] * 0.7).astype(np.uint8)
                kante = ky
                richt = 1
            f = auf & ~ueb
            for d in range(2):                                     # Kantenstein
                a[kante + richt * d, f] = H('#d4d8de')
            a[kante + richt * 2, f] = H('#8a909a')
            a[kante + richt * 4, f] = WEISS                        # Sicherheitslinie
            a[kante + richt * 5, f] = WEISS
            for x in np.nonzero(auf)[0]:                           # Noppenreihe (gelb)
                if x % 4 in (1, 2):
                    a[kante + richt * 8, x] = GELB
                    a[kante + richt * 9, x] = GELB
                a[kante + richt * 7, x] = (a[kante + richt * 7, x] * 0.85).astype(np.uint8)


def leitstreifen(a, lay):
    """Leitstreifen auf den Bahnsteigen (Vorlage): dunkler Rillenstreifen mit gelber Noppenlinie."""
    for (x0, x1, y) in lay['leitstreifen']:
        X0, X1, m = x0 * T, (x1 + 1) * T, y * T + 8
        a[m - 4:m + 1, X0:X1] = H('#55555a')
        a[m - 4, X0:X1] = H('#3e3e44')
        for x in range(X0, X1):
            if x % 3 == 0:
                a[m - 2, x] = H('#707078')
        a[m + 1:m + 4, X0:X1] = H('#c8a840')
        for x in range(X0, X1):
            if x % 4 in (1, 2):
                a[m + 2, x] = H('#ecd070')
        a[m + 4, X0:X1] = H('#8a7430')


def weichen(a, lay):
    """Je Gleisband ein Gleiswechsel zwischen den beiden Gleisen: flache Schraege (1:3), Schwellen und Schienen nur
    zwischen den beiden Gleisachsen, Weichenzungen enden auf den Gleisen; nicht unter dem stehenden Zug."""
    for bi, (y0, y1) in enumerate(lay['gleisbaender']):
        gl = [g for g in lay['gleise'] if y0 <= g <= y1]
        if len(gl) < 2:
            continue
        m1, m2 = gl[0] * T + 8, gl[1] * T + 8
        dy = m2 - m1
        u = lay['uebergaenge'][0 if bi == 0 else 1]
        x0 = (u[1] + 4) * T                                        # rechts neben einem Uebergang, frei vom Zug
        for t in range(4, dy - 3, 4):                              # Schwellen nur zwischen den Gleisen
            yc, xc = m1 + t, x0 + 3 * t
            a[yc - 1:yc + 1, xc - 7:xc + 8] = H('#6c6c72')
        for off in (-5, 4):                                        # Schienen: Spurweite wie die Gleise
            for t in range(0, dy + 1):
                yy = m1 + off + t
                if not (m1 - 5 <= yy <= m2 + 4):
                    continue
                for xx in range(x0 + 3 * t, x0 + 3 * t + 3):
                    a[yy - 1, xx] = H('#9aa0aa'); a[yy, xx] = H('#d6dae2'); a[yy + 1, xx] = H('#4a4e58')


def gleis_spuren(a, lay, cols):
    """Rost an einzelnen Schwellen und wenige Oelflecken zwischen den Schienen (fest, kein Flimmern)."""
    rs = np.random.RandomState(3838)
    W = cols * T
    for g in lay['gleise']:
        m = g * T + 8
        for x in range(0, W - 3, 6):
            if rs.rand() < 0.18:
                a[m - 8:m + 8, x:x + 3] = (a[m - 8:m + 8, x:x + 3] * np.array((1.02, 0.92, 0.84))).clip(0, 255).astype(np.uint8)
        for _ in range(W // 220):
            cx, rx, ry = rs.randint(20, W - 20), rs.randint(4, 9), rs.randint(2, 3)
            yy, xx = np.ogrid[-ry:ry + 1, -rx:rx + 1]
            f = (yy / max(ry, 1)) ** 2 + (xx / rx) ** 2 <= 1
            sub = a[m - ry:m + ry + 1, cx - rx:cx + rx + 1]
            sub[f] = (sub[f] * 0.72).astype(np.uint8)


def boden_leben(a, kl, frame, leit=()):
    """Abnutzung (Nutzer: Karte lebendiger, dezent): einzelne gesprungene Bahnsteigplatten, Flecken auf Ziegeln und
    Platten, wenige Pfuetzen mit Himmelsspiegelung und wanderndem Glanz. Alles flach und begehbar."""
    rs = np.random.RandomState(38)
    rows, cols = kl.shape
    frei = lambda x, y: kl[y, x] in 'kp' and all(kl[y + dy, x + dx] in 'kp' for dy in (-1, 0, 1) for dx in (-1, 0, 1))
    gesperrt = {(x, y + d) for (x0, x1, y) in leit for x in range(x0 - 1, x1 + 2) for d in (-1, 0, 1)}
    kand = [(x, y) for y in range(2, rows - 2) for x in range(2, cols - 2) if frei(x, y) and (x, y) not in gesperrt]
    rs.shuffle(kand)
    for (x, y) in kand[:40]:                                       # Risse in Platten (nur 'p')
        if kl[y, x] != 'p':
            continue
        X, Y = x * T, y * T
        px, py = X + rs.randint(2, 6), Y + rs.randint(2, 5)
        for i in range(rs.randint(7, 12)):
            a[py, px] = (a[py, px] * 0.68).astype(np.uint8)
            px += 1; py += rs.choice((0, 1, 1))
            if px >= X + 15 or py >= Y + 15:
                break
    for (x, y) in kand[40:70]:                                     # Flecken
        cx, cy, r = x * T + 8, y * T + 8, rs.randint(3, 6)
        yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
        f = (yy ** 2 + xx ** 2 <= r * r) & (rs.rand(2 * r + 1, 2 * r + 1) < 0.8)
        sub = a[cy - r:cy + r + 1, cx - r:cx + r + 1]
        sub[f] = (sub[f] * 0.9).astype(np.uint8)
    f_ = frame or 0
    gesetzt = []
    for (x, y) in kand[70:]:                                       # Pfuetzen (wenige, Abstand)
        if len(gesetzt) >= 6:
            break
        if any(abs(x - gx) + abs(y - gy) < 14 for gx, gy in gesetzt):
            continue
        gesetzt.append((x, y))
        cx, cy = x * T + 8, y * T + 8
        rx, ry = rs.randint(9, 14), rs.randint(4, 6)
        yy, xx = np.ogrid[-ry:ry + 1, -rx:rx + 1]
        f = (yy / ry) ** 2 + (xx / rx) ** 2 <= 1
        sub = a[cy - ry:cy + ry + 1, cx - rx:cx + rx + 1]
        sub[f] = np.clip(sub[f] * 0.55 + np.array((120, 140, 170)) * 0.45, 0, 255).astype(np.uint8)
        rand_ = f & ~((yy / max(ry - 1, 1)) ** 2 + (xx / max(rx - 1, 1)) ** 2 <= 1)
        sub[rand_] = (sub[rand_] * 0.85).astype(np.uint8)
        gx = -rx + 3 + (f_ * 4 + x) % (2 * rx - 6)                 # Glanzstrich wandert
        for d in range(3):
            yy_, xx_ = -1 + (d % 2), gx + d
            if f[yy_ + ry, xx_ + rx]:
                sub[yy_ + ry, xx_ + rx] = (220, 230, 240)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    a = k18.textur('k', cols, rows)                                  # Ziegelwege
    platten = gross(kl == 'p')
    pt = np.clip(k18.textur('v', cols, rows).astype(np.float32) * np.array((1.0, 1.03, 1.02)), 0, 255).astype(np.uint8)
    a[platten] = pt[platten]
    for g in range(0, Hp, T):                                         # Plattenraster
        a[g, :][platten[g, :]] = (a[g, :][platten[g, :]] * 0.9).astype(np.uint8)
    for g in range(0, Wp, T):
        a[:, g][platten[:, g]] = (a[:, g][platten[:, g]] * 0.9).astype(np.uint8)
    rp = kontur(platten)                                              # feine Plattenkante (Licht oben links)
    a[rp] = H('#7e868c')
    a[kontur(platten & ~rp) & verschieben(rp, 1, 0)] = H('#dfe4e4')
    dunkel = gross(kl == 'd')
    dt = np.clip(k18.textur('k', cols, rows).astype(np.float32) * np.array((0.40, 0.50, 0.60)), 0, 255).astype(np.uint8)
    a[dunkel] = dt[dunkel]
    rd = kontur(dunkel)
    a[rd] = H('#2c3644')
    wald = gross(kl == 'h')
    a[wald] = k18.textur('n', cols, rows)[wald]
    gleisbett(a, lay, cols)
    gleis_spuren(a, lay, cols)
    weichen(a, lay)
    uebergaenge(a, lay)
    bahnsteigkanten(a, lay, kl)
    leitstreifen(a, lay)
    boden_leben(a, kl, frame, lay['leitstreifen'])
    land = np.zeros((Hp, Wp), bool)
    land[T:-T, T:-T] = True
    lvl = np.ones((Hp, Wp), np.uint8)
    gleis = gross(kl == 'a')
    for (y0, y1) in lay['gleisbaender']:
        for (x0, x1) in lay['uebergaenge']:
            gleis[y0 * T:(y1 + 1) * T, x0 * T:(x1 + 1) * T] = False
    leere = wald | gleis                                              # Baumguertel und Gleise gesperrt
    lvl[leere] = 0
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
        np.save(os.path.join(KARTE, 'leere.npy'), np.packbits(leere))
    img = Image.fromarray(a).convert('RGBA')
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = np.ones((Hp, Wp), np.int16)
            ebenen[gross(kl == 'a')] = 0                               # Schatten nicht auf das tiefere Gleisbett
            k4.objekte_zeichnen(img, objs, cache, land, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
            k6.animieren_k6(img, objs, cache, frame or 0)
    a = np.array(img.convert('RGB'))
    if os.path.exists(pf):                                            # Fahrdraehte der Oberleitung: in Auslegerhoehe
        for y_ in sorted({o['y'] for o in json.load(open(pf)) if o.get('oberleitung')}):   # ueber die ganze Breite
            for dy, f in ((7, 0.15), (18, 0.25)):
                yy = y_ + dy
                if 0 <= yy < Hp:
                    a[yy] = (a[yy] * f + np.array((40, 44, 52)) * (1 - f)).astype(np.uint8)
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
        if not os.path.exists(pf):
            img.save(os.path.join(KARTE, 'terrain_basis.png'))
    print('Karte 38 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
