"""Objekte fuer Karte 15 (Apocalymon's Realm) - am 16x16-Raster, nach den Regeln aus CLAUDE.md.

  python3 tools/karte15_bauen.py   (einmal ohne Objekte -> pixelhoehe.npy, leere.npy)
  python3 tools/karte15_objekte.py && python3 tools/karte15_bauen.py

Wiederverwendet (Regel 3): Leere-Objekte und Kleinkram der Karte 14 (Obelisken mit Auge, schwarze Kristalle,
Kettenpfahl, Datenwuerfel, Eierschalen, Orb-Altar, Geroell) - kopiert nach assets/objekte/karte15/.
Neu (PixelLab k15_inseln): schwebende Brocken verlorener Welten (Wiese, Wueste, Eis, Maschinenschrott, Spielzeug,
Meer, Moorwald, Gipfelteppich, Asteroid, Geroell, Kristall, Saeule, Datenwuerfel, Ketten, Ranke, Eierschale).
Die Plattform ist spiegelsymmetrisch zur Steg-Achse (x = 320 px); Kleinkram sparsam und unregelmaessig.
"""
import json, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
from karte04_objekte import saeubern

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte15')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte15')
K14 = os.path.join(ROOT, 'assets', 'objekte', 'karte14')
T = 16
ACHSE = 20 * T

# Plattform: (Quelle, Mitte x in px (links der Achse, wird gespiegelt), Fuss-Kachelreihe, Animation)
PAARE = [
    ('leere/05', ACHSE - 96, 14, 'auge'),           # Obelisken mit Auge, schraeg vor und hinter dem Riss
    ('leere/05', ACHSE - 96, 26, 'auge'),
    ('leere/11', ACHSE - 136, 20, None),            # schwarze Kristallgruppen an der West-/Ostseite
    ('leere/13', ACHSE - 72, 10, None),             # Kettenpfaehle beiderseits des Orb-Altars             # Kettenpfaehle an der Stegmuendung
]
EINZELN = [
    ('leere/07', ACHSE, 10, 'glimmen'),             # Orb-Altar im Norden auf der Achse
]
import math
POLAR = [   # Kleinkram (nicht gespiegelt, unregelmaessig): Quelle, Winkel (0 = Ost, 90 = Sued), Radius in px
    ('klein/55', 200, 150), ('klein/00', 250, 158), ('leere/12', 300, 150), ('klein/01', 332, 122),
    ('leere/04', 148, 122), ('klein/08', 38, 138), ('leere/02', 284, 108), ('klein/11', 116, 150),
    ('klein/30', 6, 150), ('klein/63', 176, 104),
]
KLEIN = [(n, (int((320 + math.cos(math.radians(w)) * r) // T) * T + 8), int((304 + math.sin(math.radians(w)) * r) // T))
         for n, w, r in POLAR]
# Kleinkram an den Sockelecken (Einbettung): klein/01 Kiesel, klein/08 Kristall
EINBETTEN = {'leere/05': ('klein/01', 'r'), 'leere/11': ('klein/08', 'l')}
# Leere: schwebende Inseln (Quelle, x-Mitte, Fuss-Kachelreihe) - verstreut, keine Reihen
INSELN = [
    ('inseln/00', 3 * T + 8, 3), ('inseln/07', 33 * T, 2), ('inseln/03', 37 * T + 8, 9), ('inseln/02', 2 * T + 8, 12),
    ('inseln/05', 37 * T, 21), ('inseln/04', 3 * T + 8, 25), ('inseln/06', 36 * T + 8, 33), ('inseln/01', 5 * T + 8, 37),
('inseln/13', 10 * T + 8, 38), 
]
INSEL_OBJEKTE = False           # Nutzerwunsch: keine Objekte auf der Plattform
ANIM_INSEL = {'inseln/10': 'schweben', 'inseln/12': 'schweben'}


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    Hp, Wp = lvl.shape
    leer = np.unpackbits(np.load(os.path.join(KARTE, 'leere.npy')))[:Hp * Wp].reshape(Hp, Wp).astype(bool)
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    for gr in ('leere', 'klein'):                                # Wiederverwendung: Karte-14-Sprites kopieren
        os.makedirs(os.path.join(OBJ, gr), exist_ok=True)
    cache, alpha = {}, {}
    pixel = np.zeros((Hp, Wp), bool)
    objekte = []
    land = (lvl == 2)
    # Felder, die frei bleiben: Steg (Weg zum Teleporter), Riss mit 1 Kachel Abstand, Achse vom Steg zum Riss
    gesperrt = np.zeros((Hp, Wp), bool)
    gesperrt[24 * T:, 17 * T:23 * T] = True
    yy, xx = np.mgrid[0:Hp, 0:Wp]
    gesperrt |= (np.abs(xx + 0.5 - ACHSE) <= 80) & (np.abs(yy + 0.5 - 304) <= 80)

    def sprite(name, spiegeln=False, rand=0):
        key = (name, spiegeln)
        if key not in cache:
            q = os.path.join(OBJ, name + '.png')
            if not os.path.exists(q):
                shutil.copy(os.path.join(K14, name + '.png'), q)
            sp = saeubern(Image.open(q).convert('RGBA'))
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            if rand:                                             # Luft oben/unten fuers Schweben
                neu = Image.new('RGBA', (sp.width, sp.height + 2 * rand))
                neu.paste(sp, (0, rand))
                sp = neu
            datei = 'sauber/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
            sp.save(os.path.join(OBJ, datei))
            a = np.array(sp.getchannel('A')) >= 128
            zu = int(np.nonzero(a.any(axis=1))[0].max())
            xs = np.nonzero(a.any(axis=0))[0]
            cache[key] = (datei, zu, (xs.min() + xs.max() + 1) / 2.0)
            alpha[datei] = a
        return cache[key]

    def passt(datei, x, y, maske, abstand=2):
        a = alpha[datei]
        h_, w_ = a.shape
        if x < 0 or y < 0 or x + w_ > Wp or y + h_ > Hp:
            return False
        sub = a
        if not maske[y:y + h_, x:x + w_][sub].all():
            return False
        fuss = a.copy(); fuss[:max(0, h_ - 6)] = False                # Fuss (unterste Reihen) nicht im Sperrfeld
        if gesperrt[y:y + h_, x:x + w_][fuss].any() and maske is not frei_leer_ref[0]:
            return False
        return not (pixel[y:y + h_, x:x + w_] & sub).any()

    def belegen(datei, x, y, r=5):
        a = np.array(Image.fromarray((alpha[datei] * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(r))) > 0
        h_, w_ = a.shape
        pixel[y:y + h_, x:x + w_] |= a[:h_, :w_]

    def setzen(name, mitte, reihe, anim=None, spiegeln=False, maske=None, symm=None, extra=None, pruefen=True):
        rand = 3 if name.startswith('inseln/') else 0
        datei, zu, m = sprite(name, spiegeln, rand)
        x = int(round(mitte - m))
        y = (reihe + 1) * T - 1 - zu
        if pruefen and not passt(datei, x, y, maske):
            print('  passt nicht:', name, mitte, reihe)
            return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': zu, 'kachel': [int(mitte // T), reihe], 'ebene': 2}
        if anim:
            o['anim'] = anim
        if symm:
            o['symm'] = symm
        if extra:
            o.update(extra)
        objekte.append(o)
        belegen(datei, x, y)
        return o

    # Plattform: fuer Objekte gilt - ganze Figur ueber der Insel (Boden oder Randring), Fuss nicht im Sperrfeld
    platz = land
    frei_leer_ref = [None]
    for i, (name, mx, reihe, anim) in enumerate(PAARE if INSEL_OBJEKTE else []):          # grosse Objekte zuerst, exakt gespiegelt
        o1 = setzen(name, mx, reihe, anim, False, platz, 'p%d' % i)
        o2 = setzen(name, 2 * ACHSE - mx, reihe, anim, True, platz, 'p%d' % i)
        for o, seite in ((o1, 1), (o2, -1)):
            if o and name in EINBETTEN:                          # Sockelecke: kleiner Begleiter
                kl, s_ = EINBETTEN[name]
                w_ = alpha[o['datei']].shape[1]
                ecke = o['x'] + (w_ if (s_ == 'r') == (seite == 1) else 0)
                setzen(kl, ecke + (4 if (s_ == 'r') == (seite == 1) else -4), reihe, None, seite == -1, platz, pruefen=False)
    for name, mx, reihe, anim in (EINZELN if INSEL_OBJEKTE else []):
        setzen(name, mx, reihe, anim, False, land)
    for (name, w, r), (_, mx, reihe) in (zip(POLAR, KLEIN) if INSEL_OBJEKTE else []):
        anim = 'glimmen' if name in ('klein/55', 'klein/08', 'leere/02', 'leere/04') else None
        ok = None
        for dw, dr in ((0, 0), (8, 0), (-8, 0), (0, 16), (0, -16), (14, 12), (-14, 12), (14, -12), (-14, -12)):
            w_, r_ = math.radians(w + dw), r + dr                # Ausweichen in der Naehe, falls belegt
            mx_ = int((320 + math.cos(w_) * r_) // T) * T + 8
            ry_ = int((304 + math.sin(w_) * r_) // T)
            datei, zu, m = sprite(name)
            if passt(datei, int(round(mx_ - m)), (ry_ + 1) * T - 1 - zu, platz):
                ok = setzen(name, mx_, ry_, anim, False, platz)
                break
        if not ok:
            print('  kein Platz:', name)
    # Leere: Inseln schweben frei, mindestens 1 Kachel Abstand zu Insel, Bauch und Steg
    frei_leer_ref[0] = frei_leer = np.array(Image.fromarray((~leer * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(33))) == 0
    for name, mx, reihe in INSELN:
        setzen(name, mx, reihe, ANIM_INSEL.get(name, 'schweben'), False, frei_leer,
               extra={'schwebt': True, 'kein_schatten': True, 'keine_verdeckung': True})
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 15: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
