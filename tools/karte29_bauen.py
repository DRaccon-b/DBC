"""Karte 29 - The Sea of Darkness (A02), Gelaende im Stil der A02-Karten (Bausteine Karte 01/04/05).

Dunkles, tiefes Meer (Wasserkacheln Karte 01, dunkel umgefaerbt, mit Tiefenstufen zum Ufer hin), flaches
tuerkisgraues Wasser am Ufer mit Schaumlinie, graublauer Strand (Sandkacheln Karte 01, umgefaerbt) mit helleren
Sandflecken, Felsbloecke als Hochflaechen mit Schieferfront, Pflasterplatz oben links, erhoehter Tempelplatz mit
Front und Treppe, dunkle Steinbruecken.

  python3 tools/karte29_layout.py && python3 tools/karte29_bauen.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte29')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte29')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
FRONT = 32                                       # Felsfronten 2 Kacheln
LIPPE_FELS = ['#2c3240', '#3c4454', '#4e5868', '#62707e', '#788694', '#8e9cab']


def faerben(lo, hi):
    lo, hi = np.array(lo, np.float32), np.array(hi, np.float32)

    def f(a):
        l = a.mean(axis=2, keepdims=True) / 255.0
        return lo + (hi - lo) * np.clip((l - 0.35) / 0.55, 0, 1)
    return f


def maske(cls, arten):
    return np.kron(np.array([[c in arten for c in z] for z in cls]), np.ones((T, T), bool))


def dehnen(m, n):
    im = Image.fromarray(m.astype(np.uint8) * 255)
    while n > 1:                                                     # grosse Radien in Schritten (PIL-Grenze)
        s_ = min(n, 9) | 1
        im = im.filter(ImageFilter.MaxFilter(s_))
        n -= s_ - 1
    return np.array(im) > 0


def pflaster(cols, rows, hell=1.0):
    """Graue Pflastersteine (8x8 versetzt, Fugen dunkel, Licht oben links) im kuehlen Ton der Karte."""
    t = np.zeros((rows * T, cols * T, 3), np.uint8)
    rng = np.random.RandomState(29)
    for y in range(0, rows * T, 8):
        off = 4 if (y // 8) % 2 else 0
        for x in range(-8, cols * T, 8):
            c = (np.array((112, 118, 134)) + rng.randint(-8, 8)) * hell
            x0, x1 = max(0, x + off), min(cols * T, x + off + 8)
            if x1 <= x0:
                continue
            t[y:y + 8, x0:x1] = np.clip(c, 0, 255)
            t[y, x0:x1] = np.clip(c + 20, 0, 255)
            t[y:y + 8, x0] = np.clip(c + 10, 0, 255)
            t[y + 7, x0:x1] = (62, 66, 80)
            t[y:y + 8, x1 - 1] = (70, 74, 88)
    return t


def bruecke(a, x0, y0, x1, y1, senkrecht):
    """Dunkle Steinbruecke: quer liegende Platten mit Fugen, seitliche Bruestungskante, Schatten aufs Wasser."""
    dunkel, mitte, hell, kante = H('#1c1f2a'), H('#2e3342'), H('#454c60'), H('#0c0e14')
    for y in range(y0, y1):
        for x in range(x0, x1):
            i = (y - y0) if senkrecht else (x - x0)
            c = hell if i % 8 == 0 else dunkel if i % 8 == 7 else mitte
            rand = (x - x0 < 3 or x1 - 1 - x < 3) if senkrecht else (y - y0 < 3 or y1 - 1 - y < 3)
            if rand:
                c = kante if (x in (x0, x1 - 1) if senkrecht else y in (y0, y1 - 1)) else hell
            a[y, x] = c
    if senkrecht:
        for k, f in ((0, 0.6), (1, 0.75), (2, 0.88)):
            a[y0:y1, min(a.shape[1] - 1, x1 + k)] = (a[y0:y1, min(a.shape[1] - 1, x1 + k)] * f).astype(np.uint8)
    else:
        for k, f in ((0, 0.6), (1, 0.75), (2, 0.88)):
            a[min(a.shape[0] - 1, y1 + k), x0:x1] = (a[min(a.shape[0] - 1, y1 + k), x0:x1] * f).astype(np.uint8)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = np.kron(np.array([[int(c) for c in z] for z in lay['hoehe']]), np.ones((T, T), int))
    f = frame or 0
    basis = os.path.join(ROOT, 'assets', 'basis')
    strand = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, faerben((88, 104, 116), (138, 156, 166))), cols, rows)
    hell = flaeche(k6.kacheln(os.path.join(basis, 'sand_%d.png'), 5, faerben((120, 128, 142), (170, 176, 188))), cols, rows)
    fels = flaeche(k6.kacheln(os.path.join(ROOT, 'assets', 'karte05', 'basis', 'r_%d.png'), 5,
                              faerben((70, 76, 92), (132, 140, 156))), cols, rows)
    tief_t = flaeche(k6.kacheln(os.path.join(basis, 'wasser_%d.png'), 5, faerben((30, 48, 72), (62, 88, 116))), cols, rows)
    flach_t = flaeche(k6.kacheln(os.path.join(basis, 'wasser_%d.png'), 5, faerben((76, 116, 130), (124, 164, 174))), cols, rows)
    # Wasser: tiefes Meer und flaches Ufer (Wellen wandern je Bild um 2 px)
    a = np.roll(tief_t, 2 * f, axis=1).copy()
    land_t = maske(cls, 'glrmpqbT')
    flach_roh = maske(cls, 's')
    land = weich(land_t.astype(np.float32), 3, 0.25, 7, 0.5)
    flach = weich((flach_roh | land_t).astype(np.float32), 5, 0.35, 8, 0.5) & ~land
    a[flach] = np.roll(flach_t, -f, axis=1)[flach]
    tief = ~flach & ~land                                            # Tiefenstufen: dunkler, je weiter vom Ufer
    nah_ = np.array(Image.fromarray(((flach | land) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(14))) / 255.0
    nah2 = np.array(Image.fromarray(((flach | land) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(34))) / 255.0
    fern = nah_ < 0.04                                               # weiche, runde Tiefenstufen statt Rechtecke
    sehr = nah2 < 0.04
    a[tief & fern] = (a[tief & fern] * 0.86).astype(np.uint8)
    a[tief & sehr] = (a[tief & sehr] * 0.86).astype(np.uint8)
    kante = flach & dehnen(tief, 3)                                  # Abbruchkante flach -> tief
    a[kante] = (a[kante] * 0.78).astype(np.uint8)
    # Strand, heller Sand, Pfuetzen bleiben flaches Wasser
    a[land] = strand[land]
    lm = weich(zell_maske(cls, 'l', cols, rows), 5, 0.45, 9) & land
    a[lm] = hell[lm]
    saum = land & dehnen(~land, 3)                                   # nasser Saum + Schaumlinie am Ufer
    a[saum] = (a[saum] * 0.8).astype(np.uint8)
    schaum = ~land & dehnen(land, 3) & ~dehnen(land, 1)
    yy, xx = np.nonzero(schaum)
    sel = ((xx // 3 + yy + f) % 5) < 3
    a[yy[sel], xx[sel]] = H('#c8d6dc')
    # Plaetze: Pflaster oben links (ebenerdig) und Tempelplatz (erhoeht)
    pf = pflaster(cols, rows)
    qm = maske(cls, 'q')
    a[qm] = pf[qm]
    pm = maske(cls, 'p')
    a[pm] = pflaster(cols, rows, 1.08)[pm]
    for m_ in (qm, pm):
        rand_ = m_ & ~(np.roll(m_, 1, 0) & np.roll(m_, -1, 0) & np.roll(m_, 1, 1) & np.roll(m_, -1, 1))
        a[rand_] = H('#3a3f4e')
    # Felsbloecke: Oberseite Felskacheln, Fronten (Schiefer) nach Sueden, schmale Seitenkanten
    rm = (hp == 2) & ~pm
    a[rm] = fels[rm]
    lippe = LIPPE_FELS
    wand = k4.hoehenkanten(a, rm, 'schiefer', FRONT, 8, lippe, np.zeros((Hp, Wp), bool), 29, berg=False)
    px0, py0, px1, py1 = lay['platz']
    frei = np.zeros((Hp, Wp), bool)
    tx0, tx1 = lay['platz_treppe']
    ye = (py1 + 1) * T - 1
    frei[ye - 14:ye + FRONT + 8, tx0 * T:(tx1 + 1) * T] = True
    wand |= k4.hoehenkanten(a, pm, 'schiefer', FRONT, 8, lippe, frei, 30, berg=False)
    k4.treppe(a, tx0 * T, (tx1 + 1) * T, ye, 's', FRONT, 'schiefer', pf)
    # Bruecken
    for (x0, y0, x1, y1) in lay['bruecken']:
        senk = (y1 - y0) > (x1 - x0)
        bruecke(a, x0 * T + (2 if senk else 0), y0 * T + (0 if senk else 2), (x1 + 1) * T - (2 if senk else 0),
                (y1 + 1) * T - (0 if senk else 2), senk)
    img = Image.fromarray(a).convert('RGBA')
    wasser = ~land & ~maske(cls, 'b')
    lvl = np.where(hp == 2, 2, 1).astype(np.uint8)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        lv_ = lvl.copy(); lv_[wand] = 9
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lv_)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(wasser))
    pfj = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pfj):
        objs = sorted((o for o in json.load(open(pfj)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.copy().astype(np.int16)
            ebenen[wand] = 9
            ebenen[wasser] = 7
            k4.objekte_zeichnen(img, objs, cache, ~wand & ~wasser, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, f)
            k6.animieren_k6(img, objs, cache, f)
            kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 29 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
