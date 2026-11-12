"""Sneak Peek "Blick durchs Loch": Ausschnitte aller A01- und A02-Karten liegen nebeneinander, darueber eine schwarze
Ebene mit einem Loch, das langsam ueber die Karten wandert (Nutzer). Darunter laufen die Karten-Animationen (16 Bilder).

  python3 tools/sneak_peek_loch.py        -> maps/sneak_peek_loch_1.gif (runder Lichtkegel, freie Bahn)
                                             maps/sneak_peek_loch_2.gif (45-Grad-Achteck am 16er-Raster, Karte fuer Karte
                                                                         mit Namensschild)
Die Ausschnitte waehlt das Skript dort, wo die Karte am meisten Details und Bewegung hat (wie tools/sneak_peek.py).
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTEN = [('16', 'The Network'), ('17', 'Our War Game!'), ('19', 'Revenge'),
          ('20', 'Startdorf'), ('21', 'Digi-Egg Valley'), ('23', 'Harvest Hills'), ('24', "The Kaiser's Canyon"),
          ('25', 'Sunset Bay'), ('26', "The Kaiser's Fortress"), ('27', 'Destiny Lake'), ('28', 'Tower Forest'),
          ('07', 'The Holy Peaks'), ('29', 'The Sea of Darkness'), ('30', 'Odaiba'), ('31', 'Highton View Terrace'),
          ('32', 'Dream Ruins'), ('33', 'The World of Dreams')]
ZW, ZH = 240, 176                  # Zelle (Ausschnitt je Karte, Originalgroesse = 15 x 11 Kacheln)
SP = 6                             # Spalten -> 6 x 3 Raster (17 Karten + Titelfeld)
LUECKE = 4
DAUER = 110                        # ms je Bild (Takt der 16-Bilder-Animationen)
FETT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
# von Hand gewaehlte Ausschnitte (x, y am 16er-Raster), wo die Automatik nur Leere/Wald/Boden findet
AUSSCHNITT = {'16': (368, 96), '17': (432, 32), '19': (704, 96), '26': (64, 16), '27': (1040, 96), '28': (1104, 112),
              '31': (1152, 1360), '32': (400, 0), '33': (16, 48)}


def animation(k):
    p16 = os.path.join(ROOT, 'maps', 'karte' + k, 'animation', 'karte%s_animiert_16.webp' % k)
    p4 = os.path.join(ROOT, 'maps', 'karte' + k, 'animation', 'karte%s_animiert.webp' % k)
    im = Image.open(p16 if os.path.exists(p16) else p4)
    fr = [f.convert('RGB') for f in ImageSequence.Iterator(im)]
    if len(fr) < 16:                                             # 4-Bilder-Fassung: jedes Bild 4x
        fr = [fr[i * len(fr) // 16] for i in range(16)]
    return fr


def ausschnitt(fr):
    a = np.array(fr[0].convert('L')).astype(np.float32)
    kante = np.abs(np.diff(a, axis=0))[:, :-1] + np.abs(np.diff(a, axis=1))[:-1, :]
    bew = np.zeros_like(kante)
    for f in fr[1::3]:
        b = np.array(f.convert('L')).astype(np.float32)
        bew += (np.abs(b - a) > 6)[:-1, :-1]
    wert = np.minimum(kante, 60) + 25 * np.minimum(bew, 2)
    s = 16
    h_, w_ = wert.shape[0] // s, wert.shape[1] // s
    bl = wert[:h_ * s, :w_ * s].reshape(h_, s, w_, s).sum(axis=(1, 3))
    ii = np.pad(bl.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    bw, bh = ZW // s, ZH // s
    summe = ii[bh:, bw:] - ii[:-bh, bw:] - ii[bh:, :-bw] + ii[:-bh, :-bw]
    yy, xx = np.mgrid[0:summe.shape[0], 0:summe.shape[1]]
    cy, cx = (summe.shape[0] - 1) / 2, (summe.shape[1] - 1) / 2
    summe = summe * (1 - 0.3 * np.hypot((yy - cy) / max(1, cy), (xx - cx) / max(1, cx)) / 1.42)
    y, x = np.unravel_index(np.argmax(summe), summe.shape)
    return int(x * s), int(y * s)                                 # am 16er-Raster


def mosaik():
    """16 Bilder des Mosaiks (alle Karten-Ausschnitte nebeneinander) + Zellpositionen."""
    zeilen = math.ceil((len(KARTEN) + 1) / SP)
    W, H = SP * ZW + (SP + 1) * LUECKE, zeilen * ZH + (zeilen + 1) * LUECKE
    bilder = [Image.new('RGB', (W, H), (14, 16, 24)) for _ in range(16)]
    zellen = []
    for i, (k, name) in enumerate(KARTEN):
        fr = animation(k)
        x0, y0 = AUSSCHNITT.get(k) or ausschnitt(fr)
        x0, y0 = min(x0, fr[0].width - ZW), min(y0, fr[0].height - ZH)
        zx, zy = LUECKE + (i % SP) * (ZW + LUECKE), LUECKE + (i // SP) * (ZH + LUECKE)
        for f in range(16):
            bilder[f].paste(fr[f].crop((x0, y0, x0 + ZW, y0 + ZH)), (zx, zy))
        zellen.append((zx + ZW // 2, zy + ZH // 2, k, name))
        print('Karte %s: Ausschnitt %d,%d' % (k, x0, y0), flush=True)
    i = len(KARTEN)                                               # Titelfeld
    zx, zy = LUECKE + (i % SP) * (ZW + LUECKE), LUECKE + (i // SP) * (ZH + LUECKE)
    for b in bilder:
        d = ImageDraw.Draw(b)
        d.rectangle((zx, zy, zx + ZW - 1, zy + ZH - 1), fill=(10, 12, 28))
        d.text((zx + ZW // 2, zy + ZH // 2 - 18), 'A01 + A02', font=ImageFont.truetype(FETT, 26), fill=(120, 220, 255),
               anchor='mm')
        d.text((zx + ZW // 2, zy + ZH // 2 + 18), '17 Karten', font=ImageFont.truetype(FETT, 16), fill=(230, 230, 240),
               anchor='mm')
    zellen.append((zx + ZW // 2, zy + ZH // 2, None, None))
    return bilder, zellen


def loch_rund(W, H, cx, cy, r):
    """Alpha der schwarzen Ebene: 0 im Loch, weicher Rand in 4-px-Stufen (Pixelstil), sonst 255."""
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.hypot(xx - cx, yy - cy)
    al = np.clip((d - r) / 16.0, 0, 1)
    al = np.floor(al * 4) / 4                                     # 4 harte Stufen statt Verlauf
    return (al * 255).astype(np.uint8)


def loch_achteck(W, H, cx, cy, r):
    """Achteck-Loch am 16er-Raster mit 45-Grad-Schraegen (wie Regel 6b), zwei dunkle Randstufen."""
    yy, xx = np.mgrid[0:H, 0:W]
    dx, dy = np.abs(xx - cx), np.abs(yy - cy)
    d = np.maximum(np.maximum(dx, dy), (dx + dy) * 0.7071)
    al = np.where(d < r, 0, np.where(d < r + 8, 110, np.where(d < r + 16, 190, 255)))
    return al.astype(np.uint8)


def speichern(frames, pfad):
    q = [f.quantize(colors=255, method=Image.Quantize.MAXCOVERAGE) for f in frames]
    q[0].save(pfad, save_all=True, append_images=q[1:], duration=DAUER, loop=0, disposal=1, optimize=True)
    print('%s: %d Bilder, %.1f MB' % (pfad, len(frames), os.path.getsize(pfad) / 1e6))


def main():
    bilder, zellen = mosaik()
    W, H = bilder[0].size
    schwarz = Image.new('RGB', (W, H), (0, 0, 0))
    out = os.path.join(ROOT, 'maps')
    # 1) runder Lichtkegel auf einer ruhigen Lissajous-Bahn ueber das ganze Mosaik
    n1 = 176                                                      # ~19 s
    fr1 = []
    for t in range(n1):
        u = 2 * math.pi * t / n1
        cx = W / 2 + (W / 2 - 150) * math.sin(u)
        cy = H / 2 + (H / 2 - 110) * math.sin(2 * u + 0.6)
        r = 138 + 12 * math.sin(4 * u)
        al = Image.fromarray(loch_rund(W, H, cx, cy, r))
        fr1.append(Image.composite(schwarz, bilder[t % 16], al))
    speichern(fr1, os.path.join(out, 'sneak_peek_loch_1.gif'))
    # 2) Achteck-Loch faehrt Karte fuer Karte ab (Schlangenlinie), haelt kurz, Namensschild der Karte
    reihen = {}
    for z in zellen[:-1]:
        reihen.setdefault(z[1], []).append(z)
    bahn = []
    for n, y in enumerate(sorted(reihen)):
        reihe = sorted(reihen[y], key=lambda z: z[0], reverse=bool(n % 2))
        bahn += reihe
    fr2, t = [], 0
    halten, fahren = 10, 6                                        # Bilder je Karte: ~1,1 s halten, 0,66 s fahren
    font = ImageFont.truetype(FETT, 15)
    for i, z in enumerate(bahn):
        nz = bahn[(i + 1) % len(bahn)]
        for s in range(halten + fahren):
            if s < halten:
                cx, cy = z[0], z[1]
            else:
                p = (s - halten + 1) / fahren
                p = p * p * (3 - 2 * p)                           # weich anfahren und abbremsen
                cx, cy = z[0] + (nz[0] - z[0]) * p, z[1] + (nz[1] - z[1]) * p
            al = Image.fromarray(loch_achteck(W, H, cx, cy, 104))
            b = Image.composite(schwarz, bilder[t % 16], al)
            if s < halten:
                d = ImageDraw.Draw(b)
                txt = 'Karte %s - %s' % (int(z[2]), z[3])
                tw = d.textlength(txt, font=font)
                y_ = min(H - 22, z[1] + 104 + 14)
                d.rectangle((z[0] - tw / 2 - 8, y_ - 11, z[0] + tw / 2 + 8, y_ + 11), fill=(8, 10, 22))
                d.line((z[0] - tw / 2 - 8, y_ - 11, z[0] + tw / 2 + 8, y_ - 11), fill=(90, 200, 255), width=2)
                d.text((z[0], y_), txt, font=font, fill=(240, 240, 250), anchor='mm')
            fr2.append(b)
            t += 1
    speichern(fr2, os.path.join(out, 'sneak_peek_loch_2.gif'))


if __name__ == '__main__':
    main()
