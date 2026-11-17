"""Objekte fuer Karte 54 - D-Reaper Kernel (A03 Nr. 21).

  python3 tools/karte54_bauen.py   (einmal -> pixelhoehe.npy, wand.npy)
  python3 tools/karte54_objekte.py && python3 tools/karte54_bauen.py

Nach der Vorlage (PixelLab k54_kern, k54_klein, neu k54_kern_gross): Waechter-Mechs auf den Gewebebahnen, Stahltraeger,
Gasflaschen, gelbe Kaefiglampen, alte Terminals und Stasekapseln an der Suedseite, Bodengitter, Kabel, Schrauben.
Neu (Kernel): das pulsierende Herz des D-Reaper exakt auf der Achse der inneren Kammer, gespiegelt zwei Fleischsaeulen,
Brutnester und befallene Terminals; Waechter-Wesen (Karte 52) in den Gaengen. Lampen und Herz leuchten (animiert).
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte54')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte54')
T = 16
# name -> (Quelle, Skalierung)
D = {'mech': ('karte54/kern/00.png', 0.75), 'terminal': ('karte54/kern/01.png', 0.55), 'lampe': ('karte54/kern/02.png', 0.6),
     'kapsel': ('karte54/kern/03.png', 0.6), 'flasche': ('karte54/kern/04.png', 0.5), 'rack': ('karte54/kern/06.png', 0.6),
     'rohr': ('karte54/kern/07.png', 0.6), 'konsole': ('karte54/kern/09.png', 0.6),
     'herz': ('karte54/kern_gross/00.png', 0.85), 'saeule': ('karte54/kern_gross/01.png', 0.6),
     'nest': ('karte54/kern_gross/02.png', 0.55), 'befallen': ('karte54/kern_gross/03.png', 0.5),
     'waechter': ('karte52/reaper/02.png', 0.6), 'ranke': ('karte52/reaper/00.png', 0.55),
     'kabel': ('karte54/klein/00.png', 0.75), 'gitter': ('karte54/klein/01.png', 0.75), 'bolzen': ('karte54/klein/02.png', 0.6),
     'pfuetze': ('karte54/klein/03.png', 0.7)}
FLACH = {'kabel', 'gitter', 'bolzen', 'pfuetze', 'traeger', 'rohr'}


def main():
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    wand = np.unpackbits(np.load(os.path.join(KARTE, 'wand.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    wasser = np.unpackbits(np.load(os.path.join(KARTE, 'wasser.npy')))[:lvl.size].reshape(lvl.shape).astype(bool)
    os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
    sperr = [(t['x'] * T - 2 * T, t['y'] * T - 3 * T, (t['x'] + t['b'] + 2) * T, (t['y'] + t['h']) * T)
             for t in lay['teleporter']]
    ix0, iy0, ix1, iy1 = lay['innen']
    t0, t1 = lay['tor']
    sperr.append((t0 * T, (iy1 - 1) * T, (t1 + 1) * T, (iy1 + 2) * T))   # Tor und Austritt frei
    ax0, ay0, ax1, ay1 = lay['aussen']
    sperr.append((ax0 * T, (ay1 - 1) * T, (ax0 + 3) * T, (ay1 + 2) * T))  # Zugang zum Aussenring frei
    objekte, rects = [], []
    rnd = random.Random(54)

    def schnitt(a, b, d):
        return not (a[2] + d < b[0] or b[2] + d < a[0] or a[3] + d < b[1] or b[3] + d < a[1])

    def setze(name, cx, fy, opt=None, spiegeln=False, gap=2, pruefen=True, belag='gf', x_fest=None):
        opt = dict(opt or {})
        q, f = D[name]
        sp = Image.open(os.path.join(ROOT, 'assets', 'objekte', q)).convert('RGBA')
        sp = sp.crop(sp.getbbox())
        if f != 1:
            sp = sp.resize((max(1, round(sp.width * f)), max(1, round(sp.height * f))), Image.NEAREST)
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        datei = 'varianten/%s%s.png' % (name, '_m' if spiegeln else '')
        sp.save(os.path.join(OBJ, datei))
        bb = sp.getbbox()
        liegend = name in FLACH
        if not liegend:
            fy = int(fy) // T * T + T - 1                            # Regel 1b: Fuss buendig auf der Kachelunterkante
        x = int(round(cx - (bb[0] + bb[2]) / 2.0)) if x_fest is None else x_fest
        y = int(fy - (bb[3] - 1))
        r = (x + bb[0], y + bb[1], x + bb[2] - 1, y + bb[3] - 1)
        if r[0] < 2 or r[1] < 2 or r[2] >= cols * T - 2 or r[3] >= rows * T - 2:
            return None
        if pruefen:
            if any(schnitt(r, tuple(rr[:4]), gap) for rr in rects):
                return None
            if any(schnitt(r, s_, 0) for s_ in sperr):
                return None
            y_ab = r[1] if liegend else max(r[1], r[3] - 2 * T + 1)
            if (lvl[y_ab:r[3] + 4, max(0, r[0] - 3):r[2] + 4] != 1).any():
                return None
            if wand[max(0, r[1] - 2):r[3] + 4, r[0] - 2:r[2] + 3].any() or wasser[y_ab:r[3] + 5, r[0] - 3:r[2] + 4].any():
                return None
            kl_ = {cls[yy][xx] for yy in range(y_ab // T, r[3] // T + 1) for xx in range(r[0] // T, r[2] // T + 1)}
            if not kl_ <= set(belag):
                return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': bb[3] - 1, 'kachel': [int(cx) // T, int(fy) // T],
             'ebene': 0 if liegend else 1, 'ohne_wall': True}
        if liegend:
            o['liegend'] = True
            if name in ('kabel', 'gitter', 'bolzen', 'pfuetze'):
                o['schattenlos'] = True
        else:
            o['nur_kontakt'] = True
        o.update(opt)
        objekte.append(o)
        rects.append(list(r))
        return o

    def suche(name, cx, fy, opt=None, spiegeln=False, r=3, schritt=T, belag='gf'):
        for d in range(r + 1):
            for dy in range(-d, d + 1):
                for dx in range(-d, d + 1):
                    if max(abs(dx), abs(dy)) == d:
                        o = setze(name, cx + dx * schritt, fy + dy * schritt, opt, spiegeln, belag=belag)
                        if o:
                            return o
        print('  nicht gesetzt:', name, int(cx) // T, int(fy) // T)
        return None

    def paar(name, achse2, ab, fy, opt=None, dfy=(0, -T, T)):
        """Paar exakt gespiegelt zur Pixelachse achse2 (Kachelkante): rechts x_r = 2*achse2 - x_l - w."""
        w_ = D[name]
        sp = Image.open(os.path.join(ROOT, 'assets', 'objekte', w_[0])).convert('RGBA')
        sp = sp.crop(sp.getbbox())
        breite = max(1, round(sp.width * w_[1]))
        for dy_ in dfy:
            for d_ in (0, 8, -8, 16, -16, 24, -24, 32):
                xl = int(round(achse2 - (ab + d_) - breite / 2.0))
                xr = int(2 * achse2 - xl - breite)
                n0 = len(objekte)
                ol = setze(name, 0, fy + dy_, opt, False, x_fest=xl)
                orr = setze(name, 0, fy + dy_, opt, True, x_fest=xr) if ol else None
                if ol and orr:
                    return True
                del objekte[n0:]; del rects[n0:]
        print('  Paar nicht gesetzt:', name)
        return False

    # Herz des Kernels exakt auf der Achse der inneren Kammer (aus dem Ring berechnet), Paare gespiegelt
    achse = (ix0 + ix1 + 1) * T / 2.0
    my = (iy0 + iy1 + 1) // 2
    hs = Image.open(os.path.join(ROOT, 'assets', 'objekte', D['herz'][0])).convert('RGBA')
    hs = hs.crop(hs.getbbox()); hs = hs.resize((round(hs.width * D['herz'][1]), round(hs.height * D['herz'][1])), Image.NEAREST)
    ha = np.array(hs).astype(int)
    rot = (ha[..., 3] > 0) & (ha[..., 0] > 120) & (ha[..., 0] > ha[..., 1] + 60)          # nur die rote Kugel pulsiert
    ys_, xs_ = np.nonzero(rot)
    herz = setze('herz', achse, (my + 1) * T + 15, {'anim': 'lampe', 'lampe_box': [int(xs_.min()), int(ys_.min()),
                 int(xs_.max()) + 1, int(ys_.max()) + 1], 'licht_farbe': (255, 60, 90)}, pruefen=False)
    paar('saeule', achse, 6 * T, (my + 1) * T + 15, dfy=(0,))
    paar('nest', achse, 6 * T, (iy1 - 2) * T + 15, dfy=(0, -T))
    # Vorlage: Mechs auf den Gewebebahnen, Traeger, Flaschen, Lampen, Terminals, Kapseln
    paar('lampe', achse, 104, 30 * T + 15, {'anim': 'lampe'})          # Suedseite: Paare gespiegelt zur Kammerachse
    paar('terminal', achse, 168, 28 * T + 15, {'anim': 'maschine', 'leds': True})
    paar('kapsel', achse, 168, 31 * T + 15)
    for (n, px, py, sp_) in [('mech', 110, 180, False), ('mech', 656, 190, True), ('mech', 672, 495, True),
                             ('rohr', 112, 96, False), ('rohr', 656, 112, True), ('rohr', 656, 448, False),
                             ('flasche', 72, 80, False), ('flasche', 664, 80, True), ('flasche', 704, 392, False),
                             ('lampe', 72, 300, False), ('lampe', 700, 330, True)]:
        o = suche(n, px, py, {'anim': 'lampe'} if n == 'lampe' else {}, sp_, r=3, schritt=8)
    for (n, px, py, sp_) in [('gitter', 380, 490, False), ('gitter', 440, 470, False), ('kabel', 50, 200, False),
                             ('kabel', 712, 250, True), ('kabel', 160, 300, False), ('bolzen', 190, 330, False),
                             ('bolzen', 330, 445, True), ('bolzen', 640, 230, False), ('pfuetze', 520, 380, False),
                             ('pfuetze', 140, 520, True)]:
        suche(n, px, py, {}, sp_, r=3, schritt=8)
    # Kernel: befallene Technik, Ranken, Waechter-Wesen in den Gaengen
    for (n, px, py, sp_) in [('befallen', 60, 470, False), ('flasche', 720, 440, True), ('konsole', 392, 525, False),
                             ('ranke', 208, 120, False), ('ranke', 576, 280, True), ('ranke', 500, 410, False),
                             ('waechter', 200, 200, False), ('waechter', 570, 100, True), ('waechter', 400, 340, False)]:
        suche(n, px, py, {'anim': 'maschine', 'leds': True} if n in ('rack', 'konsole', 'befallen') else {}, sp_, r=3,
              schritt=8)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte')


if __name__ == '__main__':
    main()
