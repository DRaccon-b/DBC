"""Gebaeude fuer Karte 30 (Odaiba) -> assets/objekte/karte30/gebaeude/<art>.png, uebersicht.png

  python3 tools/karte30_gebaeude.py

Die grossen Gebaeude kommen aus dem PixelLab Pro-Generator (pixellab_gross.py, Vorlagenausschnitt als Motiv, Ausnahme
> 256 px) und werden hier genau in ihr Rechteck aus layout.json eingepasst (Fuss buendig unten, waagerecht mittig).
Fehlt einem Gebaeude das Dach (flaches Glasbuero), wird eine Dachflaeche von leicht oben ergaenzt (Regel: Gebaeude mit
Dach). Das Riesenrad wird prozedural gezeichnet, damit sich Ring und Gondeln drehen koennen (riesenrad(winkel)).
"""
import json, math, os, random
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte30')
QUELLE = os.path.join(ROOT, 'assets', 'objekte', 'karte30')
OUT = os.path.join(QUELLE, 'gebaeude')
T = 16
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
UMRISS = H('#2a3040')


def einpassen(im, w, h):
    """Sprite auf w x h: zuschneiden auf den Inhalt, unten buendig, waagerecht mittig (nie skalieren)."""
    bb = im.getbbox()
    im = im.crop(bb)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    cw = min(w, im.width)                                           # Regel 1b: kleinster Kachelblock, darin mittig
    if im.width > w:                                                # zu breit: mittig auf die Flaeche zuschneiden und
        l_ = (im.width - w) // 2                                    # die Enden als echte Hauskanten nachzeichnen
        im = enden(im.crop((l_, 0, l_ + w, im.height)))
    nb = -(-cw // T)
    x_ = ((w // T - nb) // 2) * T + (nb * T - cw) // 2
    if im.height > h:                                               # hoeher als die Flaeche: ragt nach oben hinaus
        out = Image.new('RGBA', (w, im.height), (0, 0, 0, 0))       # (Nutzer: Haeuser ganz zeigen, nichts abschneiden)
        h = im.height
    out.alpha_composite(im.crop((0, 0, cw, im.height)), (x_, h - im.height))
    return out


def enden(im):
    """Seitlich abgeschnittene Fassade zu echten Gebaeudeenden machen: 1 px Kontur, links 2 px Lichtkante,
    rechts 2 px Schattenkante (Licht von oben links) - nur dort, wo das Gebaeude Pixel hat."""
    a = np.array(im).astype(np.float32)
    w = a.shape[1]
    al = a[..., 3] > 0
    for x, f in ((1, 1.25), (2, 1.12), (w - 3, 0.82), (w - 2, 0.68)):
        a[al[:, x], x, :3] = np.clip(a[al[:, x], x, :3] * f, 0, 255)
    for x in (0, w - 1):
        a[al[:, x], x, :3] = UMRISS[:3]
    return Image.fromarray(a.astype(np.uint8))


def loecher_fuellen(im):
    """Vom Generator freigestellte helle Glasflaechen (durchsichtige Loecher mitten im Gebaeude) wieder fuellen:
    Loch = durchsichtig und nicht ueber Durchsichtiges mit dem Bildrand verbunden. Farbe aus den Nachbarn, leicht blau."""
    from collections import deque
    a = np.array(im)
    leer = a[..., 3] == 0
    h, w = leer.shape
    aussen = np.zeros_like(leer)
    q = deque()
    for y in range(h):
        for x in (0, w - 1):
            if leer[y, x] and not aussen[y, x]:
                aussen[y, x] = True; q.append((y, x))
    for x in range(w):
        for y in (0, h - 1):
            if leer[y, x] and not aussen[y, x]:
                aussen[y, x] = True; q.append((y, x))
    while q:
        y, x = q.popleft()
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= yy < h and 0 <= xx < w and leer[yy, xx] and not aussen[yy, xx]:
                aussen[yy, xx] = True; q.append((yy, xx))
    loch = leer & ~aussen
    a[loch] = (176, 214, 236, 255)                                   # helle Himmelsspiegelung im Glas
    a[loch & np.roll(~loch, 1, 0)] = (214, 236, 248, 255)            # obere Kante noch heller
    return Image.fromarray(a)


def dach_ergaenzen(im, dach_h=28):
    """Flachdach mit Attika von leicht oben ueber die Fassade setzen (Fassade oben um dach_h - 6 px gekuerzt)."""
    w, h = im.size
    a = np.array(im)
    zeilen = np.nonzero(a[..., 3].max(1) > 0)[0]
    oben = zeilen.min()
    fassade = im.crop((0, oben + dach_h - 6, w, h))
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    y0 = h - fassade.height - dach_h + 2
    d.rectangle((0, y0, w - 1, y0 + dach_h), fill=H('#8a909c'))
    d.rectangle((4, y0 + 4, w - 5, y0 + dach_h - 3), fill=H('#727884'))
    d.rectangle((0, y0, w - 1, y0 + 1), fill=H('#c4c8d2'))
    d.rectangle((0, y0, 1, y0 + dach_h), fill=H('#b0b4be'))
    d.rectangle((w - 2, y0, w - 1, y0 + dach_h), fill=H('#565c68'))
    rs = random.Random(30)
    x = 24
    while x < w - 40:                                               # Dachaufbauten (Klima, Luefter)
        if rs.random() < 0.45:
            yy = y0 + 7 + rs.randint(0, 6)
            d.rectangle((x, yy, x + 11, yy + 7), fill=H('#a4aab4'))
            d.rectangle((x, yy, x + 11, yy), fill=H('#d4d8e0'))
            d.rectangle((x + 3, yy + 2, x + 8, yy + 5), fill=H('#5a5e6a'))
            d.rectangle((x, yy + 8, x + 12, yy + 8), fill=H('#4a4e5a'))
        x += 30 + rs.randint(0, 30)
    d.rectangle((0, y0 + dach_h - 2, w - 1, y0 + dach_h), fill=H('#4a4e5a'))   # Gesims-Schatten
    out.alpha_composite(fassade, (0, h - fassade.height))
    al = np.array(out)[..., 3] > 0
    a2 = np.array(out)
    rand = al & ~(np.roll(al, 1, 0) & np.roll(al, -1, 0) & np.roll(al, 1, 1) & np.roll(al, -1, 1))
    rand[:, 0] |= al[:, 0]; rand[:, -1] |= al[:, -1]
    a2[rand & (np.arange(h)[:, None] < h - fassade.height + 2)] = UMRISS
    return Image.fromarray(a2)


GONDEL = ['#d84a4a', '#f0b030', '#4aa860', '#4a8ad8', '#e07a30', '#e070a8', '#8a5ad0', '#40b8c0']


def riesenrad(winkel=0.0, w=272, h=368):
    """Riesenrad: weisser Stahlring (doppelt, Querstreben), 16 Speichen zur Nabe, 24 bunte Gondeln (haengen immer
    senkrecht), A-Stuetzen links und rechts zur Nabe. winkel in Grad (Drehung von Ring, Speichen und Gondeln)."""
    S = 2                                                            # doppelt zeichnen, dann verkleinern (saubere Linien)
    im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy, R = w / 2 * S, 132 * S, 120 * S
    weiss, grau, dunkel = H('#eef1f5'), H('#a8b0bc'), H('#4a5262')
    fuss_y = (h - 4) * S
    for sx in (-1, 1):                                               # hintere Stuetze (dunkler)
        d.line((cx, cy, cx + sx * 70 * S, fuss_y), fill=grau, width=5 * S)
    for k in range(16):                                              # Speichen
        a = math.radians(winkel + k * 22.5)
        d.line((cx, cy, cx + R * math.cos(a), cy + R * math.sin(a)), fill=grau if k % 2 else weiss, width=S)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=weiss, width=3 * S)
    d.ellipse((cx - R + 7 * S, cy - R + 7 * S, cx + R - 7 * S, cy + R - 7 * S), outline=grau, width=2 * S)
    for k in range(48):                                              # Querstreben zwischen den Ringen
        a = math.radians(winkel + k * 7.5)
        d.line((cx + R * math.cos(a), cy + R * math.sin(a), cx + (R - 7 * S) * math.cos(a), cy + (R - 7 * S) * math.sin(a)),
               fill=grau, width=S)
    for sx in (-1, 1):                                               # vordere A-Stuetzen
        d.line((cx, cy, cx + sx * 82 * S, fuss_y), fill=weiss, width=6 * S)
        d.line((cx + sx * 2 * S, cy + 4 * S, cx + sx * 84 * S, fuss_y), fill=grau, width=2 * S)
        d.rectangle((cx + sx * 82 * S - 8 * S, fuss_y - 4 * S, cx + sx * 82 * S + 8 * S, fuss_y + 3 * S), fill=dunkel)
    d.line((cx - 46 * S, cy + 150 * S, cx + 46 * S, cy + 150 * S), fill=grau, width=3 * S)   # Querverstrebung der Stuetzen
    d.ellipse((cx - 11 * S, cy - 11 * S, cx + 11 * S, cy + 11 * S), fill=grau, outline=dunkel, width=S)   # Nabe
    d.ellipse((cx - 5 * S, cy - 5 * S, cx + 5 * S, cy + 5 * S), fill=weiss)
    for k in range(24):                                              # Gondeln
        a = math.radians(winkel + k * 15)
        gx, gy = cx + (R + 2 * S) * math.cos(a), cy + (R + 2 * S) * math.sin(a)
        f = H(GONDEL[k % len(GONDEL)])
        d.line((gx, gy, gx, gy + 4 * S), fill=dunkel, width=S)
        d.rounded_rectangle((gx - 6 * S, gy + 3 * S, gx + 6 * S, gy + 15 * S), radius=4 * S, fill=f, outline=dunkel, width=S)
        d.rectangle((gx - 4 * S, gy + 6 * S, gx + 4 * S, gy + 9 * S), fill=H('#cfe8f6'))   # Fenster
        d.line((gx - 4 * S, gy + 6 * S, gx - 1 * S, gy + 6 * S), fill=(255, 255, 255, 255), width=S)
    im = im.resize((w, h), Image.NEAREST)
    a = np.array(im)                                                 # dunkle Kontur aussen (Handheld-Stil)
    al = a[..., 3] > 0
    rand = ~al & (np.roll(al, 1, 0) | np.roll(al, -1, 0) | np.roll(al, 1, 1) | np.roll(al, -1, 1))
    a[rand] = H('#3a4252')
    return Image.fromarray(a)


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    os.makedirs(OUT, exist_ok=True)
    teile = []
    for (x0, y0, x1, y1, art) in lay['gebaeude']:
        w, h = (x1 - x0 + 1) * T, (y1 - y0 + 1) * T
        if art in ('buero_klein', 'buero_klein2'):
            q = os.path.join(QUELLE, 'buero1' if art == 'buero_klein' else 'buero2', '00.png')
        else:
            neu_ = {'laeden': 'gross_laeden_c', 'buero_flach': 'gross_buero_flach_c'}   # Nutzer: Qualitaet, neu erzeugt
            q = os.path.join(QUELLE, neu_.get(art, 'gross_' + art), '00.png')
        im = loecher_fuellen(einpassen(Image.open(q).convert('RGBA'), w, h))
        if art == 'buero_flach' and False:                         # (alte Fassung ohne Dach - nicht mehr noetig)
            a_ = np.array(im).astype(int)                             # weisse Scheiben -> helle Himmelsspiegelung
            weiss_ = (a_[..., :3].min(2) > 228) & (a_[..., 3] > 0)
            a_[weiss_, :3] = (184, 216, 238)
            im = dach_ergaenzen(Image.fromarray(a_.astype(np.uint8)))
        im.save(os.path.join(OUT, art + '.png'))
        teile.append((art, im))
    for i in range(4):                                               # Riesenrad: 4 Bilder (Gondelabstand 15 Grad)
        rr = riesenrad(i * 15 / 4.0)
        rr.save(os.path.join(OUT, 'riesenrad_%d.png' % i))
    teile.append(('riesenrad', riesenrad(0)))
    W = 1900
    x = y = rowh = 0
    pos = []
    for _, im in teile:
        if x + im.width > W:
            x = 0; y += rowh + 8; rowh = 0
        pos.append((x, y)); x += im.width + 8; rowh = max(rowh, im.height)
    sheet = Image.new('RGBA', (W, y + rowh), (110, 150, 90, 255))
    for (_, im), p in zip(teile, pos):
        sheet.alpha_composite(im, p)
    sheet.save(os.path.join(OUT, 'uebersicht.png'))
    print('Gebaeude ->', OUT, [a for a, _ in teile])


if __name__ == '__main__':
    main()
