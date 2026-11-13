# Grundgeruest aus karte39 (tools/neue_karte.py) - an die Vorlage von karte39 "West Shinjuku Siege" anpassen!
# Grundgeruest aus karte35 (tools/neue_karte.py) - an die Vorlage von karte39 "Shinjuku Backstreets" anpassen!
"""Karte 39 - Shinjuku Backstreets (A03 Nr. 3), Gelaende + Objekte + Animation (4 Bilder).

  python3 tools/karte39_layout.py && python3 tools/karte39_bauen.py && python3 tools/karte39_objekte.py && python3 tools/karte39_bauen.py

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
KARTE = os.path.join(ROOT, 'maps', 'karte39')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte39')
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
    rest = gelb & ~k4.splitter_weg(gelb, 14)                          # auch 2x6-Stummel vor Zebrastreifen
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
    P = lay.get('versatz', 0)                                          # Karte ringsum erweitert (Baumguertel)
    rows_, cols_ = kl.shape
    for band in lay['strassen_h']:
        for (xa, xb, (ya, yb)) in abschnitte(band, True):
            k30.striche(a, frei, xa * T, (xb + 1) * T, (ya + yb + 1) * T // 2 - 1, GELB)
    for band in lay['strassen_v']:
        for (ya, yb, (xa, xb)) in abschnitte(band, False):
            k30.striche(a, frei, ya * T, (yb + 1) * T, (xa + xb + 1) * T // 2 - 1, GELB, senkrecht=True)
    for (x0, x1, y0, y1, art) in lay['zebra']:
        for y in range(y0 * T + (2 if art == 'h' else 0), (y1 + 1) * T - (2 if art == 'h' else 0)):
            for x in range(x0 * T + (0 if art == 'h' else 2), (x1 + 1) * T - (0 if art == 'h' else 2)):
                if not asphalt[y, x]:
                    continue
                if art == 'h' and (x % 8) < 5 and 3 <= x - x0 * T < (x1 - x0 + 1) * T - 3:
                    a[y, x] = WEISS
                if art == 'v' and (y % 8) < 5 and 3 <= y - y0 * T < (y1 - y0 + 1) * T - 3:
                    a[y, x] = WEISS


def kanaldeckel(a, kl, seed=36, P=0, lay=None):
    """Wenige runde Kanaldeckel und Gullys am Fahrbahnrand (Vorlage), unregelmaessig, fest (kein Flimmern)."""
    rs = np.random.RandomState(seed)
    rows, cols = kl.shape
    mitte_y = tuple(y for (y0, y1, _, _) in lay['strassen_h'] for y in range((y0 + y1) // 2 - 1, (y0 + y1) // 2 + 2))
    mitte_x = tuple(x for (x0, x1, _, _) in lay['strassen_v'] for x in range((x0 + x1) // 2 - 1, (x0 + x1) // 2 + 2))              # Kachelreihen/-spalten der Mittellinien
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


def plaetze_boden(a, kl, objs):
    """Boden passend zu den Platz-Objekten (Nutzer: neue Sachen wirken nur draufgesetzt): Granit-Vorplatz vor dem
    Rathaus mit Achsweg, rundes Ringpflaster um den Brunnen, Holzterrasse unter der Cafe-Ecke, Steinsockel-Platz unter
    Skulptur und Kuebeln, Pflasterflaeche am Kiosk. Nur auf Platz-/Gehwegflaeche, nie auf der Fahrbahn."""
    Hh, W = a.shape[:2]
    erlaubt = gross(np.isin(kl, ['q', 'g', 'b', 'k']))
    yy, xx = np.mgrid[0:Hh, 0:W]

    def kante(m, c=(96, 100, 108)):
        p_ = np.pad(m, 1)
        r = m & ~(p_[:-2, 1:-1] & p_[2:, 1:-1] & p_[1:-1, :-2] & p_[1:-1, 2:])
        a[r & erlaubt] = c

    def box(name):
        return [o for o in objs if o['basis'].startswith(name)]
    for o in box('rathaus'):                                      # Vorplatz in Gebaeudebreite + Achsweg nach Sueden
        sp_w = 210
        x0, x1 = o['x'] - 56, o['x'] + sp_w + 56
        fuss = o['y'] + o['fuss']
        m = (xx >= x0) & (xx < x1) & (yy >= fuss - 24) & (yy < fuss + 56)
        ax = o['x'] + sp_w // 2
        m |= (abs(xx - ax) < 40) & (yy >= fuss + 56) & (yy < fuss + 120)
        m &= erlaubt
        g = ((xx // 32 + yy // 24) % 2).astype(np.float32)
        basis = np.array((176, 172, 162), np.float32)
        a[m] = np.clip(basis * (0.96 + 0.04 * g[m, None]), 0, 255).astype(np.uint8)
        a[m & ((xx % 32 == 0) | (yy % 24 == 0))] = (150, 146, 138)
        kante(m)
    for o in box('brunnen'):                                      # Ringpflaster
        cx, cy = o['x'] + 54, o['y'] + o['fuss'] - 34
        r = np.sqrt((xx - cx) ** 2 + ((yy - cy) * 1.5) ** 2)
        m = (r < 96) & erlaubt
        band = (r // 12).astype(int) % 2
        a[m & (band == 0)] = (186, 186, 178)
        a[m & (band == 1)] = (168, 168, 160)
        fuge = m & (np.abs(r % 12) < 1)
        a[fuge] = (140, 140, 134)
        kante(m)
    cafe = box('platz/03') + box('platz/12')                      # Holzterrasse
    if cafe:
        x0 = min(o['x'] for o in cafe) - 10; x1 = max(o['x'] + 57 for o in cafe) + 10
        y0 = min(o['y'] + o['fuss'] for o in cafe) - 30; y1 = max(o['y'] + o['fuss'] for o in cafe) + 10
        m = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1) & erlaubt
        holz = np.array((150, 112, 78), np.float32)
        streifen = ((yy // 6) % 2 == 0)
        a[m] = holz.astype(np.uint8)
        a[m & streifen] = (162, 122, 86)
        a[m & (yy % 6 == 0)] = (112, 82, 56)
        a[m & ((xx + (yy // 6) * 23) % 48 == 0)] = (112, 82, 56)
        kante(m, (92, 66, 44))
    sk = box('platz/02')
    if sk:                                                        # Sockelplatz unter Skulptur und Kuebeln
        o = sk[0]
        cx, cy = o['x'] + 30, o['y'] + o['fuss'] - 6
        m = (np.abs(xx - cx) < 116) & (np.abs(yy - cy) < 22) & erlaubt
        a[m] = (190, 186, 176)
        a[m & ((xx - cx) % 32 == 0)] = (160, 156, 148)
        kante(m)
    for o in box('gross/bruecke'):                                # Bruecke in den Boden einbinden (Nutzer: Uebergang hart)
        al = np.array(Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA'))[..., 3] > 0
        h_, w_ = al.shape
        X, Y = o['x'], o['y']
        fuss = Y + h_ - 1
        # weicher Schatten der Bruecke: Silhouette nach unten auf den Boden gelegt (Deck ~60 px hoch), stark verwischt
        sil = np.zeros((Hh, W), np.float32)
        ys_, xs_ = np.nonzero(al)
        ty_ = np.clip(ys_ + Y + 8, 0, Hh - 1); tx_ = np.clip(xs_ + X + 6, 0, W - 1)   # Draufsicht: knapp versetzt
        sil[ty_, tx_] = 1.0
        sil[fuss + 6:] = 0
        sil = np.array(Image.fromarray((sil * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
        a[:] = np.clip(a * (1 - 0.28 * sil[..., None]), 0, 255).astype(np.uint8)
        # Treppen-/Rampenfuesse: unterster deckender Punkt in den aeussersten 24 Spalten links und rechts
        for (c0, c1) in ((0, 24), (w_ - 24, w_)):
            sp_ = al[:, c0:c1]
            ys_e = np.nonzero(sp_.any(1))[0]
            yb = ys_e.max()
            xs_e = np.nonzero(sp_[yb - 3:yb + 1].any(0))[0] + c0
            fx0, fx1 = X + xs_e.min(), X + xs_e.max() + 1
            fy_ = Y + yb
            m = (xx >= fx0 - 10) & (xx < fx1 + 10) & (yy >= fy_ - 8) & (yy < fy_ + 24) & erlaubt
            a[m] = (178, 174, 164)
            a[m & ((xx - fx0) % 24 == 0)] = (150, 146, 138)
            kante(m)
        unten = al[h_ - 4:].any(0)                                # Stuetzen/Pfeiler: Kontaktschatten am Fuss
        xg = 0
        while xg < w_:
            if unten[xg]:
                e = xg
                while e < w_ and unten[e]:
                    e += 1
                if xg > 24 and e < w_ - 24:
                    sm = (xx >= X + xg - 1) & (xx < X + e + 4) & (yy > fuss) & (yy <= fuss + 4)
                    a[sm] = (a[sm] * 0.72).astype(np.uint8)
                xg = e
            else:
                xg += 1
    for o in box('gross/turm'):                                   # Hochhaus: Sockelschatten + Granit-Vorplatz am Eingang
        al = np.array(Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA'))[..., 3] > 0
        bb_ = Image.fromarray(al.astype(np.uint8) * 255).getbbox()
        x0, x1 = o['x'] + bb_[0], o['x'] + bb_[2]
        fuss = o['y'] + o['fuss']
        ax = (x0 + x1) // 2
        m = (xx >= ax - 64) & (xx < ax + 64) & (yy > fuss - 4) & (yy <= fuss + 16) & erlaubt
        a[m] = (178, 174, 164)
        a[m & ((xx - ax) % 32 == 0)] = (150, 146, 138)
        kante(m)
        sm = (xx >= x0 - 2) & (xx < x1 + 4) & (yy > fuss) & (yy <= fuss + 3) & erlaubt
        a[sm] = (a[sm] * 0.8).astype(np.uint8)
        rs_ = (xx >= x1) & (xx < x1 + 5) & (yy >= o['y'] + bb_[1] + 20) & (yy <= fuss) & erlaubt   # Schatten rechts
        a[rs_] = (a[rs_] * 0.82).astype(np.uint8)
    for o in box('k38/kiosk'):                                    # Pflasterflaeche am Kiosk
        m = (xx >= o['x'] - 10) & (xx < o['x'] + 86) & (yy >= o['y'] + o['fuss'] - 24) & (yy < o['y'] + o['fuss'] + 16)
        m &= erlaubt
        a[m] = (172, 168, 160)
        a[m & ((xx + yy) % 16 == 0)] = (150, 146, 140)
        kante(m)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    a = k18.textur('g', cols, rows)                                   # Gehwegplatten
    asph_k = np.isin(kl, ['a', 'x'])
    asphalt = gross(asph_k)
    a[asphalt] = k18.textur('s', cols, rows)[asphalt]
    for kk, art, f in (('q', 'v', (1.0, 1.0, 0.95)), ('b', 'k', (1.16, 1.04, 0.86)), ('k', 'k', (1.0, 1.0, 1.0))):
        m_ = gross(kl == kk)                                          # Platzpflaster, Ziegelplatz, dunkle Gehwegstreifen
        t_ = np.clip(k18.textur(art, cols, rows).astype(np.float32) * np.array(f), 0, 255).astype(np.uint8)
        a[m_] = t_[m_]
    wald = gross(kl == 'h')                                           # Boden im Baumguertel: Rasen (ohne Steinkante)
    a[wald] = k18.textur('n', cols, rows)[wald]
    rasen = gross(kl == 'n')
    k18.mittelstreifen(a, rasen, k18.textur('n', cols, rows))         # Gruenstreifen mit Steinkante
    k18.bordsteine(a, asphalt, ~asphalt)
    markierungen(a, kl, lay)
    kanaldeckel(a, kl, P=lay.get('versatz', 0), lay=lay)
    import karte38_bauen as k38b                                      # Bodenleben (Nutzer: Karte etwas leer): Risse,
    kl38 = np.where(kl == 'q', 'p', np.where(np.isin(kl, ['g', 'k', 'b']), 'k', 'x'))   # Flecken, Pfuetzen - flach
    k38b.boden_leben(a, kl38, frame)
    pf_ = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf_):
        plaetze_boden(a, kl, json.load(open(pf_)))
    land = np.zeros((Hp, Wp), bool)                                   # Nebel nur am aeussersten Rand ueber den Baeumen
    land[T:-T, T:-T] = True
    lvl = np.ones((Hp, Wp), np.uint8)
    leere = gross(kl == 'h')                                          # Baumguertel nicht begehbar (Kartenrand)
    lvl[leere] = 0                                                    # Kollision: Leere
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
    # (kein Nebel: normale Seitenstrassen; der Baumguertel schliesst die Karte ab)
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
        if not os.path.exists(pf):
            img.save(os.path.join(KARTE, 'terrain_basis.png'))
    print('Karte 39 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
