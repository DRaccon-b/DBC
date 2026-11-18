"""Objekte fuer Karte 55 (Hurricane Landing) -> assets/objekte/karte55/platzierung.json

  python3 tools/karte55_objekte.py && python3 tools/karte55_bauen.py

Wiederverwendet (Regel 3): Stadtgebaeude, Laternen, Taxi/Autos, Haltestelle, Bank, Tauben aus Karte 35/39;
neu mit PixelLab (Regel 3b): Ranchzaeune, Telegrafenmasten, Heuballen, Warnschild, Briefkasten, Beifuss, Felsen,
Praeriegras, Steppenlaeufer, Wildblumen (k55_land, k55_n32) sowie Hydrant/Briefkasten (k55_stadt).
Objekte stehen am 16er-Raster, waagerecht zentriert in ihrem Kachelblock, Fuss buendig auf der Kachelunterkante (1b).
Kampfraeume: die Mitte bleibt frei, Deko nur an den Raendern.
"""
import json, os, shutil
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'assets', 'objekte')
OBJ = os.path.join(SRC, 'karte55')
LAYOUT = os.path.join(ROOT, 'maps', 'karte55', 'layout.json')
T = 16


def sprite(quelle, name, spiegeln=False):
    """Sprite nach assets/objekte/karte55/varianten kopieren (optional gespiegelt), Dateiname zurueck."""
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
    ziel = 'varianten/%s%s.png' % (name, '_m' if spiegeln else '')
    im = Image.open(os.path.join(SRC, quelle)).convert('RGBA')
    bb = im.getbbox()
    im = im.crop(bb)
    if spiegeln:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    im.save(os.path.join(OBJ, ziel))
    return ziel


def setzen(liste, datei, tx, ty, breite=None, dx=0, **extra):
    """Objekt mit Fuss auf Kachelreihe ty (Unterkante), waagerecht zentriert im Block ab Spalte tx (Breite in
    Kacheln, sonst aus der Spritebreite)."""
    im = Image.open(os.path.join(OBJ, datei))
    w, h = im.size
    b = breite or max(1, -(-w // T))
    x = tx * T + (b * T - w) // 2 + dx
    y = (ty + 1) * T - h
    o = {'datei': datei, 'basis': 'k55/' + os.path.basename(datei)[:-4], 'x': int(x), 'y': int(y), 'fuss': h - 1,
         'kachel': [tx, ty], 'ebene': 2}
    o.update(extra)
    liste.append(o)
    return o


def new_york(L, x0, y0):
    """Raum links (x0, y0 = linke obere Raumecke). Reihen: 1-10 Gebaeude, 11-12 Gehweg, 13-17 Avenue,
    18-22 Gehweg mit Aufstellfeld (Spalten 1-6)."""
    G = dict(ebene=2, gebaeude=True, ohne_wall=True, nur_kontakt=True)
    fuss = y0 + 10
    a = sprite('karte35/varianten/schmal_a-00.png', 'ny-schmal_a')
    b = sprite('karte40/varianten/gross-beige.png', 'ny-beige')
    c = sprite('karte35/varianten/schmal_b-00.png', 'ny-schmal_b')
    setzen(L, a, x0 + 1, fuss, breite=6, **G)
    setzen(L, b, x0 + 7, fuss, breite=14, **G)
    setzen(L, c, x0 + 21, fuss, breite=6, **G)
    S = dict(ohne_wall=True, nur_kontakt=True)                    # Gehweg: kein Bodenwall, nur Kontaktschatten
    lat = sprite('karte35/varianten/k18s-18.png', 'ny-laterne')
    for tx in (3, 14, 24):                                        # Nordgehweg an der Bordsteinkante
        setzen(L, lat, x0 + tx, y0 + 12, anim='leuchten', licht=[4, 7], licht_box=[2, 5, 6, 10], licht_r=9, **S)
    for tx in (15, 25):                                           # Suedgehweg (Zebrastreifen-Austritt 10-12 frei)
        setzen(L, lat, x0 + tx, y0 + 18, anim='leuchten', licht=[4, 7], licht_box=[2, 5, 6, 10], licht_r=9, **S)
    taxi = sprite('karte39/varianten/k18a-04.png', 'ny-taxi')     # Front links -> obere Spur (Richtung Westen)
    setzen(L, taxi, x0 + 19, y0 + 14, breite=4, auto=True, fest_pos=True, **S)
    rot = sprite('karte39/varianten/k18a-02_m.png', 'ny-auto_rot')   # Front rechts -> untere Spur (Osten)
    setzen(L, rot, x0 + 3, y0 + 17, breite=4, auto=True, fest_pos=True, **S)
    hs = sprite('karte35/varianten/k18s-41.png', 'ny-haltestelle')
    setzen(L, hs, x0 + 18, y0 + 18, breite=2, **S)
    bank = sprite('karte39/varianten/k38-bank.png', 'ny-bank')
    setzen(L, bank, x0 + 21, y0 + 21, breite=2, **S)
    mull = sprite('karte35/varianten/k18s-12.png', 'ny-muell')
    setzen(L, mull, x0 + 23, y0 + 21, breite=2, **S)
    taube = sprite('karte39/varianten/k38-taube.png', 'ny-taube')
    taube_m = sprite('karte39/varianten/k38-taube.png', 'ny-taube', spiegeln=True)
    setzen(L, taube, x0 + 12, y0 + 21, liegend=True, **S)
    setzen(L, taube_m, x0 + 9, y0 + 12, liegend=True, **S)
    zeitung = sprite('karte39/varianten/k38-zeitung.png', 'ny-zeitung')
    setzen(L, zeitung, x0 + 8, y0 + 20, liegend=True, **S)
    S2 = dict(S)
    setzen(L, sprite('karte55/stadt/01.png', 'ny-briefkasten'), x0 + 6, y0 + 12, **S2)
    setzen(L, sprite('karte55/stadt/02.png', 'ny-zeitungsboxen'), x0 + 18, y0 + 12, breite=2, **S2)
    setzen(L, sprite('karte55/stadt/47.png', 'ny-hotdog'), x0 + 9, y0 + 22, breite=3, **S2)

def colorado(L, x0, y0):
    """Raum rechts: Praerie mit Landstrasse; Zaeune, Masten und Deko an den Raendern (Mitte = Kampfflaeche)."""
    if not os.path.exists(os.path.join(OBJ, 'auswahl.json')):
        return
    w = json.load(open(os.path.join(OBJ, 'auswahl.json')))       # Auswahl der PixelLab-Kandidaten
    for e in w.get('setzen', []):
        n = sprite('karte55/' + e['quelle'], e['name'], e.get('spiegeln', False))
        setzen(L, n, x0 + e['x'], y0 + e['y'], breite=e.get('b'), **e.get('extra', {}))
    streudeko(L, x0, y0)


def _rechteck(o):
    w, h = Image.open(os.path.join(OBJ, o['datei'])).size
    return o['x'], o['y'], o['x'] + w, o['y'] + h


def streudeko(L, x0, y0):
    """Kleinkram dezent (Regel): wenige Bueschel, Blumen, Kiesel, ein Schaedel - nur auf Praerie, nie am Aufstellfeld,
    nie in Reihen, 2 px Abstand zu allen Objekten, gleiches Motiv nie nah beieinander."""
    lay = json.load(open(LAYOUT))
    kl = lay['klassen']
    motive = [('n32/00.png', 'co-gras'), ('n32/13.png', 'co-gras_hoch'), ('n32/21.png', 'co-gras_rispe'),
              ('n32/02.png', 'co-blumen'), ('n32/01.png', 'co-steppenlaeufer'), ('n32/03.png', 'co-kiesel'),
              ('n32/08.png', 'co-schaedel'), ('n32/00.png', 'co-gras'), ('n32/02.png', 'co-blumen'),
              ('n32/13.png', 'co-gras_hoch'), ('n32/03.png', 'co-kiesel')]
    rs = np.random.RandomState(5555)
    kand = [(tx, ty) for ty in range(1, 23) for tx in range(1, 27)
            if kl[y0 + ty][x0 + tx] == 'q' and not (tx <= 8 and ty >= 16)
            and all(kl[y0 + ty + dy][x0 + tx + dx] == 'q' for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                    if 0 < ty + dy < 23 and 0 < tx + dx < 27)]
    rs.shuffle(kand)
    gesetzt = []
    for (q, name) in motive:
        for (tx, ty) in kand:
            if any(abs(tx - a) + abs(ty - b) < 4 for (a, b, _) in gesetzt):
                continue
            if any(n_ == name and abs(tx - a) + abs(ty - b) < 10 for (a, b, n_) in gesetzt):
                continue
            if any(b == ty and abs(tx - a) < 6 for (a, b, _) in gesetzt):       # keine Reihen
                continue
            datei = sprite('karte55/' + q, name, spiegeln=bool(rs.randint(2)))
            o = setzen([], datei, x0 + tx, y0 + ty, liegend=name in ('co-kiesel', 'co-schaedel'))
            r = _rechteck(o)
            if any(not (r[2] + 2 <= s_[0] or s_[2] + 2 <= r[0] or r[3] + 2 <= s_[1] or s_[3] + 2 <= r[1])
                   for s_ in map(_rechteck, L)):
                continue
            L.append(o)
            gesetzt.append((tx, ty, name))
            break


def guertel(L):
    """Dichter Baumguertel ringsum (Nutzer: wie Karte 35): NY-Seite Parkbaeume, Colorado-Seite Kiefern; Kronen bleiben
    ganz auf Guertelkacheln (nie ueber Gehweg, Fassaden oder Praerie der Raeume) und im Kartenbild; Luecken mit
    Bueschen schliessen (kein kahler Boden im Guertel)."""
    lay = json.load(open(LAYOUT))
    kl = np.array([list(r) for r in lay['klassen']])
    rows, cols = kl.shape
    rs = np.random.RandomState(5557)
    wald = {'h': ['karte35/varianten/k01-baum%02d.png' % i for i in (0, 1, 2, 4, 15)],
            'H': ['karte55/baum/%02d.png' % i for i in (0, 0, 0, 1, 1, 2, 2, 5)]}    # Praerie (Nutzer)
    busch = {'h': ['karte35/varianten/k01-baum%02d.png' % i for i in (12, 13, 14)],
             'H': ['karte55/baum/%02d.png' % i for i in (3, 4, 8, 13, 4, 8, 6)]}
    fremd = [_rechteck(o) for o in L]

    def versuch(quelle, tx, ty, art):
        n = sprite(quelle, 'wald-' + quelle.split('/')[-2].replace('varianten', '') + os.path.basename(quelle)[:-4].replace('k01-', ''),
                   spiegeln=bool(rs.randint(2)))
        o = setzen([], n, tx, ty, breite=1, anim='baum' if art == 'baum' else 'wehen')
        r = _rechteck(o)
        if r[0] < 0 or r[1] < 0 or r[2] > cols * T or r[3] > rows * T:
            return None
        if any(kl[y][x] not in 'hHLE' for y in range(r[1] // T, (r[3] - 1) // T + 1)
               for x in range(r[0] // T, (r[2] - 1) // T + 1)):
            return None
        if any(not (r[2] + 2 <= f[0] or f[2] + 2 <= r[0] or r[3] + 2 <= f[1] or f[3] + 2 <= r[1]) for f in fremd):
            return None
        L.append(o)
        return r

    deck = np.zeros((rows * T, cols * T), bool)
    n_b = n_s = 0
    for ty in range(rows):
        for tx in range(cols):
            if (kl[ty, tx] == 'h' and (tx + ty) % 2 == 0) or (kl[ty, tx] == 'H' and (tx + 2 * ty) % 3 == 0):
                r = versuch(wald[kl[ty, tx]][rs.randint(len(wald[kl[ty, tx]]))], tx, ty, 'baum')
                if r:
                    deck[r[1]:r[3], r[0]:r[2]] = True; n_b += 1
    for ty in range(rows):
        for tx in range(cols):
            if kl[ty, tx] in 'hH' and deck[ty * T:(ty + 1) * T, tx * T:(tx + 1) * T].mean() < 0.7:
                r = versuch(busch[kl[ty, tx]][rs.randint(len(busch[kl[ty, tx]]))], tx, ty, 'busch')
                if r:
                    deck[r[1]:r[3], r[0]:r[2]] = True; n_s += 1
    print('Baumguertel: %d Baeume, %d Buesche' % (n_b, n_s))


def main():
    lay = json.load(open(LAYOUT))
    (nx, ny), (cx, cy) = lay['raeume']
    L = []
    new_york(L, nx, ny)
    colorado(L, cx, cy)
    guertel(L)
    json.dump(L, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 55: %d Objekte' % len(L))


if __name__ == '__main__':
    main()
