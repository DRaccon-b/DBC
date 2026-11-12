"""Gebaeude fuer Karte 31 (Highton View Terrace) -> assets/objekte/karte31/gebaeude/<art>.png, uebersicht.png

  python3 tools/karte31_gebaeude.py

Nutzer: "Gebaeude schlau generieren, manche zur Haelfte generieren und spiegeln".
  - Wohnbloecke: linke Haelfte (PixelLab Pro, Vorlagenausschnitt) + gespiegelte Haelfte = ganzer Block. Block 1 und 3
    (grau, gleich gross) teilen sich denselben Block, Block 2 (beige) eigene Haelfte.
  - Hochhaeuser 12 und 5: ein generiertes Hochhaus, das gleichfoermige Flachdach wird mit einem Dachabschnitt ohne
    Aufbauten auf die Laenge des jeweiligen Turms verlaengert (nichts abgeschnitten, Ecken/Fassade bleiben original).
  - Ladenzeile: einzelne Ladenfronten (Objekt-Creator) nebeneinander.
Generator-Hintergrund Magenta: eingeschlossene Magentareste werden aufgefuellt (Daecher) bzw. durchsichtig (Bruecke).
"""
import json, os
from collections import deque
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
QUELLE = os.path.join(ROOT, 'assets', 'objekte', 'karte31')
OUT = os.path.join(QUELLE, 'gebaeude')
T = 16
LADEN = ['ladendach1/00', 'ladendach1/01', 'ladendach1/02', 'books/00', 'ladendach2/00', 'ladendach2/01',
         'ladendach2/02', 'ladendach2/03']                         # Nutzer: mit Dach (vorher flach)


def magenta_rein(im, durchsichtig=False):
    a = np.array(im.convert('RGBA')).astype(int)
    mg = (a[..., 3] > 0) & (a[..., 0] > 150) & (a[..., 2] > 150) & (a[..., 1] < a[..., 0] - 60)
    if durchsichtig:
        a[mg, 3] = 0
        return Image.fromarray(a.astype(np.uint8))
    rest = mg.copy()
    for _ in range(12):                                             # von aussen nach innen aus Nachbarn auffuellen
        if not rest.any():
            break
        ok = (a[..., 3] > 0) & ~rest
        summe = np.zeros(a.shape[:2] + (3,)); n = np.zeros(a.shape[:2])
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            s_ok = np.roll(np.roll(ok, dy, 0), dx, 1)
            summe += np.roll(np.roll(a[..., :3], dy, 0), dx, 1) * s_ok[..., None]
            n += s_ok
        neu = rest & (n > 0)
        a[neu, :3] = (summe[neu] / n[neu][:, None]).astype(int)
        rest &= ~neu
    return Image.fromarray(a.astype(np.uint8))


def haelfte_spiegeln(q):
    """Linke Haelfte (rechts am Bildrand offen) + gespiegelte Haelfte."""
    im = magenta_rein(Image.open(q))
    bb = im.getbbox()
    halb = im.crop((bb[0], bb[1], im.width, bb[3]))
    ha = np.array(halb).astype(int)
    for _ in range(3):                                              # dunkle Randkontur an der Spiegelnaht entfernen
        last, prev = ha[:, -1, :3].sum(1), ha[:, -2, :3].sum(1)
        if (last < prev - 40).mean() > 0.25:
            ha = ha[:, :-1]
    halb = Image.fromarray(ha.astype(np.uint8))
    voll = Image.new('RGBA', (halb.width * 2, halb.height), (0, 0, 0, 0))
    voll.alpha_composite(halb, (0, 0))
    voll.alpha_composite(halb.transpose(Image.FLIP_LEFT_RIGHT), (halb.width, 0))
    return voll


def turm(q, hoehe, nummer=None):
    """Hochhaus auf die Hoehe 'hoehe' bringen: Dachabschnitt ohne Aufbauten wiederholen (oberhalb der Fassade)."""
    im = magenta_rein(Image.open(q))
    im = im.crop(im.getbbox())
    a = np.array(im)
    # mitgemalten Boden (Erde links/rechts, Gehweg unten) wegnehmen: nur der Baukoerper zwischen den Aussenkonturen
    dunkel = (a[..., :3].astype(int).sum(2) < 200) & (a[..., 3] > 0)
    spalten = np.nonzero(dunkel[a.shape[0] // 3:a.shape[0] * 2 // 3].mean(0) > 0.8)[0]
    w_ = a.shape[1]
    xl = max([c for c in spalten if c < w_ // 2] or [0])            # innere Aussenkonturen des Baukoerpers
    xr = min([c for c in spalten if c > w_ // 2] or [w_ - 1])
    zeilen = np.nonzero(dunkel[:, xl] & dunkel[:, xr])[0]          # Zeilen, in denen beide Aussenkonturen laufen
    a = a[zeilen.min():zeilen.max() + 1, xl:xr + 1].copy()
    # Dach neu aufbauen: glatte Dachzeile als Flaeche, Dachaufbauten (Lueftungskaesten) gleichmaessig verteilt
    st = np.array([a[y, 4:-4, :3].astype(int).std(0).sum() for y in range(a.shape[0])])
    ref = np.median(a[a.shape[0] // 3:a.shape[0] // 2, a.shape[1] // 2, :3], 0)   # Dachfarbe
    farbe = np.abs(a[:, a.shape[1] // 2, :3].astype(int) - ref).sum(1) < 12
    glatt = (st <= st[a.shape[0] // 3:a.shape[0] // 2].min() + 2) & farbe
    gy = np.nonzero(glatt)[0]
    fassade = gy.max() + 1                                         # nach der letzten glatten Dachzeile: Fassade
    oben = gy.min()                                                # Dachrand oben
    zeile = a[gy[len(gy) // 2]:gy[len(gy) // 2] + 1]
    baender, y = [], oben
    while y < fassade:                                             # Aufbauten = Zeilenbereiche zwischen glatten Zeilen
        if not glatt[y]:
            y0_ = y
            while y < fassade and not glatt[y]:
                y += 1
            baender.append(a[y0_ - 2:y + 2])
        y += 1
    unten = a[fassade:]
    L = max(0, hoehe - oben - unten.shape[0])
    k = max(1, round(L / 100))
    teile = [baender[i % len(baender)] for i in range(k)]
    luecke = L - sum(t.shape[0] for t in teile)
    stuecke = [a[:oben]]
    for i, t in enumerate(teile):
        g_ = luecke * (i + 1) // (k + 1) - luecke * i // (k + 1)
        stuecke += [np.repeat(zeile, g_, 0), t]
    rest = L - sum(x.shape[0] for x in stuecke[1:])
    stuecke += [np.repeat(zeile, rest, 0), unten]
    a = np.concatenate(stuecke, 0)
    gleich = (a[:, 4:-4] == zeile[0, 4:-4]).all((1, 2))             # Dachbahnen wie in der Vorlage (feine Fugen)
    for y in np.nonzero(gleich)[0]:
        if y % 6 == 0:
            innen = a[y, 4:-4, :3].astype(int)
            maske = np.abs(innen - ref).sum(1) < 12
            innen[maske] -= 10
            a[y, 4:-4, :3] = innen.clip(0, 255)
    out = Image.fromarray(a)
    if nummer is not None:
        out = nummer_ersetzen(out, nummer)
    return out


def nummer_ersetzen(im, nummer):
    """Hausnummer (dunkle Punktziffern mittig in der obersten Fassadenreihe) finden, mit Wandfarbe uebermalen und eine
    andere Ziffer in derselben Punktschrift (2x2-Punkte) an dieselbe Stelle setzen."""
    a = np.array(im)
    h, w = a.shape[:2]
    y_lo, x_lo, x_hi = h - 160, int(w * 0.28), int(w * 0.72)
    reg = a[y_lo:h - 60, x_lo:x_hi]
    dunkel = (reg[..., :3].astype(int).sum(2) < 230) & (reg[..., 3] > 0)
    zeilen = np.nonzero(dunkel.sum(1) > 0)[0]
    if not len(zeilen):
        return im
    gruppen = np.split(zeilen, np.nonzero(np.diff(zeilen) > 3)[0] + 1)   # erste Gruppe dunkler Zeilen = Ziffern
    g = max(gruppen, key=lambda z: dunkel[z].sum()) if len(gruppen) > 1 else gruppen[0]
    ys, xs = np.nonzero(dunkel[g.min():g.max() + 1])
    y0, y1 = y_lo + g.min(), y_lo + g.max() + 1
    x0, x1 = x_lo + xs.min(), x_lo + xs.max() + 1
    for y in range(y0 - 1, y1 + 1):
        a[y, x0 - 1:x1 + 1] = a[y, x0 - 2]
    ZIFFERN = {'5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110']}
    cx, cy = (x0 + x1) // 2 - 5, (y0 + y1) // 2 - 7
    for zy, z in enumerate(ZIFFERN[nummer]):
        for zx, c in enumerate(z):
            if c == '1':
                a[cy + zy * 2:cy + zy * 2 + 2, cx + zx * 2:cx + zx * 2 + 2] = (40, 50, 86, 255)
    return Image.fromarray(a)


def main():
    lay = json.load(open(os.path.join(ROOT, 'maps', 'karte31', 'layout.json')))
    os.makedirs(OUT, exist_ok=True)
    teile = []
    grau = haelfte_spiegeln(os.path.join(QUELLE, 'gross_block_grau_halb', '00.png'))
    beige = haelfte_spiegeln(os.path.join(QUELLE, 'gross_block_beige_halb', '00.png'))
    ba = np.array(beige)                                              # Spiegelnaht-Fehler auf dem Dach (halbes Rohr -> Spitze):
    c, dach = ba.shape[1] // 2, int(ba.shape[0] * 0.34)              # Dachmitte mit Dachflaeche von daneben ueberdecken
    for y in range(dach):
        if ba[y, c - 14:c + 14, 3].min() > 0 and ba[y, c - 44:c - 16, 3].min() > 0:
            ba[y, c - 14:c] = ba[y, c - 42:c - 28]
            ba[y, c:c + 14] = ba[y, c - 42:c - 28][::-1]
        elif ba[y, c - 44:c - 16, 3].max() == 0:                     # Spitze ueber der Dachkante: weg
            ba[y, c - 16:c + 16] = 0
    beige = Image.fromarray(ba)
    for n, im in (('block1', grau), ('block3', grau), ('block2', beige)):
        im.save(os.path.join(OUT, n + '.png')); teile.append((n, im))
    hoehen = {a: (y1 - y0 + 1) * T for (x0, y0, x1, y1, a) in lay['gebaeude']}
    q = os.path.join(QUELLE, 'gross_turm', '00.png')
    for n, nr in (('turm12', None), ('turm5', '5')):
        im = turm(q, hoehen[n], nr)
        im.save(os.path.join(OUT, n + '.png')); teile.append((n, im))
    for n, src, durch in (('bahnhof', 'gross_bahnhof_b', False), ('bruecke', 'gross_bruecke_c', True)):
        p = os.path.join(QUELLE, src, '00.png')
        if not os.path.exists(p):
            p = os.path.join(QUELLE, src.rsplit('_', 1)[0], '00.png')
        im = magenta_rein(Image.open(p), durch)
        im = im.crop(im.getbbox())
        im.save(os.path.join(OUT, n + '.png')); teile.append((n, im))
    for i, src in enumerate(LADEN):
        im = Image.open(os.path.join(QUELLE, src + '.png')).convert('RGBA')
        im = im.crop(im.getbbox())
        im.save(os.path.join(OUT, 'laden_%d.png' % i)); teile.append(('laden_%d' % i, im))
    W = 1600
    x = y = rh = 0
    pos = []
    for _, im in teile:
        if x + im.width > W:
            x = 0; y += rh + 8; rh = 0
        pos.append((x, y)); x += im.width + 8; rh = max(rh, im.height)
    sheet = Image.new('RGBA', (W, y + rh), (150, 160, 150, 255))
    for (_, im), p in zip(teile, pos):
        sheet.alpha_composite(im, p)
    sheet.save(os.path.join(OUT, 'uebersicht.png'))
    print('Gebaeude ->', [(n, im.size) for n, im in teile])


if __name__ == '__main__':
    main()
