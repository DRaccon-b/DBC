"""Karte 19 (Revenge): zwei schwebende Plattformen in der Leere des Netzes (Stil von Karte 16/17).

Links Network-Stil: Plattenboden der Vorlage, Aufstellfeld, Ankunfts- und Goldpfeile, drei kleine Bodenplatten
(Metallplatten mit zwei Nieten, wie in der Vorlage). Rechts ein Hafen: oben das Hafenbecken (Wasser wie Karte 01/18
mit Flachwasser, Stufen, Schaumkante und Lichtstrichen; der Randring der Plattform ist die Beckenmauer), darunter
Pflaster (Plattenkacheln der Vorlage in Grau, wie in der Vorlage) mit Kaikante aus hellem Stein, Aufstellfeld,
Ankunftspfeilen und Ringmarke. Ringsum Netzraster, blauer Nebel, Datenstraenge und Fragmente (Funktionen Karte 16).

  python3 tools/karte19_layout.py && python3 tools/karte19_bauen.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte04_bauen as k4
import karte08_bauen as k8
import karte16_bauen as k16
import karte17_bauen as k17

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte19')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte19')
T = 16
N_FRAMES = k16.N_FRAMES
BILDDAUER = k16.BILDDAUER
CYAN, LEER = k16.CYAN, k16.LEER
kontur, mischen, puls = k16.kontur, k16.mischen, k16.puls
PFLASTER = np.array((137, 154, 155), np.float32)              # Pflasterfarbe der Vorlage
WASSER_STILE = {}
RAND = os.environ.get('K19_RAND', 'kai')                           # Rand der Hafen-Plattform: kai (gewaehlt) | netz | bunt | warn


def pflaster_textur(cols, rows):
    """Plattenkacheln von Karte 16 in das Grau der Vorlage umgefaerbt (Helligkeit bleibt erhalten)."""
    bt = k16.boden_textur(cols, rows).astype(np.float32)
    lum = bt.mean(axis=2, keepdims=True)
    basis = np.array((54, 94, 126), np.float32).mean()
    return np.clip(lum / basis * PFLASTER * 0.92, 0, 255).astype(np.uint8)


def bodenplatte(a, tx, ty):
    """Kleine Metallplatte mit zwei Nieten (Vorlage: hellgraue Platte 10x4 px), mittig in der Kachel."""
    X, Y = tx * T + 3, ty * T + 7
    a[Y - 1, X + 1:X + 9] = (40, 52, 70)                      # Kontur
    a[Y + 4, X:X + 10] = (24, 32, 48)
    a[Y:Y + 4, X - 1] = (40, 52, 70); a[Y:Y + 4, X + 10] = (24, 32, 48)
    a[Y:Y + 4, X:X + 10] = (150, 170, 180)
    a[Y, X:X + 10] = (196, 212, 220)                          # Licht oben
    a[Y + 3, X:X + 10] = (112, 130, 142)
    a[Y + 2, X + 2] = a[Y + 2, X + 7] = (90, 104, 116)        # Nieten
    a[Y + 5, X + 1:X + 11] = (a[Y + 5, X + 1:X + 11] * 0.7).astype(np.uint8)   # Kontaktschatten


def hafenbecken(a, wasser, frame):
    """Hafenbecken wie das Meer von Karte 01 (wasser_details.meer_terrassen): klares Wasser, der Grund ist sichtbar.
    Der Grund sind hier die versunkenen Pflasterplatten (statt Sand): an den Mauern ein flacher Sims, dann eine
    Stufe mit Lichtkante und dunklem Fuss ins tiefere Becken; Algen, Lichtstriche, feine Wasserlinie an den Mauern.
    Kein Strand-Schaum (Hafenmauern statt Ufer), keine Felsen. An der Nordmauer bleibt die nasse Mauerfront sichtbar."""
    import wasser_details as wd
    f = frame or 0
    Hp, Wp = wasser.shape
    pt = pflaster_textur(Wp // T, Hp // T).astype(np.float32)
    alt = (wd.FARBEN, wd.N_FRAMES, wd.FLACH, wd.SCHAUM_D, wd.STUFE1, wd.STUFE2, wd.MISCH, wd._kacheln)
    wd.FARBEN = [c * 0.88 for c in wd.FARBEN]
    wd.N_FRAMES = N_FRAMES
    wd.FLACH, wd.SCHAUM_D, wd.STUFE1, wd.STUFE2 = 12, (900, 900), 18, 900
    wd.MISCH = [0.38, 0.52, 0.7, 0.85]
    wd._kacheln = lambda name, Hh, W: (pt[:Hh, :W] * (1.0 if name == 'sand' else 0.8)).copy()
    wd.FELSEN_PROTOKOLL.clear()
    meiden = np.ones_like(wasser)                                  # keine Felsen im Becken
    try:
        img = wd.meer_terrassen(Image.fromarray(a), wasser, frame, meiden, maske=wasser)
    finally:
        wd.FARBEN, wd.N_FRAMES, wd.FLACH, wd.SCHAUM_D, wd.STUFE1, wd.STUFE2, wd.MISCH, wd._kacheln = alt
    a = np.array(img.convert('RGB'))
    # Nordmauer: sichtbare Front (6 px nasser Stein) mit Wasserlinie darunter
    ys, xs = np.nonzero(wasser)
    y0, x0, x1 = ys.min(), xs.min(), xs.max() + 1
    stein = [(120, 126, 124), (104, 110, 110), (92, 98, 100), (80, 88, 92), (66, 76, 84), (54, 66, 78)]
    for d, c in enumerate(stein):
        a[y0 + d, x0:x1] = c
    for x in range(x0, x1, 16):
        a[y0 + 1:y0 + 5, x] = (70, 78, 82)
    p = 0.5 + 0.5 * np.sin(2 * np.pi * f / N_FRAMES)
    linie = np.zeros_like(wasser)
    linie[y0 + 6, x0:x1] = True
    mischen(a, linie, (190, 225, 235), 0.45 + 0.2 * p)
    return a


WASSER = os.environ.get('K19_WASSER', 'netz')                  # gewaehlt: Netz-Wasser (Nutzer)


def _becken(wasser):
    ys, xs = np.nonzero(wasser)
    return ys.min(), ys.max() + 1, xs.min(), xs.max() + 1


def _nordmauer(a, wasser, frame):
    y0, y1, x0, x1 = _becken(wasser)
    stein = [(120, 126, 124), (104, 110, 110), (92, 98, 100), (80, 88, 92), (66, 76, 84), (54, 66, 78)]
    for d, c in enumerate(stein):
        a[y0 + d, x0:x1] = c
    for x in range(x0, x1, 16):
        a[y0 + 1:y0 + 5, x] = (70, 78, 82)
    p = 0.5 + 0.5 * np.sin(2 * np.pi * (frame or 0) / N_FRAMES)
    linie = np.zeros_like(wasser); linie[y0 + 6, x0:x1] = True
    mischen(a, linie, (190, 225, 235), 0.45 + 0.2 * p)
    return a


def _grund(wasser):
    Hp, Wp = wasser.shape
    return pflaster_textur(Wp // T, Hp // T).astype(np.float32)


def wasser_sand(a, wasser, frame):
    """Wie Karte 01 genau: Sandgrund (Kacheln von Karte 01), Flachwasser, Stufe, Lichtstriche (ohne Strand-Schaum)."""
    import wasser_details as wd
    alt = (wd.FARBEN, wd.N_FRAMES, wd.FLACH, wd.SCHAUM_D, wd.STUFE1, wd.STUFE2)
    wd.N_FRAMES = N_FRAMES
    wd.FLACH, wd.SCHAUM_D, wd.STUFE1, wd.STUFE2 = 12, (900, 900), 18, 900
    wd.FELSEN_PROTOKOLL.clear()
    try:
        img = wd.meer_terrassen(Image.fromarray(a), wasser, frame, np.ones_like(wasser), maske=wasser)
    finally:
        wd.FARBEN, wd.N_FRAMES, wd.FLACH, wd.SCHAUM_D, wd.STUFE1, wd.STUFE2 = alt
    return _nordmauer(np.array(img.convert('RGB')), wasser, frame)


def wasser_kaustik(a, wasser, frame):
    """Klar und flach: ueberall sieht man die Pflasterplatten, darueber ein wanderndes Lichtnetz (Kaustik)."""
    f = frame or 0
    y0, y1, x0, x1 = _becken(wasser)
    g = _grund(wasser)[y0:y1, x0:x1]
    yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0].astype(np.float32)
    ph = 2 * np.pi * f / N_FRAMES
    u = np.sin(xx / 6.0 + 1.3 * np.sin(yy / 9.0 + ph) + ph)
    v = np.sin(yy / 5.5 - 1.3 * np.sin(xx / 8.0 - ph) - ph)
    netz = ((np.abs(u) < 0.13) | (np.abs(v) < 0.13)).astype(np.float32)[..., None]   # feine Lichtlinien (Kaustik)
    farbe = np.array((70, 170, 190), np.float32)
    sub = g * 0.55 + farbe * 0.45
    sub = sub * (1 - 0.55 * netz) + np.array((210, 245, 250), np.float32) * 0.55 * netz
    m = wasser[y0:y1, x0:x1]
    a[y0:y1, x0:x1][m] = np.clip(sub, 0, 255).astype(np.uint8)[m]
    return _nordmauer(a, wasser, frame)


def wasser_tief(a, wasser, frame):
    """Tiefes Hafenbecken: Grund nur nahe der Mauern sichtbar, zur Mitte dunkles Blau; Wellenzeichen der Vorlage."""
    f = frame or 0
    y0, y1, x0, x1 = _becken(wasser)
    g = _grund(wasser)[y0:y1, x0:x1]
    h, w = y1 - y0, x1 - x0
    yy, xx = np.mgrid[0:h, 0:w]
    rand = np.minimum(np.minimum(yy - 6, h - 1 - yy), np.minimum(xx, w - 1 - xx)).clip(0).astype(np.float32)
    t = (np.clip(rand / 8, 0, 3).astype(int) / 3.0).astype(np.float32)[..., None]   # 4 Tiefenstufen (Pixelart)
    flach, tief = np.array((70, 140, 160), np.float32), np.array((22, 52, 92), np.float32)
    sub = g * (0.45 * (1 - t)) + (flach * (1 - t) + tief * t) * (0.55 + 0.45 * t)
    for gy in range(10, h, 8):
        for gx in range(-16, w, 16):
            X = gx + (8 if (gy // 8) % 2 else 0) + (2 * f) % 16
            for dx, dy in ((1, 0), (2, 0), (0, 1), (3, 1)):
                if 0 <= X + dx < w and gy + dy < h:
                    sub[gy + dy, X + dx] = sub[gy + dy, X + dx] * 0.4 + np.array((120, 170, 195), np.float32) * 0.6
    m = wasser[y0:y1, x0:x1]
    a[y0:y1, x0:x1][m] = np.clip(sub, 0, 255).astype(np.uint8)[m]
    return _nordmauer(a, wasser, frame)


def wasser_netz(a, wasser, frame):
    """Netz-Wasser: klares Cyan ueber den Platten, unter Wasser ein leuchtendes Datenraster, Lichtwellen laufen als
    Bitreihen ueber die Oberflaeche (passt zur Netzwelt). In der Mitte eine zweite, tiefere Ebene mit sichtbarer
    Stufe (Nordwand), dunklerem Grund und schwaecherem, versetztem Raster."""
    f = frame or 0
    y0, y1, x0, x1 = _becken(wasser)
    g = _grund(wasser)[y0:y1, x0:x1]
    h, w = y1 - y0, x1 - x0
    yy, xx = np.mgrid[0:h, 0:w]
    sub = g * 0.45 + np.array((20, 110, 150), np.float32) * 0.55
    raster = ((xx % 16 == 0) | (yy % 16 == 0))
    p = 0.5 + 0.5 * np.sin(2 * np.pi * f / N_FRAMES)
    # zweite, tiefere Ebene (Nutzerwunsch): Becken im Becken, 1 Kachel vom Rand (oben unter der Mauerfront 1,5),
    # am 16er-Raster; dort ist der Grund dunkler, das Datenraster schwaecher und um 8 px versetzt (liegt tiefer)
    hb = min(h, 6 * T)                                             # Hoehe des oberen Beckens (Kanaele darunter bleiben flach)
    ex = 32 if w > 26 * T else 16                                  # offene Seiten: Sims 1 Kachel breiter
    tief = (yy >= 24) & (yy < hb - 16) & (xx >= ex) & (xx < w - ex)
    sub[tief] = g[tief] * 0.22 + np.array((10, 62, 102), np.float32) * 0.78
    raster_t = tief & (((xx + 8) % 16 == 0) | ((yy + 8) % 16 == 0))
    raster &= ~tief
    sub[raster] = sub[raster] * (0.6 - 0.15 * p) + np.array((80, 230, 255), np.float32) * (0.4 + 0.15 * p)
    sub[raster_t] = sub[raster_t] * (0.72 - 0.1 * p) + np.array((60, 170, 220), np.float32) * (0.28 + 0.1 * p)
    # Stufe: Nordwand der Vertiefung ist sichtbar (zeigt zum Betrachter, 5 px), Kanten mit Licht, Fuss dunkel
    ty0, ty1 = 24, hb - 16
    for d, c in enumerate([(40, 150, 190), (30, 126, 168), (24, 106, 148), (18, 88, 128), (10, 56, 92)]):
        sub[ty0 + d, ex:w - ex] = c
    sub[ty0 - 1, ex - 1:w - ex + 1] = sub[ty0 - 1, ex - 1:w - ex + 1] * 0.3 + np.array((150, 245, 255), np.float32) * 0.7
    sub[ty0:ty1, ex - 1] = sub[ty0:ty1, ex - 1] * 0.4 + np.array((120, 225, 245), np.float32) * 0.6          # Seitenkanten
    sub[ty0:ty1, w - ex] = sub[ty0:ty1, w - ex] * 0.55 + np.array((14, 70, 110), np.float32) * 0.45
    sub[ty1, ex:w - ex] = sub[ty1, ex:w - ex] * 0.45 + np.array((110, 215, 240), np.float32) * 0.55          # Suedkante
    sub[ty0 + 5:ty0 + 8, ex:w - ex] *= 0.8                                                                    # Schatten unter der Stufe
    if h > hb:                                                     # Kanaele: das Wasser laeuft nach unten (Bitstriche
        for kx in range(0, w, 6):                                  # wandern je Bild 4 px abwaerts)
            if not wasser[y0 + hb + 4, x0 + kx]:
                continue
            ph = (kx * 7) % 16
            for Y in range(hb - 8, h):
                if (Y - ph - 4 * f) % 16 < 4 and wasser[y0 + Y, x0 + kx]:
                    sub[Y, kx] = sub[Y, kx] * 0.3 + np.array((200, 250, 255), np.float32) * 0.7
    rs = np.random.RandomState(77)
    for _ in range(18):                                            # Bitreihen (helle Striche), treiben nach rechts
        gy, gx, lang = rs.randint(9, hb - 2), rs.randint(0, w), rs.randint(4, 10)
        for k_ in range(lang):
            X = (gx + k_ + 3 * f) % w
            if k_ % 3 != 2:
                sub[gy, X] = sub[gy, X] * 0.3 + np.array((200, 250, 255), np.float32) * 0.7
    m = wasser[y0:y1, x0:x1]
    a[y0:y1, x0:x1][m] = np.clip(sub, 0, 255).astype(np.uint8)[m]
    return _nordmauer(a, wasser, frame)


def wasser_klassik(a, wasser, frame):
    """Handheld-Klassik: Wasserkacheln wie in klassischen Handheld-RPGs (Blau mit hellen Wellenboegen im
    16er-Raster), leicht durchscheinend, damit die Platten durchschimmern."""
    f = frame or 0
    y0, y1, x0, x1 = _becken(wasser)
    g = _grund(wasser)[y0:y1, x0:x1]
    h, w = y1 - y0, x1 - x0
    yy, xx = np.mgrid[0:h, 0:w]
    sub = g * 0.25 + np.array((56, 128, 208), np.float32) * 0.75
    ky, kx = yy % 16, (xx + (2 * f if True else 0)) % 16
    hell = ((ky == 4) & (kx >= 2) & (kx <= 6)) | ((ky == 3) & (kx >= 3) & (kx <= 5)) | \
           ((ky == 12) & (kx >= 10) & (kx <= 14)) | ((ky == 11) & (kx >= 11) & (kx <= 13))
    dunkel = ((ky == 5) & (kx >= 2) & (kx <= 6)) | ((ky == 13) & (kx >= 10) & (kx <= 14))
    sub[hell] = (176, 224, 248)
    sub[dunkel] = sub[dunkel] * 0.8
    m = wasser[y0:y1, x0:x1]
    a[y0:y1, x0:x1][m] = np.clip(sub, 0, 255).astype(np.uint8)[m]
    return _nordmauer(a, wasser, frame)


def ueberlauf(a, wasser, land, frame):
    """Wo die Mauer auf Wasserhoehe fehlt (linke und rechte Seite des Beckens), laeuft das Wasser ueber die Kante
    und faellt seitlich an der Plattform hinab in die Leere (Quelle = Becken, Abfluss = Leere):
      - Stroemung: im Becken ziehen kurze helle Striche zur offenen Kante hin
      - Lippe: das Wasser woelbt sich ueber die Kante (heller, unregelmaessiger Saum, 2-4 px nach aussen)
      - Vorhang: oben breit (die ganze offene Kante), unten schmaler; hinten dunkles Blau, davor helle Straehnen in
        verschiedenen Laengen und Geschwindigkeiten, Raender leicht gewellt, schwacher cyan Schein in der Leere
      - Ende: unter der Plattform zerfaellt das Wasser in Tropfen und Datenpixel, die weiter fallen und verloeschen
    4 Bilder: alles ist auf 4 Bilder abgestimmt (Straehnen 4 px/Bild, Periode 16 px)."""
    f = frame or 0
    Hp, Wp = wasser.shape
    ys, xs = np.nonzero(wasser)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    oy = y0 + 6                                                    # Wasser beginnt unter der Nordmauerfront
    unten = int(np.nonzero(land[:, x0 + 20])[0].max()) + 1         # Unterkante der Plattform
    rs = np.random.RandomState(1921)
    dunkel, mittel = np.array((20, 78, 128), np.float32), np.array((36, 128, 178), np.float32)
    hell, weiss = np.array((150, 230, 250), np.float32), np.array((225, 250, 255), np.float32)

    def mix(Y, X, c, s_):
        if 0 <= Y < Hp and 0 <= X < Wp and not land[Y, X]:
            a[Y, X] = np.clip(a[Y, X] * (1 - s_) + c * s_, 0, 255).astype(np.uint8)

    for seite in (-1, 1):
        kante = x0 if seite < 0 else x1 - 1
        aussen = lambda d: kante + seite * d                       # d px ausserhalb der Plattform
        # --- Stroemung im Becken zur Kante hin
        for _ in range(9):
            Y = rs.randint(oy + 3, y1 - 2)
            ph = rs.randint(16)
            for t in range(5):
                d_in = (ph + 4 * f + t) % 40                       # 0 = an der Kante
                X = kante - seite * (40 - d_in)
                if wasser[Y, X] and t < 3:
                    a[Y, X] = np.clip(a[Y, X] * 0.4 + hell * 0.6, 0, 255).astype(np.uint8)
        # --- Schein in der Leere
        for Y in range(oy, min(Hp, unten + 60)):
            for d in range(1, 22):
                X = aussen(d)
                if 0 <= X < Wp and not land[Y, X]:
                    q = (Y - oy) / max(1, unten + 60 - oy)
                    mix(Y, X, np.array((40, 160, 220), np.float32), 0.10 * (1 - d / 22) * (1 - q))
        # --- Vorhang: oben 20 px breit (Bogen nach aussen), unten 12 px; Licht von links oben
        laenge = unten + 44 - oy
        for t in range(laenge):
            Y = oy + t
            q = t / laenge
            aus = max(0.0, (t - (laenge - 40)) / 40.0)                # unten blendet der Strahl aus
            bogen = 6 * max(0.0, 1 - t / 18.0)                     # oben woelbt sich der Strahl nach aussen
            breite = int(round(12 + 8 * (1 - q) ** 2 + bogen * 0.3 + 1.0 * np.sin(Y / 7.0 + seite * 1.7)
                               + 0.8 * np.sin(Y / 3.0 + 2 * np.pi * f / N_FRAMES)))
            for d in range(1, breite + 1):
                X = aussen(d)
                r_ = d / breite                                    # 0 = an der Plattform, 1 = aussen
                c = mittel * (1 - abs(r_ - 0.45)) + dunkel * abs(r_ - 0.45)
                if d <= 2:
                    c = dunkel * 0.8                               # Schattenseite zur Plattform
                if d == breite:
                    c = hell if seite < 0 else dunkel * 0.9        # Aussenkante: links im Licht, rechts im Schatten
                if aus > 0 and rs.rand() < aus * 0.7:
                    continue                                       # zerfaellt in einzelne Pixel
                mix(Y, X, c, 0.95 * (1 - aus))
        # Straehnen: durchgehende feine Linien, darauf helle Abschnitte, die nach unten laufen (4 px je Bild)
        for k in range(20):
            d = 3 + rs.randint(0, 14)
            lang, gap = rs.randint(5, 14), rs.choice((10, 18, 26))
            ph = rs.randint(gap + lang)
            for t in range(laenge):
                Y = oy + t
                q = t / laenge
                breite_ = 12 + 8 * (1 - q) ** 2
                if d >= breite_ - 1:
                    continue
                aus = max(0.0, (t - (laenge - 40)) / 40.0)
                mix(Y, aussen(d), mittel * 1.15, 0.35 * (1 - aus))
                if (t - ph - 4 * f) % (gap + lang) < lang:
                    mix(Y, aussen(d), weiss if k % 4 == 0 else hell, 0.8 * (1 - aus))
        # Gischtwolke unter der Plattform: weiche Tropfen und Datenpixel breiten sich aus, fallen und verloeschen
        for k in range(70):
            d0 = rs.randint(0, 16)
            start = unten + rs.randint(-10, 6)
            weg = rs.randint(24, 80)
            pos = ((rs.randint(32) + 4 * f) % 32) / 32.0
            Y = int(start + pos * weg)
            X = aussen(d0 + int(pos * rs.randint(-6, 14)))
            s_ = 0.85 * (1 - pos) ** 1.3
            gr = 2 if (k % 7 == 0 and pos < 0.5) else 1
            farbe = weiss if k % 3 == 0 else (hell if k % 3 == 1 else np.array((80, 220, 255), np.float32))
            for yy_ in range(gr):
                for xx_ in range(gr):
                    mix(Y + yy_, X + seite * xx_, farbe, s_)
        for d in range(0, 26):                                     # Nebel um den Aufprall (weich, statisch)
            for t in range(-8, 40):
                Y, X = unten + t, aussen(d - 4)
                w_ = max(0.0, 1 - (((d - 9) / 13.0) ** 2 + ((t - 10) / 28.0) ** 2))
                mix(Y, X, np.array((120, 200, 235), np.float32), 0.22 * w_)
        # --- Lippe: Wasser woelbt sich ueber die Kante
        for Y in range(oy, y1):
            w_ = 3 + int(1.5 + 1.5 * np.sin(Y / 5.0 + 2 * np.pi * f / N_FRAMES + seite))
            for d in range(0, w_ + 1):
                X = aussen(d)
                c = weiss if d >= w_ - 1 else hell
                if d == 0:
                    a[Y, X] = np.clip(a[Y, X] * 0.3 + hell * 0.7, 0, 255).astype(np.uint8)
                else:
                    mix(Y, X, c, 0.9)
        for Y in (oy, y1 - 1):                                      # Enden der Lippe weich
            mix(Y, aussen(1), weiss, 0.6)
        # Gischt an der Lippe (wechselt je Bild)
        for _ in range(14):
            Y, d = rs.randint(oy, y1), rs.randint(3, 8)
            if (rs.randint(4) + f) % 4 == 0:
                mix(Y, aussen(d), weiss, 0.9)


FALL = os.environ.get('K19_FALL', 'daten')                     # gewaehlt: Datenstrom (Nutzer)


def _fall_basis(a, wasser, land):
    ys, xs = np.nonzero(wasser)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    unten = int(np.nonzero(land[:, x0 + 20])[0].max()) + 1
    Hp, Wp = wasser.shape

    def mix(Y, X, c, s_):
        if 0 <= Y < Hp and 0 <= X < Wp and not land[Y, X]:
            a[Y, X] = np.clip(a[Y, X] * (1 - s_) + np.array(c, np.float32) * s_, 0, 255).astype(np.uint8)
    return y0 + 6, y1, x0, x1, unten, mix


def fall_klassik(a, wasser, land, frame):
    """Klassischer Handheld-Wasserfall: 16 px breites Band am Kachelraster, senkrechte helle/dunkle Streifen, helle
    Querwellen laufen 4 px je Bild nach unten; unten ein Schaumkranz, der pulsiert."""
    f = frame or 0
    oy, y1, x0, x1, unten, mix = _fall_basis(a, wasser, land)
    for seite in (-1, 1):
        kante = x0 if seite < 0 else x1 - 1
        for t in range(unten + 8 - oy):
            Y = oy + t
            for d in range(1, 17):
                X = kante + seite * d
                c = (46, 128, 196)
                if d in (4, 9, 13):
                    c = (96, 180, 230)                             # senkrechte helle Bahnen
                if d in (1, 16):
                    c = (225, 248, 255)                            # Schaumraender
                elif d in (2, 15):
                    c = (120, 200, 240)
                bahn = (t * 1 + d * 5 - 4 * f) % 24
                if 3 <= d <= 14 and bahn < 5 and d % 3 != 0:
                    c = (200, 240, 255)                            # helle Abschnitte laufen nach unten
                mix(Y, X, c, 0.97)
        p = 0.5 + 0.5 * np.sin(2 * np.pi * f / N_FRAMES)
        for d in range(-3, 21):                                   # Schaumkranz
            for t in range(0, 10):
                X, Y = kante + seite * d, unten + 4 + t
                w_ = 1 - ((d - 8.5) / (14 + 2 * p)) ** 2 - ((t - 3) / 8.0) ** 2
                if w_ > 0:
                    mix(Y, X, (235, 250, 255) if (d + t + f) % 3 else (160, 220, 245), min(1, w_ * 1.6))
        for d in range(3):                                         # Kante oben
            mix(oy - 1, kante + seite * (d + 1), (220, 250, 255), 0.8)


def fall_daten(a, wasser, land, frame):
    """Datenstrom: an der Kante zerfaellt das Wasser in Datenpixel - senkrechte Spalten aus cyan Bits (wie
    Daten-Regen), die nach unten rauschen und in der Leere verloeschen. Passt zur Netzwelt."""
    f = frame or 0
    oy, y1, x0, x1, unten, mix = _fall_basis(a, wasser, land)
    rs = np.random.RandomState(1931)
    for seite in (-1, 1):
        kante = x0 if seite < 0 else x1 - 1
        for Y in range(oy, y1):                                    # leuchtende Abbruchkante
            mix(Y, kante, (160, 245, 255), 0.7)
            mix(Y, kante + seite, (90, 220, 255), 0.6)
        for spalte in range(30):
            d = 1 + spalte % 16 + rs.randint(0, 2)
            Y0 = oy + rs.randint(0, y1 - oy)
            lang = unten + 90 - Y0
            ph = rs.randint(12)
            for t in range(0, lang, 1):
                Y = Y0 + t
                q = t / lang
                if (t % 3 == 2) or rs.rand() < q * 0.8:
                    continue
                kopf = (t - ph - 4 * f) % 12 < 2
                c = (225, 255, 255) if kopf else ((70, 210, 250) if (t // 2) % 3 else (40, 140, 220))
                mix(Y, kante + seite * d, c, (0.98 if kopf else 0.85) * (1 - q * 0.8))


def fall_schleier(a, wasser, land, frame):
    """Feiner Schleier: das Wasser rinnt als breiter, durchscheinender Film an der Plattform herab (man sieht die
    Leere durch), mit feinen Linien und wenigen hellen Tropfen; unten weich ausgeblendet."""
    f = frame or 0
    oy, y1, x0, x1, unten, mix = _fall_basis(a, wasser, land)
    rs = np.random.RandomState(1932)
    for seite in (-1, 1):
        kante = x0 if seite < 0 else x1 - 1
        laenge = unten + 60 - oy
        for t in range(laenge):
            Y, q = oy + t, t / laenge
            breite = int(22 - 8 * q)
            for d in range(1, breite):
                s_ = 0.6 * (1 - q) * (1 - d / breite * 0.4)
                mix(Y, kante + seite * d, (90, 190, 230), s_)
                if d % 4 == 1:
                    mix(Y, kante + seite * d, (180, 240, 255), 0.45 * (1 - q))
        for _ in range(60):
            d, ph = rs.randint(2, 18), rs.randint(32)
            Y = oy + (ph * 7 + 8 * f) % laenge
            mix(Y, kante + seite * d, (235, 252, 255), 0.9 * (1 - (Y - oy) / laenge))
            mix(Y - 1, kante + seite * d, (170, 230, 250), 0.5 * (1 - (Y - oy) / laenge))
        for Y in range(oy, y1):
            mix(Y, kante + seite, (200, 245, 255), 0.6)


def fall_tropfen(a, wasser, land, frame):
    """Tropfen-Kaskade: statt eines geschlossenen Strahls fallen einzelne Wasserbrocken (runde Pixeltropfen mit
    Glanzpunkt) in Reihen hinab, oben dicht, unten vereinzelt; an der Kante kleine Wellen."""
    f = frame or 0
    oy, y1, x0, x1, unten, mix = _fall_basis(a, wasser, land)
    rs = np.random.RandomState(1933)
    form = [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (1, 3), (2, 0), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2)]
    for seite in (-1, 1):
        kante = x0 if seite < 0 else x1 - 1
        for Y in range(oy, y1):
            mix(Y, kante + seite, (150, 225, 250), 0.8 if (Y + f) % 4 else 0.4)
        for k in range(140):
            d = rs.randint(1, 18)
            Y0 = oy + rs.randint(0, y1 - oy)
            weg = unten + 70 - Y0
            pos = ((rs.randint(40) + 4 * f) % 40) / 40.0
            Y = int(Y0 + pos * pos * weg)                          # beschleunigt (Schwerkraft)
            s_ = 0.95 * (1 - pos ** 2)
            if s_ < 0.1:
                continue
            X = kante + seite * d
            for (dy, dx) in form:
                mix(Y + dy, X + seite * dx, (50, 150, 210), s_)
            mix(Y + 1, X + seite * 1, (220, 250, 255), s_)
            mix(Y + 3, X + seite * 2, (24, 90, 150), s_ * 0.8)


def fall_speier(a, wasser, land, frame):
    """Wasserspeier: die Mauer bleibt offen, aber das Wasser schiesst in drei Strahlen im Bogen aus der Kante und
    faellt dann senkrecht hinab (Parabel), unten Gischt."""
    f = frame or 0
    oy, y1, x0, x1, unten, mix = _fall_basis(a, wasser, land)
    for seite in (-1, 1):
        kante = x0 if seite < 0 else x1 - 1
        for i, Ys in enumerate((oy + 14, oy + 44, oy + 74)):
            v = 2.6 + 0.3 * i
            pts = []
            for t in range(0, 400):
                tt = t / 10.0
                X = kante + seite * int(v * tt)
                Y = int(Ys + 0.12 * tt * tt * 10)
                if Y > unten + 50:
                    break
                pts.append((Y, X))
            for j, (Y, X) in enumerate(pts):
                q = (Y - Ys) / max(1, unten + 50 - Ys)
                for w_ in range(-3, 4):
                    c = (60, 165, 220) if abs(w_) < 2 else ((150, 225, 250) if w_ == -2 else (30, 100, 160))
                    mix(Y, X + w_, c, 0.9 * (1 - q * 0.7))
                if (j - 3 * f) % 9 < 2:
                    mix(Y, X, (225, 250, 255), 0.9 * (1 - q))
            Y, X = pts[-1]
            for k in range(14):                                    # Gischt am Ende
                r = 2 + (k * 7 + f * 3) % 9
                w = k * 0.9 + f
                mix(Y - int(r * abs(np.sin(w))) , X + int(r * np.cos(w)), (230, 250, 255), 0.7)
        for Y in range(oy, y1):
            mix(Y, kante + seite, (170, 235, 255), 0.6)


FALL_STILE = {}


def pfeil_marke(a, tx, ty, farbe, frame, ph):
    """Pfeilfeld passend zum Aufstellfeld: vier Eckklammern (wie feld_marken) und ein Doppel-Chevron nach Norden,
    beides direkt auf dem Boden, 1 px dunkler Schlagschatten rechts unten, Leuchten pulsiert."""
    p = 0.55 + 0.45 * puls(frame, ph)
    farbe = np.array(farbe, np.float32)
    X, Y = tx * T, ty * T
    pix = []
    for (ex, ey, sx, sy) in ((2, 2, 1, 1), (13, 2, -1, 1), (2, 13, 1, -1), (13, 13, -1, -1)):
        for d in range(3):
            pix += [(Y + ey, X + ex + sx * d), (Y + ey + sy * d, X + ex)]
    for oy in (4, 8):                                           # zwei Chevrons uebereinander
        for d in range(4):
            pix += [(Y + oy + d, X + 7 - d), (Y + oy + d, X + 8 + d)]
    for (yy, xx) in pix:                                        # Schatten zuerst
        a[yy + 1, xx + 1] = (a[yy + 1, xx + 1] * 0.75).astype(np.uint8)
    for (yy, xx) in pix:
        a[yy, xx] = np.clip(a[yy, xx] * (1 - 0.8 * p) + farbe * 0.8 * p, 0, 255).astype(np.uint8)


def schatten19(img, objs, cache, boden):
    """Schatten nach den Regeln: Kontaktschatten direkt am Fuss (folgt der echten Fussform), Schlagschatten = die
    Silhouette diagonal nach rechts unten gelegt und auf die Haelfte gestaucht; nur auf dem Boden der Fussebene."""
    a = np.array(img).astype(np.float32)
    Hp, Wp = boden.shape
    kontakt = np.zeros((Hp, Wp), bool)
    wurf = np.zeros((Hp, Wp), bool)
    for o in objs:
        m = np.array(cache[o['datei']].getchannel('A')) >= 128
        zeilen = np.nonzero(m.any(axis=1))[0]
        breite = m.sum(axis=1)
        zu = int(max(r for r in zeilen if breite[r] >= 0.45 * breite.max()))   # Unterkante des Sockels (nicht Seilende)
        for r in zeilen:
            k = max(0, zu - r)                                    # Hoehe ueber dem Fuss
            xs = np.nonzero(m[r])[0]
            ty = o['y'] + zu + int(round(k * 0.30))
            tx = o['x'] + xs + int(round(k * 0.45)) + 1
            ok = (tx >= 0) & (tx < Wp) & (0 <= ty < Hp)
            if 0 <= ty < Hp:
                wurf[ty, tx[ok]] = True
        fuss = m[max(0, zu - 2):zu + 1].any(axis=0)
        xs = np.nonzero(fuss)[0]
        for dy in (0, 1):
            Y = o['y'] + zu + dy
            if 0 <= Y < Hp:
                kontakt[Y, o['x'] + xs.min() + dy:o['x'] + xs.max() + 2] = True
    wurf = np.array(Image.fromarray((wurf * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
    wurf &= boden & ~kontakt
    kontakt &= boden
    a[wurf, :3] *= 0.72
    a[kontakt, :3] *= 0.55
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def kaikante(a, kai, wasser=None):
    """Kaikante: heller Stein an jeder Wasserseite des Pflasters (6 px breit, Licht zur Wasserseite, Fugen alle
    16 px, Schatten zum Pflaster). Laeuft auch an den Kanaelen entlang (Kanal-Variante)."""
    if wasser is None or not kai.any():
        return
    Hp, Wp = wasser.shape
    pfl = np.zeros_like(wasser)
    ys, xs = np.nonzero(kai)
    pfl[ys.min():, xs.min() - 48:xs.max() + 49] = True
    pfl &= ~wasser
    rechts = np.zeros_like(wasser); rechts[:, xs.min() - 48:] = True
    pfl &= rechts
    d = np.zeros((Hp, Wp), np.int16)
    cur = wasser.copy()
    for i in range(1, 8):
        cur = np.array(Image.fromarray((cur * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
        neu = cur & pfl & (d == 0)
        d[neu] = i
    stein = {1: (206, 210, 200), 2: (186, 190, 182), 3: (170, 174, 166), 4: (170, 174, 166), 5: (156, 160, 152),
             6: (120, 124, 118)}
    for i, c in stein.items():
        a[d == i] = c
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    fuge = (d >= 2) & (d <= 5) & (((xx % 16 == 0) & (np.roll(d, 1, 0) > 0)) | ((yy % 16 == 0) & (np.roll(d, 1, 1) > 0)))
    a[fuge & (np.roll(d, 1, 0) == d)] = (128, 132, 124)
    a[fuge & (np.roll(d, 1, 1) == d)] = (128, 132, 124)
    a[d == 7] = (a[d == 7] * 0.72).astype(np.uint8)


def rand_hafen(a, land, ring, front, rechts, frame):
    """Rand der Hafen-Plattform (rechts), Varianten zum Vergleich (K19_RAND):
      netz  - wie bisher: dunkler Randring aus Pflaster, cyan glimmende Kante, Metallfront
      kai   - Kaimauer: Ring aus hellem Granit (Bloecke 16x8, Licht oben), Front aus Steinquadern, keine cyan Kante
      bunt  - wie die linke Plattform: blauer Network-Randring mit cyan Kante (Pflaster nur innen)
      warn  - Hafenkante: dunkler Beton mit gelb-schwarzer Warnmarkierung innen, Metallfront, keine cyan Kante"""
    if RAND == 'netz':
        return
    Hp, Wp = land.shape
    r = ring & rechts
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    ak = kontur(land)
    if RAND == 'bunt':
        bt = k16.boden_textur(Wp // T, Hp // T)
        a[r & ~ak] = (bt[r & ~ak] * 0.72).astype(np.uint8)
        mischen(a, kontur(land & ~ak) & rechts, CYAN, 0.4 + 0.3 * puls(frame, 0.6))
        return
    if RAND == 'kai':
        c = np.zeros((Hp, Wp, 3), np.float32)
        c[:] = (176, 180, 170)
        versatz = np.where((yy // 8) % 2 == 1, 8, 0)
        c[((xx + versatz) % 16 == 15)] = (128, 132, 124)          # Stossfugen
        c[(yy % 8 == 7)] = (120, 124, 116)                         # Lagerfugen
        c[(yy % 8 == 0)] = (206, 210, 200)                         # Licht oben
        c[((xx + versatz) % 16 == 0) & (yy % 8 != 7)] = (196, 200, 190)
        a[r] = c[r].astype(np.uint8)
        a[r & ak] = (40, 44, 48)
        innen = land & ~ring & rechts
        a[innen & np.roll(r, 1, 0)] = (a[innen & np.roll(r, 1, 0)] * 0.7).astype(np.uint8)   # Schatten der Mauerkrone
        a[innen & np.roll(r, 1, 1)] = (a[innen & np.roll(r, 1, 1)] * 0.8).astype(np.uint8)
        fr_ = front & (xx >= np.nonzero(rechts.any(axis=0))[0].min() - 2)
        oben = fr_ & ~np.roll(fr_, 1, 0)
        tiefe = np.zeros((Hp, Wp), np.int16)
        cur = oben.copy(); d = 0
        while cur.any() and d < 12:
            tiefe[cur] = d + 1; d += 1
            cur = np.roll(cur, 1, 0) & fr_ & (tiefe == 0)
        st = np.zeros((Hp, Wp, 3), np.float32)
        st[:] = (132, 136, 128)
        st[(xx % 16 == 15)] = (96, 100, 94)
        st[tiefe == 1] = (170, 174, 164)
        st[tiefe >= 8] = (92, 96, 90)
        st[tiefe >= 10] = (40, 44, 46)
        a[fr_] = st[fr_].astype(np.uint8)
        return
    if RAND == 'warn':
        beton = a.copy()
        g = np.array((96, 100, 104), np.float32)
        a[r] = np.clip(beton[r] * 0.35 + g * 0.65, 0, 255).astype(np.uint8)
        innenkante = r & ~np.roll(r, 3, 0) | r & ~np.roll(r, -3, 0) | r & ~np.roll(r, 3, 1) | r & ~np.roll(r, -3, 1)
        band = r & ~ak & ~(r & ~np.roll(r, 6, 0) & ~np.roll(r, -6, 0) & ~np.roll(r, 6, 1) & ~np.roll(r, -6, 1))
        streifen = ((xx + yy) // 4) % 2 == 0
        a[band & innenkante & streifen] = (236, 196, 60)
        a[band & innenkante & ~streifen] = (30, 30, 34)
        a[r & ak] = (20, 22, 26)


WASSER_STILE.update(terrassen=hafenbecken, sand=wasser_sand, kaustik=wasser_kaustik, tief=wasser_tief,
                    netz=wasser_netz, klassik=wasser_klassik)


FALL_STILE.update(vorhang=ueberlauf, klassik=fall_klassik, daten=fall_daten, schleier=fall_schleier,
                  tropfen=fall_tropfen, speier=fall_speier)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    gross = lambda m: np.kron(m, np.ones((T, T), int)).astype(bool)
    a = np.zeros((Hp, Wp, 3), np.uint8)
    a[:] = LEER
    land = gross(kl != '.')
    ring = gross(kl == 'r')
    wasser = gross(kl == 'w')
    leer = ~land
    k16.leere(a, leer, frame)
    # ------------------------------------------------------------------ Boden (links Platten, rechts Pflaster)
    bt = k16.boden_textur(cols, rows)
    pt = pflaster_textur(cols, rows)
    rechts = np.zeros((Hp, Wp), bool)
    rechts[:, lay['raeume'][1][0] * T:] = True
    a[land] = np.where(rechts[land][:, None], pt[land], bt[land])
    a[ring] = (a[ring] * 0.72).astype(np.uint8)
    innen = land & ~ring & ~wasser
    a[innen & np.roll(ring, -1, 0)] = (18, 26, 46)
    a[innen & np.roll(ring, 1, 0) & ~rechts] = (78, 104, 140)
    a[innen & np.roll(ring, 1, 0) & rechts] = (150, 166, 168)
    kaikante(a, gross(kl == 'k'), wasser)
    for i, (x0, y0) in enumerate(lay['raeume']):
        fy, fx = np.nonzero(kl[y0:y0 + lay['raum'][1], x0:x0 + lay['raum'][0]] == 'f')   # Aufstellfeld laut Layout
        k17.feld_marken(a, x0 + fx.min(), y0 + fy.min(), fx.max() - fx.min() + 1, fy.max() - fy.min() + 1, frame)
        if i == 0:
            for (px, py) in lay['platten']:
                bodenplatte(a, x0 + px, y0 + py)
        else:
            k17.ringmarke(a, x0 + 14, y0 + 8, frame)
    a = WASSER_STILE[WASSER](a, wasser, frame)
    sch = wasser & (np.roll(ring, 2, 1) | np.roll(ring, 1, 1))     # Westmauer: Schatten aufs Wasser (Licht oben links)
    a[sch] = (a[sch] * 0.75).astype(np.uint8)
    # Pfeile im Stil des Sammelplatzes (Nutzerwunsch): keine dunkle Kachel, sondern Eckklammern wie beim
    # Aufstellfeld plus ein Doppelpfeil direkt auf dem Boden; cyan = Ankunft, gold = weiter. Leuchten nacheinander.
    n = 0
    for y in range(rows):
        for x in range(cols):
            if kl[y, x] in 'zg':
                pfeil_marke(a, x, y, (110, 225, 250) if kl[y, x] == 'z' else (250, 200, 90), frame, n * 0.25)
                n += 1
    # ------------------------------------------------------------------ Kanten, Front, Leere
    front = k16.front_und_faeden(a, land, frame)
    ak = kontur(land)
    a[ak] = (8, 14, 30)
    mischen(a, kontur(land & ~ak), CYAN, 0.4 + 0.3 * puls(frame, 0.6))
    rand_hafen(a, land, ring, front, rechts & ~wasser, frame)
    nah = np.array(Image.fromarray(((land | front) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25))) > 0
    rest = leer & ~front
    k16.straenge(a, rest & ~nah, frame, seed=1919, zonen=((8, 88), (552, 664), (1128, 1208), (100, 1100)), n=6,
                 y_bereich=(60, 440))
    stellen = [(20, 40), (40, 300), (16, 500), (300, 18), (720, 30), (1000, 20), (556, 140), (560, 330),
               (556, 500), (1172, 150), (1172, 340), (1160, 540), (220, 540), (860, 545)]
    k16.fragmente(a, rest & ~nah, frame, seed=1920, stellen=stellen)
    FALL_STILE.get(FALL, ueberlauf)(a, wasser, land, frame)
    lvl = np.zeros((Hp, Wp), np.uint8)
    lvl[land] = 2
    lvl[wasser] = 1
    lvl[front] = 9
    hx, hy = lay['raeume'][1]                                    # Mauerkrone oben am Hafen: Mauer, nicht begehbar
    lvl[hy * T:(hy + 1) * T, hx * T:(hx + lay['raum'][0]) * T] = 9
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(wasser))
        np.save(os.path.join(KARTE, 'leere.npy'), np.packbits(rest))
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
    pf_ = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf_):
        objs = sorted((o for o in json.load(open(pf_)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o['y'] + o['fuss'])
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            img = schatten19(img, objs, cache, lvl == 2)
            vor = np.array(img)
            k4.objekte_zeichnen(img, objs, cache, np.zeros((Hp, Wp), bool), frame)
            img = img.copy()
            k4.animieren(img, objs, cache, frame or 0, ruhig=frame is None)
            k8.verdeckung(img, objs, cache, lvl, vor)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 19 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
