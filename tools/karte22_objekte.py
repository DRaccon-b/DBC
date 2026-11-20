"""Objekte fuer Karte 22 (Digicasino) - am 16x16-Raster, nach den Regeln aus CLAUDE.md.

  python3 tools/karte22_bauen.py   (einmal -> pixelhoehe.npy)
  python3 tools/karte22_objekte.py && python3 tools/karte22_bauen.py

Alle Objekte neu mit dem PixelLab Objekt-Creator (k22_casino, k22_gross) im Netz-Stil von Karte 16.
Paare stehen exakt spiegelsymmetrisch zur Mittelachse des Casinos (x = 416 px; gespiegelt: x' = 832 - x).
"""
import json, os, sys
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
    H = r.shape[0]

    def stueck(i):
        # Nutzer: Rueckwand abwechslungsreich - PixelLab-Stuecke (k22_regal), unten buendig; fehlende Hoehe oben mit dem
        # Rahmen des Flaschenregals aufgefuellt, damit die Oberkante durchlaeuft
        v = np.array(Image.open(os.path.join(OBJ, 'regal', '%02d.png' % i)).convert('RGBA'))
        v = v[-H:]
        out = np.zeros((H, v.shape[1], 4), np.uint8)
        fuell = np.concatenate([rm] * (v.shape[1] // rm.shape[1] + 1), axis=1)[:, :v.shape[1]]
        out[:H - v.shape[0]] = fuell[:H - v.shape[0]]
        out[H - v.shape[0]:] = v
        leer = out[..., 3] == 0                                        # Luecken (runde Ecken) mit Regalgrund fuellen
        out[leer] = fuell[leer]
        return out

    breiten = []
    for seite, var in (('links', VARIANTEN[0::2]), ('rechts', VARIANTEN[1::2])):
        teile, i_ = [rl], 0
        breite = 6
        while True:
            t_ = rm if len(teile) % 2 == 1 else stueck(var[i_ % len(var)])
            if len(teile) % 2 == 0:
                i_ += 1
            if breite + t_.shape[1] > REGAL_BREITE:
                break
            teile.append(t_); breite += t_.shape[1]
        rest_ = REGAL_BREITE - breite                                  # auf volle Breite: Flaschenregal-Stueck anstueckeln
        while rest_ > 0:
            teile.append(rm[:, :min(rest_, rm.shape[1])]); rest_ -= rm.shape[1]
        regal = np.concatenate(teile + [rr], axis=1)
        Image.fromarray(regal).save(os.path.join(d, 'regal_%s.png' % seite))
        breiten.append(regal.shape[1])
    return tresen.shape[1], breiten


BAR_BREITE, REGAL_BREITE = 320, 384                                   # je Haelfte (px)
VARIANTEN = [0, 1, 3, 4, 5, 6, 7, 10, 15, 8, 13, 11]
TRESEN_DEKO = ([(0, 34), (3, 82), (2, 140), (4, 196), (7, 262)],          # (k22_tresen-Nr., x auf dem Tresen)
               [(1, 40), (5, 96), (8, 150), (6, 204), (9, 240), (14, 290)])                  # k22_regal: verschiedene Wandstuecke, keine doppelt
TRESEN_W, (REGAL_WL, REGAL_WR) = bar_bauen()


def paar(name, dx, reihe, anim=None, spiegeln_rechts=False):
    """Links/rechts gespiegelt zur Achse: Mitte bei MITTE -/+ dx."""
    return [(name, MITTE - dx, reihe, anim, False), (name, MITTE + dx, reihe, anim, spiegeln_rechts)]


# (Quelle, Mitte x in px, Fussreihe, Animation, gespiegelt)
OBJEKTE = (
    # Nutzer: hintere Wand = Bar. Regal an der Wand, eine Reihe Platz fuer den Barkeeper, davor der Tresen, Hocker
    [('theke_gebaut/regal_links', 528 - REGAL_WL / 2.0, 5, None, False),
     ('theke_gebaut/regal_rechts', 592 + REGAL_WR / 2.0, 5, None, False)]
    + [('theke_gebaut/tresen_links', 512 - TRESEN_W / 2.0, 8, None, False),
       ('theke_gebaut/tresen_rechts', 608 + TRESEN_W / 2.0, 8, None, False)]
    # Automatenreihen (je 4 Automaten untereinander)
    + sum((paar(AUTOMAT, 320, r, 'automat') for r in (14, 18, 22, 26)), [])    # Nutzer: Anzahl bleibt, mehr Platz ringsum
    # Spieltische: links Roulette/Karten, rechts Blackjack/Craps (gleiche Plaetze gespiegelt)
    + [(ROULETTE, MITTE - 160, 17, None, False), (BLACKJACK, MITTE + 160, 17, None, False),
       (KARTEN, MITTE - 160, 23, None, False), (CRAPS, MITTE + 160, 23, None, False)]
    # Samtkordeln am Teppich, Neonlaternen am Eingang, Geldautomaten
    + paar(KORDEL, 46, 14, None, True) + paar(KORDEL, 46, 24, None, True)
    + paar(LAMPE, 56, 32, 'lampe')
    + paar(ATM, 200, 30, 'lampe')
    # Jackpot-Inseln: je ein grosser Jackpot-Automat
    + paar(JACKPOT, 504, 18, 'automat')
    # Ankunft: zwei Datenkristalle neben den Pfeilen
    + paar(KRISTALL, 48, 37, 'lampe')
    # Nutzer: Bar oben links/rechts - Tresen, drei Hocker davor, Cocktailtisch und Jukebox (PixelLab k22_bar/k22_bar48)
    + sum((paar(HOCKER, MITTE - x_, 10) for x_ in (216, 264, 312, 360, 408, 456)), [])
    + paar(JUKEBOX, MITTE - 168, 11, 'lampe', True)
    # Nutzer: Weinfaesser an der Bar, Chip-Wagen neben den Spieltischen
    + paar('mittel/00', MITTE - 166, 7) + paar('mittel/01', MITTE - 304, 19, None, True)   # Cocktailtische entfallen (stiessen an Kordeln/Hocker)
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
        x = int(round(mitte - (xs.min() + xs.max() + 1) / 2.0))
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
