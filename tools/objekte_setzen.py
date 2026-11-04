"""Setzt die Objekte von Karte 01 (Wald, Deko, Sonderobjekte) und schreibt platzierung.json.

  python3 tools/objekte_setzen.py && python3 tools/karte_bauen.py

Sprites: assets/objekte/karte01/{baeume,deko,gross}/NN.png (PixelLab-Objekt-Manager,
siehe tools/pixellab_objekte.py). Die Auswahl, welche Kandidaten wofuer genutzt werden,
steht unten in AUSWAHL; feste Positionen kommen aus hoehenplan.json und FEST.
Alles ist mit festem Zufallsstartwert reproduzierbar.
"""
import json, os, random, sys
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte01')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
T = 16

# Welche Kandidaten wofuer (Nummern siehe jeweilige uebersicht.png); Zahl = Gewicht
AUSWAHL = {
    'wald': {'baeume/00': 5, 'baeume/01': 5, 'baeume/02': 4, 'baeume/15': 2, 'baeume/05': 1, 'baeume/04': 1,
             'baeume/06': 4, 'baeume/07': 3, 'baeume/09': 4, 'baeume/03': 1, 'baeume/08': 1},
    'waldrand': {'baeume/12': 3, 'baeume/13': 2, 'deko/25': 3, 'deko/26': 3, 'deko/61': 2, 'deko/27': 2,
                 'deko/28': 1, 'deko/05': 2},
    'wiese_klein': {'deko/00': 3, 'deko/01': 2, 'deko/02': 2, 'deko/03': 2, 'deko/04': 1, 'deko/30': 1,
                    'deko/38': 1, 'deko/05': 4, 'deko/06': 5, 'deko/29': 1, 'deko/37': 1},
    'wiese_mittel': {'deko/08': 2, 'deko/09': 1, 'deko/10': 2, 'deko/11': 2, 'deko/14': 1, 'deko/31': 1,
                     'deko/15': 1, 'deko/16': 1, 'deko/26': 2, 'deko/25': 2, 'deko/12': 1, 'deko/13': 1,
                     'deko/33': 1, 'deko/51': 1},
    'wiese_baum': {'baeume/00': 2, 'baeume/01': 2, 'baeume/02': 1, 'baeume/06': 2, 'baeume/09': 1,
                   'baeume/04': 1, 'baeume/15': 1, 'baeume/10': 1, 'baeume/11': 1, 'baeume/12': 2, 'baeume/13': 2},
    'strand': {'deko/24': 5, 'deko/21': 2, 'deko/60': 1, 'deko/20': 2, 'deko/58': 0.5, 'deko/37': 1, 'deko/08': 1,
               'deko/10': 1},
    'meer': {'deko/22': 4, 'deko/23': 3, 'deko/59': 2, 'gross/07': 1},
    'teich': {'deko/17': 3, 'deko/18': 2, 'deko/19': 3},
    'ufer': {'deko/07': 3, 'deko/05': 1},
}
# Animationsart je Sprite (fuer karte_bauen.bauen(frame) und Engine-Export)
WEHEN = ('deko/05', 'deko/06', 'deko/07', 'deko/24', 'deko/26', 'deko/61', 'deko/00', 'deko/01', 'deko/02',
         'deko/03', 'deko/04', 'deko/30', 'deko/38', 'deko/33')
WIPPEN = ('deko/17', 'deko/18', 'deko/19')
BLUMEN = ('deko/00', 'deko/01', 'deko/02', 'deko/03', 'deko/04', 'deko/30', 'deko/38', 'deko/27')
SCHATTEN = ('baeume/', 'gross/00', 'gross/01', 'gross/02', 'gross/07', 'gross/09', 'gross/10', 'gross/11',
            'gross/03', 'deko/09', 'deko/11', 'deko/12', 'deko/13', 'deko/25')

# Feste Objekte: (sprite, Ankerzelle x, y)  Anker = Mitte unten
FEST = [
    ('gross/01', 21, 11),   # grosser Rosabaum (Original: grosser Baum oben links)
    ('gross/00', 44, 13),   # uralter Runenbaum
    ('gross/02', 71, 11),   # Kristallbaum
    ('gross/00', 93, 55),   # Runenbaum im Osten
    ('gross/02', 26, 54),   # Kristallbaum im Suedwesten (Zielbild)
    ('gross/01', 86, 68),   # Rosabaum im Osten (Zielbild)
    ('gross/09', 30, 37),   # Runen-Findling auf der Wiese
    ('gross/09', 79, 45),
    ('gross/13', 9, 21),    # Wegweiser am Weg nach Westen
    ('gross/03', 97, 94),   # Zeltlager am Strand
    ('gross/14', 91, 96),   # Lagerfeuer
]


def lade(name, cache={}):
    if name not in cache:
        cache[name] = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
    return cache[name]


def strecken(img, hoehe):
    """Pixelart vertikal auf `hoehe` bringen, indem das mittlere Band wiederholt wird."""
    if img.height >= hoehe:
        return img
    oben, unten = img.height // 3, img.height - img.height // 3
    band = img.crop((0, oben, img.width, unten))
    out = Image.new('RGBA', (img.width, hoehe))
    out.paste(img.crop((0, 0, img.width, oben)), (0, 0))
    y = oben
    while y < hoehe - (img.height - unten):
        out.paste(band, (0, y)); y += band.height
    out.paste(img.crop((0, unten, img.width, img.height)), (0, hoehe - (img.height - unten)))
    return out


def main():
    rnd = random.Random(42)
    tm = json.load(open(os.path.join(KARTE, 'tilemap.json')))
    grid = json.load(open(os.path.join(KARTE, 'terrain_grid.json')))['grid']
    plan = json.load(open(os.path.join(KARTE, 'hoehenplan.json')))
    cls, cols, rows = tm['klassen'], tm['cols'], tm['rows']

    tcol, hcol = {}, {}
    for s in plan['segmente']:
        for vx in range(s['von'], s['bis'] + 1):
            tcol[vx], hcol[vx] = s['t'], s.get('h', 3)
    gesperrt = set()
    for tr in plan['treppen']:                # Treppen-Zuwege frei halten
        t, h = tcol[tr['x']], hcol[tr['x']]
        for x in range(tr['x'] - 1, tr['x'] + tr['breite'] + 1):
            for y in range(t - h - 4, t + 5):
                gesperrt.add((x, y))
    for x in range(cols):                     # Klippenwand + eine Zeile darunter
        t, h = max(tcol[x], tcol[x + 1]), max(hcol[x], hcol[x + 1])
        for y in range(min(tcol[x], tcol[x + 1]) - h, t + 2):
            gesperrt.add((x, y))
    for br in plan.get('bruecken', []) + plan.get('stege', []):
        for x in range(br['x'] - 1, br['x'] + br['breite'] + 1):
            for y in range(br['y'] - 2, br['y'] + br['hoehe'] + 3):   # Objekte wachsen nach oben
                gesperrt.add((x, y))

    def k(x, y):
        return cls[y][x] if 0 <= x < cols and 0 <= y < rows else '#'

    def frei_umgebung(x, y, r, erlaubt='g'):
        return all(k(x + dx, y + dy) in erlaubt and (x + dx, y + dy) not in gesperrt
                   for dx in range(-r, r + 1) for dy in range(-r, r + 1))

    objekte, belegt = [], set()

    def setze(name, ax, ay, ebene=1, bild=None, fuss_off=0):
        """Anker (ax, ay) in Pixeln = Mitte unten."""
        im = bild or lade(name)
        o = {'datei': name + '.png', 'x': int(ax - im.width // 2), 'y': int(ay - im.height),
             'fuss': im.height - fuss_off, 'ebene': ebene}
        if bild is not None:
            o['datei'] = name + '.png'
        if name.startswith(SCHATTEN):
            o['schatten'] = [int(im.width * 0.7), max(4, im.width // 7)]
        if name in WEHEN:
            o['anim'] = 'wehen'
        elif name in WIPPEN:
            o['anim'] = 'wippen'
        objekte.append(o)
        return o

    def wahl(gruppe):
        items = list(AUSWAHL[gruppe].items())
        return rnd.choices([n for n, _ in items], weights=[w for _, w in items])[0]

    # --- feste Objekte
    for name, cx, cy in FEST:
        setze(name, cx * T + 8, cy * T + 14)
        for dx in range(-2, 3):
            for dy in range(-3, 1):
                belegt.add((cx + dx, cy + dy))

    # Treppen, Bruecken, Steg und Wasserfaelle zeichnet karte_bauen.py selbst (tools/bauwerke.py, klippen.py)

    # --- Laternen am Wegrand: als Paar an Treppen und Brueckenkoepfen, sonst einzeln mit
    #     >= 14 Kacheln Abstand; immer auf der Wiese, vom Weg weg gerueckt
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import bauwerke
    bauwerke.laterne_bild().save(os.path.join(OBJ, 'laterne.png'))
    laternen = []

    def weg_richtung(cx, cy):
        """Richtung (dx, dy) zur naechsten Wegkachel (4er-Nachbarschaft) oder None."""
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if k(cx + dx, cy + dy) == 's' and grid[cy + dy][cx + dx] in 'RPp':
                return dx, dy
        return None

    boden = Image.open(os.path.join(KARTE, 'terrain_basis.png')).convert('RGB').load()

    def anker(cx, cy, richtung):
        richtung = richtung or weg_richtung(cx, cy) or (0, 0)
        ax = cx * T + 8 - 5 * richtung[0]
        ay = cy * T + 15 - (6 if richtung[1] > 0 else 0) + (2 if richtung[1] < 0 else 0)
        return ax, ay

    def auf_gras(cx, cy, richtung=None):
        """Steht der ganze Sockel (11 px breit) samt Rand im gerenderten Boden auf Gras?"""
        ax, ay = anker(cx, cy, richtung)
        for x in range(ax - 7, ax + 8):
            for y in (ay - 6, ay - 1, ay + 1):
                r_, g_, b_ = boden[min(max(x, 0), cols * T - 1), min(max(y, 0), rows * T - 1)]
                if not (g_ > r_ + 25 and g_ > b_ + 25):
                    return False
        return True

    def laterne_setzen(cx, cy, richtung=None):
        """Laterne auf Wiesenkachel (cx, cy), vom Weg weg in die Wiese gerueckt (Wegkante reicht
        eine halbe Kachel in die Nachbarkachel)."""
        ax, ay = anker(cx, cy, richtung)
        o = setze('laterne', ax, ay)
        o['anim'] = 'laterne'
        o['schatten'] = [18, 5]                  # Kontaktschatten unter dem Sockel
        belegt.update({(cx, cy), (cx, cy - 1), (cx, cy - 2), (cx, cy + 1)})
        laternen.append((cx, cy))

    def frei(cx, cy):
        return (k(cx, cy) == 'g' and (cx, cy) not in gesperrt and (cx, cy) not in belegt
                and not any(k(cx + dx, cy + dy) in 'wm' for dx in (-1, 0, 1) for dy in (-1, 0, 1)))

    # Paare (spiegelgleich links/rechts des Weges) unten an jeder Treppe ...
    for tr in plan['treppen']:
        t = tcol[tr['x']]
        gesetzt = False
        for y in range(t + 3, t + 7):                 # erst nah an der Treppe, dann weiter weg
            for d in (1, 2, 3):                       # gleicher Abstand links und rechts
                l, r = tr['x'] - 1 - d, tr['x'] + tr['breite'] + d
                if frei(l, y) and frei(r, y) and auf_gras(l, y, (1, 0)) and auf_gras(r, y, (-1, 0)):
                    laterne_setzen(l, y, (1, 0)); laterne_setzen(r, y, (-1, 0))
                    gesetzt = True
                    break
            if gesetzt:
                break
    # ... und am Westkopf jeder Bruecke (oberhalb und unterhalb des Weges)
    for br in plan.get('bruecken', []):
        wx = [x for x in range(br['x'], br['x'] + br['breite']) if k(x, br['y'] + br['hoehe'] // 2) == 'w']
        if not wx:
            continue
        mitte = br['y'] + br['hoehe'] // 2
        r0 = r1 = mitte
        x = min(wx) - 3
        while k(x, r0 - 1) == 's': r0 -= 1
        while k(x, r1 + 1) == 's': r1 += 1
        fertig = False
        for d in (1, 2):                          # gleicher Abstand ober- und unterhalb des Weges
            for xx in (x, x - 1, x - 2):
                if frei(xx, r0 - d) and frei(xx, r1 + d) and auf_gras(xx, r0 - d, (0, 1)) \
                        and auf_gras(xx, r1 + d, (0, -1)):
                    laterne_setzen(xx, r0 - d, (0, 1)); laterne_setzen(xx, r1 + d, (0, -1))
                    fertig = True
                    break
            if fertig:
                break
    # einzelne Laternen gleichmaessig entlang der uebrigen Wege
    kand = []
    for cy in range(2, rows - 2):
        for cx in range(2, cols - 2):
            if grid[cy][cx] == 'G' and frei(cx, cy) and weg_richtung(cx, cy) and auf_gras(cx, cy):
                kand.append((rnd.random(), cx, cy))
    kand.sort()
    for _, cx, cy in kand:
        if all(abs(cx - lx) + abs(cy - ly) >= 14 for lx, ly in laternen):
            laterne_setzen(cx, cy)
    print(len(laternen), 'Laternen')

    # --- Wald: dichtes, versetztes Raster
    for ay in range(8, rows * T + 8, 15):
        versatz = rnd.randint(0, 10)
        for ax in range(versatz, cols * T, 19):
            px, py = ax + rnd.randint(-5, 5), ay + rnd.randint(-4, 4)
            cx, cy = px // T, py // T
            if not (0 <= cx < cols and 0 <= cy < rows) or grid[cy][cx] != 'F':
                continue
            if not frei_umgebung(cx, cy, 1) or (cx, cy) in belegt:
                continue
            setze(wahl('wald'), px, py + 2)

    # --- Waldrand, Wiese, Strand, Wasser: je Kachel wuerfeln
    for cy in range(rows):
        for cx in range(cols):
            if (cx, cy) in gesperrt or (cx, cy) in belegt:
                continue
            ch, kl = grid[cy][cx], k(cx, cy)
            px, py = cx * T + rnd.randint(3, 13), cy * T + rnd.randint(8, 15)
            r = rnd.random()
            if kl == 'g' and ch != 'F':
                am_wald = any(grid[cy + dy][cx + dx] == 'F' for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                              if 0 <= cy + dy < rows and 0 <= cx + dx < cols)
                if am_wald and frei_umgebung(cx, cy, 0) and r < 0.22:
                    setze(wahl('waldrand'), px, py)
                elif frei_umgebung(cx, cy, 1) and r < 0.012:
                    setze(wahl('wiese_baum'), px, py); belegt.update({(cx + 1, cy), (cx - 1, cy), (cx, cy - 1)})
                elif frei_umgebung(cx, cy, 1) and r < 0.03:          # mittlere Deko: 1 Kachel Abstand zu Weg/Wasser
                    setze(wahl('wiese_mittel'), px, py)
                elif frei_umgebung(cx, cy, 0) and frei_umgebung(cx, cy, 1, 'gs') and r < 0.11:   # nicht ans Wasser
                    setze(wahl('wiese_klein'), px, py, ebene=0)
            elif kl == 's' and ch in 'Ss' and frei_umgebung(cx, cy, 0, 's') and r < 0.03:
                setze(wahl('strand'), px, py, ebene=0)
            elif kl in 'mw' and ch in 'hD':
                nahe_strand = any(k(cx + dx, cy + dy) == 's' for dx in range(-4, 5) for dy in range(-4, 5))
                if nahe_strand and frei_umgebung(cx, cy, 1, 'mw') and r < 0.035:
                    setze(wahl('meer'), px, py, ebene=0)
            elif kl == 'w' and ch == 'W' and cy > 50 and frei_umgebung(cx, cy, 1, 'w') and r < 0.07:
                setze(wahl('teich'), px, py, ebene=0)
            elif kl == 's' and ch == 'p' and any(k(cx + dx, cy + dy) == 'w' for dx in (-1, 0, 1) for dy in (-1, 0, 1)) \
                    and r < 0.12:
                setze(wahl('ufer'), px, py)

    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte gesetzt')

    # --- Schmetterlinge: ueber Wiesenstellen mit Blumen, mit Abstand zueinander
    farben = ['gelb', 'weiss', 'blau', 'rosa']
    kandidaten = [o for o in objekte if o['datei'][:-4] in BLUMEN]
    rnd.shuffle(kandidaten)
    falter = []
    for o in kandidaten:
        cx, cy = o['x'] + 8, o['y'] - 6
        if all(abs(cx - f['x']) + abs(cy - f['y']) > 120 for f in falter):
            falter.append({'x': cx, 'y': cy, 'rx': rnd.randint(8, 18), 'ry': rnd.randint(4, 9),
                           'phase': rnd.random(), 'richtung': rnd.choice((1, -1)), 'farbe': rnd.choice(farben)})
        if len(falter) >= 18:
            break
    json.dump(falter, open(os.path.join(OBJ, 'schmetterlinge.json'), 'w'), indent=0)
    print(len(falter), 'Schmetterlinge')


if __name__ == '__main__':
    main()
