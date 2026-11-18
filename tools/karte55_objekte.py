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
    for (quelle, tx, ty) in (('k55_stadt/00.png', 6, 12), ('k55_stadt/01.png', 20, 11)):
        if os.path.exists(os.path.join(SRC, 'karte55', quelle)):
            n = sprite('karte55/' + quelle, 'ny-' + quelle.replace('/', '_')[:-4])
            setzen(L, n, x0 + tx, y0 + ty, **S)


def colorado(L, x0, y0):
    """Raum rechts: Praerie mit Landstrasse; Zaeune, Masten und Deko an den Raendern (Mitte = Kampfflaeche)."""
    if not os.path.exists(os.path.join(OBJ, 'auswahl.json')):
        return
    w = json.load(open(os.path.join(OBJ, 'auswahl.json')))       # Auswahl der PixelLab-Kandidaten
    for e in w.get('setzen', []):
        n = sprite('karte55/' + e['quelle'], e['name'], e.get('spiegeln', False))
        setzen(L, n, x0 + e['x'], y0 + e['y'], breite=e.get('b'), **e.get('extra', {}))


def main():
    lay = json.load(open(LAYOUT))
    (nx, ny), (cx, cy) = lay['raeume']
    L = []
    new_york(L, nx, ny)
    colorado(L, cx, cy)
    json.dump(L, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 55: %d Objekte' % len(L))


if __name__ == '__main__':
    main()
