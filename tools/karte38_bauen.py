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
    uebergaenge(a, lay)
    bahnsteigkanten(a, lay, kl)
    leitstreifen(a, lay)
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
