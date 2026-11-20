"""Objekte fuer Karte 22 (Digicasino) - am 16x16-Raster, nach den Regeln aus CLAUDE.md.

  python3 tools/karte22_bauen.py   (einmal -> pixelhoehe.npy)
  python3 tools/karte22_objekte.py && python3 tools/karte22_bauen.py

Alle Objekte neu mit dem PixelLab Objekt-Creator (k22_casino, k22_gross) im Netz-Stil von Karte 16.
Paare stehen exakt spiegelsymmetrisch zur Mittelachse des Casinos (x = 416 px; gespiegelt: x' = 832 - x).
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
from karte04_objekte import saeubern

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte22')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte22')
T = 16
MITTE = 560                                                       # Achse 34.5 (70 Kacheln Breite)
AUTOMAT, ROULETTE, KARTEN, CRAPS, BLACKJACK = 'casino/00', 'casino/01', 'casino/02', 'casino/06', 'casino/07'
KORDEL, ATM, JACKPOT, THEKE, KRISTALL, LAMPE = 'casino/04', 'casino/12', 'gross/00', 'gross/01', 'gross/02', 'gross/10'
BAR, HOCKER, COCKTAIL, JUKEBOX = 'bar/00', 'bar48/00', 'bar48/01', 'bar48/10'


def bar_bauen():
    """Nutzer: die ganze hintere Wand ist eine Bar. Tresen und Flaschenregal aus den PixelLab-Stuecken (k22_theke)
    zusammengesetzt: Endstueck links + Mittelstreifen (eine Kachel breit, nahtlos) wiederholt + Endstueck rechts.
    Je eine Haelfte links und rechts der VIP-Tuer (Teppich bleibt frei). Rueckgabe: (Tresen-Breite, Regal-Breite)."""
    d = os.path.join(OBJ, 'theke_gebaut')
    os.makedirs(d, exist_ok=True)
    t = np.array(Image.open(os.path.join(OBJ, 'theke', '00.png')).convert('RGBA'))
    links, streifen, rechts = t[:, :26], t[:, 26:42], t[:, 42:]
    n = (BAR_BREITE - links.shape[1] - rechts.shape[1]) // 16
    tresen = np.concatenate([links] + [streifen] * n + [rechts], axis=1)
    # Nutzer: Glaeser, Chips usw. auf der Tresenplatte (PixelLab k22_tresen, 16 px Zielgroesse), je Haelfte andere
    for seite, deko in (('links', TRESEN_DEKO[0]), ('rechts', TRESEN_DEKO[1])):
        t2 = np.zeros((tresen.shape[0] + 12, tresen.shape[1], 4), np.uint8)
        t2[12:] = tresen
        bild = Image.fromarray(t2)
        for i_, (nr_, x_) in enumerate(deko):
            g = Image.open(os.path.join(OBJ, 'tresen', '%02d.png' % nr_)).convert('RGBA')
            g = g.crop(g.getbbox())
            if seite == 'rechts':                                     # rechte Haelfte wird gespiegelt gesetzt
                x_ = tresen.shape[1] - x_
            bild.alpha_composite(g, (int(x_ - g.width // 2), 12 + 9 - g.height + 1))
        if seite == 'rechts':
            bild = bild.transpose(Image.FLIP_LEFT_RIGHT)
        bild.save(os.path.join(d, 'tresen_%s.png' % seite))
    r = np.array(Image.open(os.path.join(OBJ, 'theke', '03.png')).convert('RGBA'))
    rl, rm, rr = r[:, :3], r[:, 3:37], r[:, 37:]
    # Nutzer: Einsaetze wirkten "draufgeklatscht" -> eine durchgehende Schrankwand: oben ein gemeinsames Kranzgesims
    # (Regal-Zeilen 0-6), unten ein gemeinsamer Schubladensockel (Zeilen 30-41); dazwischen gleich hohe Faecher, je
    # von denselben Rahmenleisten getrennt. Flaschenfaecher mit drei Boeden, Sonderfaecher (k22_regal) als Nischen.
    OBEN, UNTEN, FACH = rm[:7], rm[30:], 39
    H = OBEN.shape[0] + FACH + UNTEN.shape[0]
    PANEL = np.array((34, 20, 46, 255), np.uint8)
    flaschen = np.concatenate([rm[7:30], rm[7:23]], axis=0)            # drei Flaschenboeden (23 + 16 = 39 Zeilen)

    def kachelbreit(streifen, w):
        return np.concatenate([streifen] * (w // streifen.shape[1] + 1), axis=1)[:, :w]

    def leiste():                                                     # Rahmenleiste zwischen den Faechern (3 px)
        return np.concatenate([rl[7:30], rl[7:23]], axis=0)

    def nische(i):
        v = np.array(Image.open(os.path.join(OBJ, 'regal', '%02d.png' % i)).convert('RGBA'))
        v = v[2:-2, 2:-2]                                              # eigener Aussenrahmen weg (sitzt jetzt im Schrank)
        v = v[-(FACH - 1):]
        v[v[..., 3] > 0, 3] = 255
        out = np.tile(PANEL, (FACH, v.shape[1] + 4, 1))
        out[FACH - v.shape[0]:, 2:2 + v.shape[1]][v[..., 3] > 0] = v[v[..., 3] > 0]
        return out

    breiten = []
    for seite, var in (('links', VARIANTEN[0::2]), ('rechts', VARIANTEN[1::2])):
        mitte, breite, i_ = [leiste()], 3, 0
        fl = kachelbreit(flaschen, rm.shape[1])
        while True:
            n_ = nische(var[i_ % len(var)])
            if breite + fl.shape[1] + 3 + n_.shape[1] + 3 + fl.shape[1] + 3 > REGAL_BREITE:
                break
            mitte += [fl, leiste(), n_, leiste()]; breite += fl.shape[1] + n_.shape[1] + 6; i_ += 1
        mitte += [kachelbreit(flaschen, REGAL_BREITE - breite - 3), leiste()]
        band = np.concatenate(mitte, axis=1)
        W = band.shape[1]
        oben = np.concatenate([rl[:7], kachelbreit(OBEN, W - 6), rr[:7]], axis=1)
        unten = np.concatenate([rl[30:], kachelbreit(UNTEN, W - 6), rr[30:]], axis=1)
        regal = np.concatenate([oben, band, unten], axis=0)
        Image.fromarray(regal).save(os.path.join(d, 'regal_%s.png' % seite))
        breiten.append(regal.shape[1])
    return tresen.shape[1], breiten


BAR_BREITE, REGAL_BREITE = 320, 384                                   # je Haelfte (px)
VARIANTEN = [0, 1, 3, 4, 5, 6, 7, 10, 15, 13, 11]                    # 8 entfaellt (Textrest unter dem Monitor)
TRESEN_DEKO = ([(0, 34), (3, 82), (2, 140), (4, 196), (7, 262)],          # (k22_tresen-Nr., x auf dem Tresen)
               [(1, 40), (5, 96), (8, 150), (6, 204), (9, 240), (14, 290)])                  # k22_regal: verschiedene Wandstuecke, keine doppelt
TRESEN_W, (REGAL_WL, REGAL_WR) = bar_bauen()


def paar(name, dx, reihe, anim=None, spiegeln_rechts=False):
    """Links/rechts gespiegelt zur Achse: Mitte bei MITTE -/+ dx."""
    return [(name, MITTE - dx, reihe, anim, False), (name, MITTE + dx, reihe, anim, spiegeln_rechts)]


# (Quelle, Mitte x in px, Fussreihe, Animation, gespiegelt)
OBJEKTE = (
    # Nutzer: hintere Wand = Bar. Regal an der Wand, eine Reihe Platz fuer den Barkeeper, davor der Tresen, Hocker
    [('theke_gebaut/regal_links', 528 - REGAL_WL / 2.0, 6, 'automat22', False),
     ('theke_gebaut/regal_rechts', 592 + REGAL_WR / 2.0, 6, 'automat22', False)]
    + [('theke_gebaut/tresen_links', 512 - TRESEN_W / 2.0, 9, None, False),
       ('theke_gebaut/tresen_rechts', 608 + TRESEN_W / 2.0, 9, None, False)]
    # Automatenreihen (je 4 Automaten untereinander)
    + sum((paar(AUTOMAT, 320, r, 'automat22') for r in (14, 18, 22, 26)), [])    # Nutzer: Anzahl bleibt, mehr Platz ringsum
    # Spieltische: links Roulette/Karten, rechts Blackjack/Craps (gleiche Plaetze gespiegelt)
    + [(ROULETTE, MITTE - 160, 17, None, False), (BLACKJACK, MITTE + 160, 17, None, False),
       (KARTEN, MITTE - 160, 23, None, False), (CRAPS, MITTE + 160, 23, None, False)]
    # Samtkordeln am Teppich, Neonlaternen am Eingang, Geldautomaten
    + paar(KORDEL, 53, 14, None, True) + paar(KORDEL, 53, 24, None, True)   # Pruefung: Seilende neben dem Teppich
    + paar(LAMPE, 56, 32, 'lampe')
    + paar(ATM, 200, 30, 'automat22')
    # Jackpot-Inseln: je ein grosser Jackpot-Automat
    + paar(JACKPOT, 504, 18, 'automat22')
    # Ankunft: zwei Datenkristalle neben den Pfeilen
    + paar(KRISTALL, 48, 37, 'kristall')
    # Nutzer: Bar oben links/rechts - Tresen, drei Hocker davor, Cocktailtisch und Jukebox (PixelLab k22_bar/k22_bar48)
    + sum((paar(HOCKER, MITTE - x_, 11) for x_ in (216, 264, 312, 360, 408, 456)), [])
    + paar(JUKEBOX, MITTE - 168, 12, 'lampe', True)
    # Nutzer: Weinfaesser an der Bar, Chip-Wagen neben den Spieltischen
    + paar('mittel/00', MITTE - 166, 8) + paar('mittel/01', MITTE - 304, 19, None, True)   # Cocktailtische entfallen (stiessen an Kordeln/Hocker)
)


def main():
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    Hp, Wp = lvl.shape
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    objekte, belegt = [], np.zeros((Hp, Wp), bool)
    for name, mitte, reihe, anim, spiegeln in OBJEKTE:
        sp = saeubern(Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA'))
        if spiegeln:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        datei = 'sauber/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
        sp.save(os.path.join(OBJ, datei))
        a = np.array(sp.getchannel('A')) >= 128
        zu = int(np.nonzero(a.any(axis=1))[0].max())
        xs = np.nonzero(a.any(axis=0))[0]
        v_ = mitte - (xs.min() + xs.max() + 1) / 2.0                    # Paare pixelgenau gespiegelt (x.5 links ab-, rechts aufrunden)
        x = int(math.floor(v_)) if mitte < MITTE else int(math.ceil(v_))
        y = (reihe + 1) * T - 1 - zu
        h_, w_ = a.shape
        fuss = a.copy(); fuss[:max(0, zu + 1 - 6)] = False
        assert (lvl[y:y + h_, x:x + w_][fuss] == 2).all(), name + ': Fuss nicht auf der Plattform'
        if (belegt[y:y + h_, x:x + w_] & a).any():
            print('  WARNUNG ueberlappt:', name, mitte, reihe)
        g = np.zeros_like(belegt); g[y:y + h_, x:x + w_] = a
        belegt |= np.array(Image.fromarray((g * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': zu, 'kachel': [int(mitte // T), reihe], 'ebene': 2,
             'an_wand': True}
        if anim:
            o['anim'] = anim
        objekte.append(o)
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print('Karte 22: %d Objekte' % len(objekte))


if __name__ == '__main__':
    main()
