"""Karte 35 - Shinjuku Digital Fog (A03 Nr. 2), Gelaende + Objekte + Animation (4 Bilder).

  python3 tools/karte35_layout.py && python3 tools/karte35_bauen.py && python3 tools/karte35_objekte.py && python3 tools/karte35_bauen.py

Kacheln wie Karte 18/31 (Gehwegplatten, Asphalt, Rasen): Bordsteine an allen Fahrbahnkanten, gelbe Mittelstriche nur
auf geraden Strassenstuecken (nicht auf Kreuzungen und Zebrastreifen), Zebrastreifen quer ueber die Nord-Sued-Strassen,
Gruenstreifen mit Steinkante. Ausserhalb der Stadt liegt der digitale Nebel (cyan-violett, Schwaden ziehen nahtlos,
dazu blinkende Datenpixel) - nicht begehbar; die Ausgaenge fuehren mit Teleportern hinein.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte18_bauen as k18
import karte30_bauen as k30

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte35')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte35')
T = 16
N_FRAMES = 4                     # Regel: hoechstens 4 Animationsbilder
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
kb.N_FRAMES = N_FRAMES
k6.N_FRAMES = N_FRAMES
H = k4.H
gross, kontur, dunkeln = k18.gross, k18.kontur, k18.dunkeln
GELB = np.array(H('#d8b048'), np.uint8)
WEISS = np.array(H('#e4e8ee'), np.uint8)
NEBEL_DIGITAL = np.array(H('#7c86b8'), np.float32)               # kuehles Blauviolett (digitaler Nebel)


def lauflaenge(m, achse):
    """Laenge des zusammenhaengenden True-Laufs je Zelle entlang der Achse (0 = senkrecht, 1 = waagerecht)."""
    out = np.zeros(m.shape, int)
    mm = m if achse == 1 else m.T
    oo = out if achse == 1 else out.T
    for i in range(mm.shape[0]):
        j = 0
        while j < mm.shape[1]:
            if not mm[i, j]:
                j += 1; continue
            e = j
            while e < mm.shape[1] and mm[i, e]:
                e += 1
            oo[i, j:e] = e - j
            j = e
    return out


def markierungen(a, kl, lay):
    """Mittelstriche (gelb, gestrichelt) auf den geraden Strassenstuecken, Zebrastreifen weiss. Abgeschnittene
    Strichreste unter 10 px werden verworfen (keine gelben Fremdpixel an Kreuzungen)."""
    roh = a.copy()
    _markierungen(a, kl, lay)
    gelb = np.all(a == GELB, axis=-1) & ~np.all(roh == GELB, axis=-1)
    rest = gelb & ~k4.splitter_weg(gelb, 10)
    a[rest] = roh[rest]


def _markierungen(a, kl, lay):
    asph_k = kl == 'a'
    asphalt = gross(asph_k)
    senk = lauflaenge(asph_k, 0)                                       # Kachel-Lauflaengen der Fahrbahn
    waag = lauflaenge(asph_k, 1)
    zebra = np.zeros_like(asphalt)
    for (x0, x1, y0, y1, art) in lay['zebra']:
        zebra[y0 * T:(y1 + 1) * T, x0 * T:(x1 + 1) * T] = True
    sperre = np.array(Image.fromarray((zebra * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(21))) > 0
    tp = np.zeros_like(asphalt)                                        # Teleporter: Striche enden mit Abstand
    for t_ in lay['teleporter']:
        tp[t_['y'] * T:(t_['y'] + t_['h']) * T, t_['x'] * T:(t_['x'] + t_['b']) * T] = True
    sperre |= np.array(Image.fromarray((tp * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(25))) > 0
    # Mittellinie exakt in der Mitte der jeweiligen Fahrbahn: je Kachelspalte (bzw. -zeile) den Fahrbahnlauf durch das
    # Strassenband suchen, gleiche Mitten zu Abschnitten zusammenfassen; Kreuzungen (zu breite Laeufe) bleiben frei
    def abschnitte(band, quer):
        y0, y1, x0, x1 = band
        stuecke = []
        for x in range(x0, x1 + 1):
            spalte = asph_k[:, x] if quer else asph_k[x, :]
            m = (y0 + y1) // 2
            if not spalte[m]:
                stuecke.append(None); continue
            a_, b_ = m, m
            while a_ - 1 >= 0 and spalte[a_ - 1]:
                a_ -= 1
            while b_ + 1 < len(spalte) and spalte[b_ + 1]:
                b_ += 1
            stuecke.append((a_, b_) if b_ - a_ + 1 <= (y1 - y0 + 1) else None)
        out, i = [], 0
        while i < len(stuecke):
            if stuecke[i] is None:
                i += 1; continue
            j = i
            while j + 1 < len(stuecke) and stuecke[j + 1] == stuecke[i]:
                j += 1
            out.append((x0 + i, x0 + j, stuecke[i]))
            i = j + 1
        return out
    frei = asphalt & ~sperre
    for band in ((14, 21, 30, 93), (36, 42, 4, 81), (56, 62, 4, 93)):
        for (xa, xb, (ya, yb)) in abschnitte(band, True):
            k30.striche(a, frei, xa * T, (xb + 1) * T, (ya + yb + 1) * T // 2 - 1, GELB)
    for band in ((36, 42, 22, 77), (76, 82, 1, 77)):
        for (ya, yb, (xa, xb)) in abschnitte(band, False):
            k30.striche(a, frei, ya * T, (yb + 1) * T, (xa + xb + 1) * T // 2 - 1, GELB, senkrecht=True)
    for (x0, x1, y0, y1, art) in lay['zebra']:
        for y in range(y0 * T + 2, (y1 + 1) * T - 2):
            for x in range(x0 * T, (x1 + 1) * T):
                if asphalt[y, x] and (x % 8) < 5 and 3 <= x - x0 * T < (x1 - x0 + 1) * T - 3:
                    a[y, x] = WEISS


def kanaldeckel(a, kl, seed=35):
    """Wenige runde Kanaldeckel und Gullys am Fahrbahnrand (Vorlage), unregelmaessig, fest (kein Flimmern)."""
    rs = np.random.RandomState(seed)
    rows, cols = kl.shape
    mitte_y, mitte_x = (17, 18, 19, 39, 57, 58, 59), (38, 39, 78, 79)              # Kachelreihen/-spalten der Mittellinien
    kand = [(y, x) for y in range(3, rows - 3) for x in range(3, cols - 3) if kl[y, x] == 'a'
            and all(kl[y + dy, x + dx] == 'a' for dy in (-1, 0, 1) for dx in (-1, 0, 1))
            and y not in mitte_y and x not in mitte_x]
    rs.shuffle(kand)
    gesetzt = []
    for (y, x) in kand:
        if len(gesetzt) >= 14:
            break
        if any(abs(y - yy) + abs(x - xx) < 12 for (yy, xx) in gesetzt):
            continue
        gesetzt.append((y, x))
        cx, cy = x * T + 8, y * T + 8
        yy, xx = np.ogrid[-5:6, -5:6]
        d = np.sqrt(yy ** 2 + xx ** 2)
        sub = a[cy - 5:cy + 6, cx - 5:cx + 6]
        sub[d <= 5] = H('#2a2e38')
        sub[d <= 4] = H('#4a505e')
        sub[(d <= 4) & ((yy + xx) % 3 == 0)] = H('#3a3f4c')
        sub[(d > 3.4) & (d <= 4) & (yy < 0)] = H('#6a7080')


def nebel_digital(a, land, frame):
    """Digitaler Nebel ausserhalb der Stadt: Nebel von Karte 18 in kuehlem Blauviolett, dazu blinkende Datenpixel
    (2x2, cyan/violett) im dichten Nebel - nur dort, nie in der Stadt."""
    alt = k18.NEBEL
    k18.NEBEL = NEBEL_DIGITAL
    try:
        dichte = k18.nebel(a, land, frame)
    finally:
        k18.NEBEL = alt
    f = frame or 0
    rs = np.random.RandomState(3535)
    Hh, W = land.shape
    n = 900
    ys, xs = rs.randint(0, Hh // 2, n) * 2, rs.randint(0, W // 2, n) * 2
    phase = rs.randint(0, 4, n)
    farbe = rs.randint(0, 3, n)
    for y, x, p, c in zip(ys, xs, phase, farbe):
        if dichte[y, x] < 0.85 or (f + p) % 4 == 3:
            continue
        hell = (1.0, 0.75, 0.55, 0)[(f + p) % 4]
        col = np.array(((120, 240, 255), (190, 150, 255), (230, 236, 255))[c], np.float32)
        a[y:y + 2, x:x + 2] = np.clip(a[y:y + 2, x:x + 2] * (1 - 0.7 * hell) + col * 0.7 * hell, 0, 255).astype(np.uint8)
    return dichte


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    a = k18.textur('g', cols, rows)                                   # Gehwegplatten
    asph_k = np.isin(kl, ['a', 'x'])
    asphalt = gross(asph_k)
    a[asphalt] = k18.textur('s', cols, rows)[asphalt]
    rasen = gross(kl == 'n')
    k18.mittelstreifen(a, rasen, k18.textur('n', cols, rows))         # Gruenstreifen mit Steinkante
    k18.bordsteine(a, asphalt, ~asphalt)
    markierungen(a, kl, lay)
    kanaldeckel(a, kl)
    land = ~gross(kl == 'x')
    lvl = np.ones((Hp, Wp), np.uint8)
    leere = ~land
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
            k4.objekte_zeichnen(img, objs, cache, land, frame, ebenen=lvl.astype(np.int16))
            k4.animieren(img, objs, cache, frame or 0)
            k6.animieren_k6(img, objs, cache, frame or 0)
            kb.laternen_licht(img, [o for o in objs if o.get('anim') == 'laterne'], frame)
    a = np.array(img.convert('RGB'))
    nebel_digital(a, land, frame)                                     # Nebel liegt ueber allem am Rand
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
        if not os.path.exists(pf):
            img.save(os.path.join(KARTE, 'terrain_basis.png'))
    print('Karte 35 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
