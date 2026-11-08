"""Sneak-Peek-GIF fuer Discord aus allen fertigen Karten -> maps/sneak_peek.gif (unter 10 MB)

  python3 tools/sneak_peek.py

Ablauf: Titelkarte (Mosaik aller Karten) -> je Karte ein Ausschnitt in Originalgroesse (kleine Karten 2x, wie ihr
Discord-GIF) mit ihrer eigenen Animation und Namensleiste -> Abspann. Der Ausschnitt wird automatisch dort gewaehlt,
wo die Karte am meisten Details und Bewegung hat (oder von Hand in AUSSCHNITT festgelegt).
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageSequence, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
W, H = 800, 450
PRO_KARTE = 2400                   # ms je Karte
KARTEN = [('01', 'Wald & Strand'), ('02', 'Factorial Town'), ('03', 'Server Desert'), ('04', 'Gear Savanna'),
          ('05', 'Freezeland'), ('06', 'Startkarte'), ('07', 'The Holy Peaks'), ('08', 'Overdell'),
          ('09', "Vamdemon's Keep"), ('10', 'Toy Town'), ('11', 'Spiral Mountain: Dark Ocean'),
          ('12', 'Spiral Mountain: Puppet Woods'), ('13', 'Spiral Mountain: Machine City'),
          ('14', 'Spiral Mountain: Summit'), ('15', "Apocalymon's Realm"), ('16', 'The Network'),
          ('18', 'The Fog-Bound City')]
AUSSCHNITT = {'15': (0, 110), '16': (112, 24)}   # Karte -> (x, y) von Hand, falls automatisch unpassend
SKALA = {'15': 0.5, '16': 0.5}     # Discord-GIF ist 2x -> Sneak Peek in Originalgroesse (ganze Insel/Plattform)
FETT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def frames_von(k):
    g = Image.open(os.path.join(ROOT, 'maps', 'karte' + k, 'animation', 'karte%s_discord.gif' % k))
    fr, dauer = [], []
    for f in ImageSequence.Iterator(g):
        f = f.convert('RGB')
        if k in SKALA:
            f = f.resize((int(f.width * SKALA[k]), int(f.height * SKALA[k])), Image.NEAREST)
        fr.append(f)
        dauer.append(f.info.get('duration', 200))
    return fr, dauer


def ausschnitt(k, fr):
    if k in AUSSCHNITT:
        return AUSSCHNITT[k]
    a = np.array(fr[0].convert('L')).astype(np.float32)
    kante = np.abs(np.diff(a, axis=0))[:, :-1] + np.abs(np.diff(a, axis=1))[:-1, :]
    bew = np.zeros_like(kante)
    for f in fr[1:]:
        b = np.array(f.convert('L')).astype(np.float32)
        bew += (np.abs(b - a) > 6)[:-1, :-1]
    wert = np.minimum(kante, 60) + 25 * np.minimum(bew, 2)
    s = 8                                                         # grob rechnen (8-px-Bloecke)
    h_, w_ = wert.shape[0] // s, wert.shape[1] // s
    bl = wert[:h_ * s, :w_ * s].reshape(h_, s, w_, s).sum(axis=(1, 3))
    ii = np.pad(bl.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    bw, bh = W // s, H // s
    if bw > w_ or bh > h_:
        return 0, 0
    summe = ii[bh:, bw:] - ii[:-bh, bw:] - ii[bh:, :-bw] + ii[:-bh, :-bw]
    yy, xx = np.mgrid[0:summe.shape[0], 0:summe.shape[1]]
    cy, cx = (summe.shape[0] - 1) / 2, (summe.shape[1] - 1) / 2
    summe = summe * (1 - 0.25 * (np.hypot((yy - cy) / max(1, cy), (xx - cx) / max(1, cx)) / 1.42))  # leicht zur Mitte
    y, x = np.unravel_index(np.argmax(summe), summe.shape)
    return int(x * s), int(y * s)


def leiste(img, nr, name, i, n):
    d = ImageDraw.Draw(img, 'RGBA')
    d.rectangle((0, H - 40, W, H), fill=(8, 10, 22, 200))
    d.line((0, H - 40, W, H - 40), fill=(90, 200, 255, 255), width=2)
    f1 = ImageFont.truetype(FETT, 14)
    f2 = ImageFont.truetype(FETT, 20)
    d.fontmode = '1'
    d.text((16, H - 31), 'KARTE %s' % nr, font=f1, fill=(120, 210, 255))
    d.text((106, H - 34), name, font=f2, fill=(255, 255, 255))
    for j in range(n):                                            # Fortschrittspunkte rechts
        x = W - 16 - (n - j) * 9
        d.rectangle((x, H - 23, x + 4, H - 19), fill=(255, 210, 90) if j == i else (70, 80, 110))


def karte_mitte(fr, x, y):
    out = []
    for f in fr:
        c = f.crop((x, y, x + W, y + H))
        if c.size != (W, H) or f.width < W or f.height < H:
            b = Image.new('RGB', (W, H), (8, 10, 22))
            sub = f.crop((x, y, min(f.width, x + W), min(f.height, y + H)))
            b.paste(sub, ((W - sub.width) // 2, (H - sub.height) // 2))
            c = b
        out.append(c)
    return out


def titelkarte(alle, text1, text2):
    """Mosaik aus allen Karten, abgedunkelt, darueber der Titel."""
    b = Image.new('RGB', (W, H), (8, 10, 22))
    sp, zl = 6, 3
    tw, th = W // sp, H // zl
    for i, (k, fr) in enumerate((alle * 2)[:sp * zl]):          # 18 Felder: erste Karte fuellt das letzte
        t = fr[0].copy()
        t.thumbnail((tw * 2, th * 2))
        t = t.crop(((t.width - tw) // 2, (t.height - th) // 2, (t.width - tw) // 2 + tw, (t.height - th) // 2 + th))
        b.paste(t, ((i % sp) * tw, (i // sp) * th))
    b = Image.blend(b, Image.new('RGB', (W, H), (8, 10, 22)), 0.62)
    d = ImageDraw.Draw(b, 'RGBA')
    d.fontmode = '1'
    f1 = ImageFont.truetype(FETT, 46)
    f2 = ImageFont.truetype(FETT, 20)
    for t, f, y, c in ((text1, f1, H // 2 - 46, (255, 255, 255)), (text2, f2, H // 2 + 18, (120, 210, 255))):
        w_ = d.textlength(t, font=f)
        d.text(((W - w_) / 2 + 3, y + 3), t, font=f, fill=(0, 0, 0, 180))
        d.text(((W - w_) / 2, y), t, font=f, fill=c)
    return b


def main():
    bilder, dauern, alle, gruppe = [], [], [], []
    roh = {}
    for k, name in KARTEN:
        fr, du = frames_von(k)
        roh[k] = (fr, du)
        alle.append((k, fr))
    bilder.append(titelkarte(alle, 'MAP SNEAK PEEK', '%d Karten  ·  16×16 Top-Down  ·  Handheld-RPG-Stil' % len(KARTEN)))
    dauern.append(2200)
    gruppe.append(-1)
    for i, (k, name) in enumerate(KARTEN):
        fr, du = roh[k]
        x, y = ausschnitt(k, fr)
        teil = karte_mitte(fr, x, y)
        t = 0
        j = 0
        while t < PRO_KARTE:
            b = teil[j % len(teil)].copy()
            leiste(b, k, name, i, len(KARTEN))
            bilder.append(b)
            gruppe.append(i)
            d = max(100, du[j % len(du)])
            dauern.append(d)
            t += d
            j += 1
        print('Karte %s: Ausschnitt %d,%d, %d Bilder' % (k, x, y, j))
    bilder.append(titelkarte(alle[::-1], 'Bald mehr …', 'Karte 17: Our War Game!'))
    dauern.append(2400)
    gruppe.append(-2)
    # gemeinsame Palette je Karte: gleiche Pixel -> gleiche Indizes -> GIF speichert nur, was sich bewegt
    pal, palette = [], {}
    for b, g in zip(bilder, gruppe):
        if g not in palette:
            alle_g = [x for x, gg in zip(bilder, gruppe) if gg == g]
            band = Image.new('RGB', (W, H * min(3, len(alle_g))))
            for n_, x in enumerate(alle_g[:3]):
                band.paste(x, (0, n_ * H))
            palette[g] = band.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        pal.append(b.quantize(palette=palette[g], dither=Image.Dither.NONE))
    ziel = os.path.join(ROOT, 'maps', 'sneak_peek.gif')
    pal[0].save(ziel, save_all=True, append_images=pal[1:], duration=dauern, loop=0, optimize=True, disposal=1)
    print('Sneak Peek: %d Bilder, %.1f s, %.1f MB' % (len(pal), sum(dauern) / 1000, os.path.getsize(ziel) / 1e6))


if __name__ == '__main__':
    main()
