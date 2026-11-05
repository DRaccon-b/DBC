"""Schwarze Tuerme fuer Karte 07: schlanke, facettierte Obelisk-Tuerme (frontal, Licht oben links).

  python3 tools/karte07_tuerme.py

Erzeugt assets/objekte/karte07/turm/schwarz_{gross,klein,gefallen,stumpf}.png
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ZIEL = os.path.join(ROOT, 'assets', 'objekte', 'karte07', 'turm')


def H(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


# dunkle, leicht blaeuliche Obsidianpalette
UMRISS = H('#0c0d12')
LINKS = [H('#2a2e3a'), H('#353a48'), H('#424858')]       # Licht-Facette (von unten nach oben heller)
RECHTS = [H('#14161d'), H('#1a1d26'), H('#20242e')]      # Schatten-Facette
GRAT = H('#6a7288')
GLANZ = H('#8890a6')
SPALT = H('#08090c')


def turm(hoehe, breite, spitze, sockel_h=14, risse=()):
    """Stehender Turm: zwei sichtbare Facetten mit Mittelgrat, leicht verjuengt, Pyramidenspitze, breiter Sockel."""
    W = breite + 12
    img = np.zeros((hoehe, W, 4), np.uint8)
    cx = W // 2
    for y in range(hoehe):
        if y < spitze:                                    # Spitze
            hw = int(round((breite * 0.32) * y / spitze))
        elif y < hoehe - sockel_h:                        # Schaft, nach unten breiter
            t = (y - spitze) / max(1, hoehe - sockel_h - spitze)
            hw = int(round(breite * 0.32 + t * breite * 0.18))
        else:                                             # Sockel mit schraegen Facetten
            t = (y - (hoehe - sockel_h)) / sockel_h
            hw = int(round(breite * 0.5 + t * 5))
        for x in range(cx - hw, cx + hw + 1):
            if not 0 <= x < W:
                continue
            stufe = 2 if y < hoehe * 0.35 else 1 if y < hoehe * 0.7 else 0
            if x < cx:
                c = LINKS[stufe]
            elif x > cx:
                c = RECHTS[stufe]
            else:
                c = GRAT
            if y >= hoehe - sockel_h:
                c = LINKS[1] if x < cx else RECHTS[1] if x > cx else GRAT
                if y == hoehe - sockel_h:
                    c = GLANZ if x < cx else LINKS[0]
            if x in (cx - hw, cx + hw) or y == hoehe - 1:
                c = UMRISS
            img[y, x] = c + (255,)
        # Glanzstreifen auf der Lichtfacette (schraeg nach unten)
        if spitze < y < hoehe - sockel_h:
            gx = cx - hw + 2 + ((y // 3) % 3 == 0)
            if (y // 9) % 4 != 3 and 0 <= gx < cx - 1:
                img[y, gx] = GLANZ + (255,) if y < hoehe * 0.5 else LINKS[2] + (255,)
    # Fugen (horizontale Segmente)
    for yf in range(spitze + 22, hoehe - sockel_h, 26):
        for x in range(W):
            if img[yf, x, 3] and tuple(img[yf, x, :3]) != UMRISS:
                img[yf, x, :3] = SPALT if x >= cx else RECHTS[2]
    for (y0, x0, n) in risse:                             # Risse
        x, y = cx + x0, y0
        for i in range(n):
            if 0 <= y < hoehe and 0 <= x < W and img[y, x, 3]:
                img[y, x, :3] = SPALT
            y += 1
            x += (1 if i % 3 == 0 else 0) * (1 if x0 >= 0 else -1)
    return Image.fromarray(img, 'RGBA')


def gefallen(laenge, dicke):
    """Umgestuerzter Turm: liegt quer (Spitze rechts), Bruchkante links mit Truemmern, Unterseite im Schatten."""
    t = turm(laenge, dicke, 22, sockel_h=0)
    t = t.crop((0, 0, t.width, int(laenge * 0.82)))      # abgebrochenes Stueck ohne Sockel
    t = t.rotate(-90, expand=True)                        # Spitze zeigt nach rechts
    a = np.array(t)
    h, w = a.shape[:2]
    # Bruchkante links: gezackt
    for y in range(h):
        z = 3 + int(3 * abs(np.sin(y * 1.7)))
        a[y, :z, 3] = 0
        xs = np.nonzero(a[y, :, 3])[0]
        if len(xs):
            a[y, xs.min(), :3] = SPALT
            a[y, xs.min() + 1, :3] = H('#4a5064')
    # Liegend: Oberseite = Lichtfacette (oben), Unterseite dunkler
    out = Image.new('RGBA', (w + 18, h + 8), (0, 0, 0, 0))
    out.alpha_composite(Image.fromarray(a), (12, 2))
    o = np.array(out)
    rs = np.random.RandomState(3)
    for _ in range(14):                                   # Truemmerbrocken an der Bruchstelle und unten
        bx = rs.randint(0, 26)
        by = rs.randint(h - 10, h + 4)
        s = rs.randint(2, 5)
        for yy in range(by, min(o.shape[0], by + s)):
            for xx in range(bx, min(o.shape[1], bx + s + 1)):
                if o[yy, xx, 3] == 0:
                    o[yy, xx] = (LINKS[1] if yy == by else RECHTS[1] if yy < by + s - 1 else UMRISS) + (255,)
    return Image.fromarray(o)


def stumpf(breite, hoehe):
    """Abgebrochener Turmstumpf mit gezackter Bruchkante oben."""
    t = turm(170, breite, 22)
    a = np.array(t)[170 - hoehe:]
    h, w = a.shape[:2]
    for x in range(w):
        z = int(4 + 4 * abs(np.sin(x * 0.9)) + 3 * (x % 5 == 0))
        a[:z, x, 3] = 0
        ys = np.nonzero(a[:, x, 3])[0]
        if len(ys):
            a[ys.min(), x, :3] = H('#5a6278')
    return Image.fromarray(a)


if __name__ == '__main__':
    os.makedirs(ZIEL, exist_ok=True)
    turm(176, 34, 26, risse=((70, -6, 14), (120, 5, 10))).save(os.path.join(ZIEL, 'schwarz_gross.png'))
    turm(128, 28, 20, risse=((60, 4, 10),)).save(os.path.join(ZIEL, 'schwarz_klein.png'))
    gefallen(170, 34).save(os.path.join(ZIEL, 'schwarz_gefallen.png'))
    stumpf(34, 52).save(os.path.join(ZIEL, 'schwarz_stumpf.png'))
    for n in ('gross', 'klein', 'gefallen', 'stumpf'):
        print(n, Image.open(os.path.join(ZIEL, 'schwarz_%s.png' % n)).size)
