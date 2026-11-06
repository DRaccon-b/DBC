"""Objekte fuer Karte 10 (Toy Town) - am 16x16-Raster, nach den Regeln aus CLAUDE.md.

  python3 tools/karte10_bauen.py   (einmal ohne Objekte -> pixelhoehe.npy, wandflaeche.npy)
  python3 tools/karte10_objekte.py && python3 tools/regeln_v11.py karte10 && python3 tools/karte10_objekte.py symmetrie
  python3 tools/karte10_bauen.py

Neu (PixelLab, assets/objekte/karte10): haeuser, haeuser2, burg, bahnhof, spielplatz, baeume, klein.
Die Ecktuerme der Burg sind aus der Burgfront ausgeschnitten (gleicher Stil, kein Neu-Generieren noetig).
Grosse Objekte zuerst (Burg, Bahnhof, Haeuser, Uhrturm, Brunnen), dann Baeume mit Begleitern, dann Kleinkram.
Paare auf Plaetzen stehen spiegelsymmetrisch zur Achse ihres Bauwerks.
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
from karte04_objekte import saeubern
from karte09_objekte import raster_x, groesstes_teil, bewerten

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte10')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte10')
T = 16
ACHSE_BURG = 76 * T              # Burg, Torweg, Hofrahmen
ACHSE_BAHNHOF = 76 * T           # Bahnsteig x 69-82
ACHSE_BRUNNEN = 10 * T           # Brunnenplatz (Mitte x 10.0)
ACHSE_UHR = 54 * T               # Uhrenplatz (Mitte x 54.0)
WAND_FUSS = 37 * T + 15          # Unterkante der Wandflaeche der Burg-Nordmauer (Reihen 35-37)

LAMPE, BANK, BRIEF, HYDRANT, ZAUN = 'spielplatz/04', 'spielplatz/03', 'spielplatz/05', 'spielplatz/06', 'spielplatz/07'
SOLDAT = 'spielplatz/09'
BAEUME = ['baeume/00', 'baeume/01', 'baeume/02', 'klein/49', 'klein/48', 'baeume2/00', 'baeume2/01', 'baeume2/02']
STARR = {'baeume2/00', 'baeume2/01', 'baeume2/02'}     # Spielzeugbaeume aus Holz/Zucker: bewegen sich nicht im Wind
BUESCHE = ['baeume2/03', 'baeume/03', 'klein2/58', 'klein2/04', 'klein2/05', 'klein2/11']
LIEGEND = {'klein/58', 'klein/63', 'klein/15', 'klein/30', 'klein/25'}
FLACH = LIEGEND | {'klein/09', 'klein/10', 'klein/11', 'klein/12', 'baeume/14', 'klein2/04', 'klein2/05', 'klein2/11'}
WIND = {'klein/09', 'klein/10', 'klein/12', 'klein/35', 'baeume/03', 'klein2/04', 'klein2/05', 'klein2/11', 'klein2/58'}
SPIELZEUG = ['klein/02', 'klein/03', 'klein/06', 'klein/07', 'klein/22', 'klein/32', 'klein/41', 'klein/42',
             'klein/43', 'klein/45', 'klein/46', 'klein/53', 'klein/54', 'klein/59', 'klein/14', 'klein/52']

SCHAUKEL = {'baeume2/08', 'klein2/61', 'klein/06'}
HAUS_ANIM = {'haeuser/03': 'kamin', 'haeuser/02': 'kamin', 'haeuser2/03': 'glocke'}   # Rauch aus dem Kamin, Glocke
# (sprite, Mitte x in px, Fussreihe, Optionen)  - grosse Objekte zuerst
FEST = [
    # Bahnhof: Gebaeude auf der Bahnsteigachse, Zug auf dem unteren Gleis
    ('bahnhof/00', ACHSE_BAHNHOF, 12, {'achse': ACHSE_BAHNHOF, 'anim': 'uhr'}),
    ('klein/39', ACHSE_BAHNHOF - 72, 13, {'symm': 'bsl', 'anim': 'lampe'}), ('klein/39', ACHSE_BAHNHOF + 72, 13, {'symm': 'bsl', 'anim': 'lampe'}),
    # Uhrenplatz: Uhrturm in der Mitte, Baenke und Laternen symmetrisch
    ('gross1/00', ACHSE_UHR, 55, {'achse': ACHSE_UHR, 'anim': 'uhr'}),
    (LAMPE, ACHSE_UHR - 72, 52, {'symm': 'ul', 'anim': 'lampe'}), (LAMPE, ACHSE_UHR + 72, 52, {'symm': 'ul', 'anim': 'lampe'}),
    (BANK, ACHSE_UHR - 72, 57, {'symm': 'ub'}), (BANK, ACHSE_UHR + 72, 57, {'symm': 'ub'}),
    # Brunnenplatz: Brunnen in der Mitte, vier Laternen und zwei Baenke symmetrisch
    ('spielplatz/08', ACHSE_BRUNNEN, 38, {'achse': ACHSE_BRUNNEN, 'anim': 'brunnen'}),
    (LAMPE, ACHSE_BRUNNEN - 96, 33, {'symm': 'bl1', 'anim': 'lampe'}), (LAMPE, ACHSE_BRUNNEN + 96, 33, {'symm': 'bl1', 'anim': 'lampe'}),
    (BANK, ACHSE_BRUNNEN - 48, 43, {'symm': 'bb'}), (BANK, ACHSE_BRUNNEN + 48, 43, {'symm': 'bb'}),
    # Burghof: Soldaten am Torweg, Brunnen im Rahmen, Blumenbeete in den Rahmenecken (symmetrisch)
    (SOLDAT, ACHSE_BURG - 56, 41, {'symm': 's1', 'ueberlappen': True}), (SOLDAT, ACHSE_BURG + 56, 41, {'symm': 's1', 'ueberlappen': True}),
    (SOLDAT, ACHSE_BURG - 56, 46, {'symm': 's2'}), (SOLDAT, ACHSE_BURG + 56, 46, {'symm': 's2'}),
    ('baeume/07', ACHSE_BURG, 54, {'achse': ACHSE_BURG, 'anim': 'brunnen'}),
    ('baeume/15', ACHSE_BURG - 72, 51, {'symm': 'f1'}), ('baeume/15', ACHSE_BURG + 72, 51, {'symm': 'f1'}),
    ('spielplatz/15', ACHSE_BURG - 72, 57, {'symm': 'f2'}), ('spielplatz/15', ACHSE_BURG + 72, 57, {'symm': 'f2'}),
    # Burghof unten: Kapelle links und Stall rechts an der Suedmauer, dazwischen die Spielzeugecke
    ('schloss2/01', 67 * T, 68, {}), ('schloss2/03', 84 * T, 68, {}),
    ('spielplatz/12', 73 * T, 67, {}), ('spielplatz/11', 76 * T + 8, 68, {}), ('spielplatz/10', 79 * T + 8, 67, {}),
    ('spielplatz/13', 66 * T, 61, {}), ('klein/32', 85 * T, 61, {}),
    ('klein/55', 72 * T, 62, {}), ('klein/60', 66 * T, 42, {}), ('klein/03', 85 * T + 8, 42, {}),
    # Spielplatz
    ('spielplatz/00', 27 * T, 49, {}), ('spielplatz/01', 35 * T, 48, {}), ('spielplatz/02', 38 * T, 54, {}),
    ('gross2/01', 35 * T, 69, {}), ('baeume/14', 21 * T, 57, {}), ('klein/26', 27 * T, 66, {}),
    ('klein/24', 23 * T, 61, {}), ('gross2/00', 29 * T, 62, {}),
    ('baeume/04', 47 * T, 66, {}), ('baeume/05', 21 * T + 8, 44, {}),
    # Garten (Beeterde): Beete, Kuebel, Windmuehle
    ('spielplatz/15', 6 * T + 8, 63, {}), ('baeume/15', 12 * T + 8, 63, {}), ('baeume/13', 9 * T + 8, 67, {}),
    ('banner/10', 4 * T + 8, 67, {}), ('klein/37', 14 * T, 66, {}), ('klein/36', 7 * T + 8, 68, {}),
    # Strasse: geparkte Spielzeugautos, Hydranten, Briefkaesten
    ('klein/00', 31 * T, 12, {}), ('klein/01', 45 * T, 28, {}), ('klein/00', 25 * T, 37, {}), ('klein/01', 59 * T, 9, {}),
    (BRIEF, 43 * T + 8, 15, {}), ('baeume/09', 29 * T + 8, 28, {}),          # Hydranten (zu gross) weggelassen
    ('baeume/09', 46 * T + 8, 46, {}), ('baeume/05', 17 * T + 8, 23, {}),
    # Teich: Ente am Ufer
    ('klein/08', 36 * T, 61, {}),
    # Baeume zwischen Bahnstrecke und den oberen Haeusern (Nutzer-Skizze, gruen), je mit Begleiter (Regel 5)
    ('klein/49', 11 * T + 8, 8, {'anim': 'baum'}), ('klein2/58', 12 * T + 8, 9, {'begleiter': True, 'anim': 'wehen'}),
    ('klein/48', 15 * T, 9, {'anim': 'baum'}), ('baeume/01', 19 * T + 8, 10, {'anim': 'baum'}),
    ('baeume2/03', 21 * T + 8, 11, {'begleiter': True}), ('klein2/11', 17 * T, 10, {'begleiter': True, 'anim': 'wehen'}),
    ('klein/49', 26 * T + 8, 8, {'anim': 'baum'}), ('klein2/04', 27 * T + 8, 9, {'begleiter': True, 'anim': 'wehen'}),
    ('baeume/00', 34 * T + 8, 9, {'anim': 'baum'}), ('baeume/03', 32 * T + 8, 10, {'begleiter': True, 'anim': 'wehen'}),
    ('klein/48', 50 * T, 8, {'anim': 'baum'}), ('klein2/05', 51 * T + 8, 9, {'begleiter': True, 'anim': 'wehen'}),
    # Neu (PixelLab k10_banner, k10_klein2, k10_baeume2)
    ('baeume2/12', 52 * T, 67, {'anim': 'zirkus'}), ('baeume2/13', 21 * T, 66, {'achse': 21 * T}), ('baeume2/08', 23 * T + 8, 52, {'anim': 'schaukeln', 'amp': 7, 'fest': 0.32}),
    ('klein2/63', 33 * T, 52, {}), ('klein2/61', 27 * T, 54, {'anim': 'schaukeln', 'amp': 6, 'fest': 0.12}),
    ('banner/12', 62 * T + 4, 23, {}), ('banner/05', 85 * T, 18, {'anim': 'signal'}),
    # Bahnhof und Strecke (PixelLab k10_bahn, k10_bahn2): Wasserturm und Stellwerk neben dem Bahnhof, Gueterschuppen
    # und Kohlebunker auf dem Vorplatz, Prellboecke an den Gleisenden, Gepaeck am Bahnsteig, Masten im festen Abstand
    ('bahn/00', 67 * T, 12, {'achse': 67 * T}), ('bahn/01', 1354, 12, {'achse': 1354}),
    ('bahn/02', 1050, 29, {'achse': 1050}), ('bahn/03', 1380, 29, {'achse': 1380}),
    ('bahn2/02', 66 * T + 8, 31, {}), ('bahn2/13', 85 * T, 31, {}),
    ('bahn2/00', 74 * T, 15, {'ueberlappen': True}), ('bahn2/03', 78 * T + 8, 15, {'ueberlappen': True}),
    # Schranken geschlossen: Pfosten auf dem linken Gehweg, der Arm sperrt quer ueber die Strasse
    ('bahn2/11_zu', 29 * T + 8, 8, {'ueberlappen': True}), ('bahn2/11_zu', 43 * T + 8, 8, {'ueberlappen': True}),
    ('bahn2/11_zu', 57 * T + 8, 8, {'ueberlappen': True}),
    ('bahn2/05', 55 * T + 8, 6, {}), ('bahn2/05', 63 * T + 8, 21, {}),
    ('bahn2/02', 9 * T + 8, 6, {}), ('bahn2/03', 37 * T + 8, 6, {}), ('bahn2/09', 26 * T + 8, 6, {}),
    ('bahn2/14', 52 * T + 8, 6, {'anim': 'lampe'}),
] + [('bahn2/06', x * T + 8, 3, {'fest_pos': True}) for x in (6, 18, 30, 42, 54, 66)] + [
    ('banner/05', 20 * T + 8, 6, {'anim': 'signal'}), ('banner/05', 46 * T + 8, 6, {'anim': 'signal'}),
    ('banner/13', 32 * T + 8, 23, {'anim': 'ampel'}), ('banner/13', 46 * T + 8, 23, {'anim': 'ampel'}),
    ('banner/13', 43 * T + 8, 34, {'anim': 'ampel'}),
    ('klein2/00', 46 * T + 8, 13, {}), ('klein2/00', 32 * T + 8, 30, {}), ('klein2/00', 60 * T + 8, 28, {}),
    ('klein2/01', 24 * T + 8, 17, {}), ('banner/15', 12 * T + 8, 11, {}),
    ('banner/11', 35 * T, 33, {}), ('banner/11', 49 * T, 33, {}),
    ('banner/14', ACHSE_BRUNNEN, 43, {'achse': ACHSE_BRUNNEN}),
    ('baeume2/07', ACHSE_BURG - 104, 47, {'symm': 'kl', 'anim': 'lampe'}), ('baeume2/07', ACHSE_BURG + 104, 47, {'symm': 'kl', 'anim': 'lampe'}),
]
# Laternen in festem Rhythmus entlang der Gehwege (alle 6 Kacheln), Wegweiser an den Kreuzungen
# (ausgeduennt: je Strassenzug nur wenige Laternen, versetzt statt in Reihen)
FEST += [(LAMPE, 43 * T + 8, 12, {'anim': 'lampe'}), (LAMPE, 43 * T + 8, 29, {'anim': 'lampe'}),
         (LAMPE, 24 * T + 8, 19, {'anim': 'lampe'}), (LAMPE, 52 * T + 8, 19, {'anim': 'lampe'}),
         (LAMPE, 38 * T + 8, 35, {'anim': 'lampe'})]
# Waldrand (Karte 01 wiederverwendet, Regel 3) mit ein paar rosa Bluetenbaeumen passend zur Spielzeugstadt
WALD = {'rand/k1-00': 5, 'rand/k1-01': 5, 'rand/k1-02': 4, 'rand/k1-06': 4, 'rand/k1-07': 3, 'rand/k1-09': 4,
        'rand/k1-15': 2, 'rand/k1-04': 1, 'rand/k1-05': 1, 'rand/k1-10': 1}
WALDSAUM = {'rand/k1-12': 3, 'rand/k1-13': 2, 'baeume2/03': 2, 'baeume/03': 2, 'klein2/58': 2, 'klein/09': 2,
            'klein/10': 2, 'klein2/04': 1, 'klein2/05': 1}
# Haine (x0, y0, x1, y1, Dichte): Baeume nur auf Gras
HAINE = [(2, 4, 28, 10, 0.05), (2, 14, 15, 18, 0.06), (2, 39, 28, 58, 0.06), (11, 23, 17, 34, 0.06),
         (33, 4, 42, 18, 0.04), (47, 4, 56, 18, 0.04), (33, 23, 42, 34, 0.04), (47, 23, 56, 34, 0.04),
         (47, 39, 58, 48, 0.08), (30, 64, 58, 70, 0.07), (46, 58, 58, 66, 0.06), (14, 60, 22, 70, 0.06),
         (2, 70, 10, 71, 0.1)]
STREU = {'klein/09': 4, 'klein/10': 4, 'klein2/04': 3, 'klein2/05': 3, 'klein2/11': 2, 'klein/12': 8, 'klein/11': 3, 'klein/05': 2, 'klein/56': 2, 'klein/58': 1,
         'klein/15': 1, 'klein/30': 1, 'klein/04': 1}


def main():
    rnd = random.Random(10)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    lvl = np.load(os.path.join(KARTE, 'pixelhoehe.npy'))
    os.makedirs(os.path.join(OBJ, 'sauber'), exist_ok=True)
    gesperrt = set()
    for (x0, y0, x1, y1) in lay.get('bruecken', []):
        for y in range(y0 - 1, y1 + 2):
            for x in range(x0 - 1, x1 + 2):
                gesperrt.add((x, y))
    for tp in lay.get('teleporter', []):
        for y in range(tp['y'] - 1, tp['y'] + tp['h'] + 1):
            for x in range(tp['x'], tp['x'] + tp['b'] + 2):
                gesperrt.add((x, y))
    cache, alpha = {}, {}
    objekte, belegt = [], set()
    pixel = np.zeros(lvl.shape, bool)

    def sprite(name, spiegeln=False):
        key = (name, spiegeln)
        if key not in cache:
            if name == 'turm':                                   # Eckturm aus der Burgfront ausgeschnitten
                a = np.array(Image.open(os.path.join(OBJ, 'burg/00.png')).convert('RGBA'))
                a[:, 46:, 3] = 0
                a[80:, 27:, 3] = 0
                sp = Image.fromarray(a)
                sp = sp.crop(sp.getbbox())
            else:
                basis_ = name.replace('_zu', '').replace('_gedreht', '')
                sp = saeubern(Image.open(os.path.join(OBJ, basis_ + '.png')).convert('RGBA'))
                if name.endswith('_zu'):                         # Schranke geschlossen: senkrechten Arm entfernen
                    a_ = np.array(sp)
                    pfosten = int(np.nonzero(a_[:, :a_.shape[1] // 3, 3].any(axis=1))[0].min())
                    oben_arm = int(a_.shape[0] * 0.48)
                    a_[:oben_arm, :, 3] = 0
                    sp = Image.fromarray(a_)
                    sp = sp.crop(sp.getbbox())
                if name.endswith('_gedreht'):                    # Prellbock quer zum Gleisende (Puffer nach links)
                    sp = sp.transpose(Image.ROTATE_90)
                if name.startswith('schloss2/'):                     # Rosa an das Hauptschloss anpassen
                    a_ = np.array(sp)
                    for q_, z_ in (('#f09ac8', '#ffd0e8'), ('#d06a9a', '#f09ac8')):
                        m_ = (a_[..., :3] == [int(q_[i:i + 2], 16) for i in (1, 3, 5)]).all(-1)
                        a_[m_, :3] = [int(z_[i:i + 2], 16) for i in (1, 3, 5)]
                    sp = Image.fromarray(a_)
                if name.startswith(('bahnhof/', 'haeuser', 'spielplatz/', 'baeume/', 'gross')):
                    sp = groesstes_teil(sp)                          # PixelLab-Reste (z. B. Glocke unter der Lok)
            if spiegeln:
                sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
            if name in SCHAUKEL:                                 # Rand zum Kippen
                g_ = Image.new('RGBA', (sp.width + 12, sp.height + 4), (0, 0, 0, 0))
                g_.alpha_composite(sp, (6, 4))
                sp = g_
            datei = 'sauber/%s%s.png' % (name.replace('/', '-'), '_m' if spiegeln else '')
            sp.save(os.path.join(OBJ, datei))
            a = np.array(sp.getchannel('A')) >= 128
            zu = int(np.nonzero(a.any(axis=1))[0].max())
            xs = np.nonzero(a.any(axis=0))[0]
            cache[key] = (datei, sp.height, zu, (xs.min() + xs.max() + 1) / 2.0)
            alpha[datei] = a
        return cache[key]

    def frei_px(datei, x, y):
        a = alpha[datei]
        h_, w_ = a.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(pixel.shape[0], y + h_), min(pixel.shape[1], x + w_)
        if y1 <= y0 or x1 <= x0:
            return True
        return not (pixel[y0:y1, x0:x1] & a[y0 - y:y1 - y, x0 - x:x1 - x]).any()

    def belegen(datei, x, y):
        a = np.array(Image.fromarray((alpha[datei] * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
        h_, w_ = a.shape
        y0, x0 = max(0, y), max(0, x)
        y1, x1 = min(pixel.shape[0], y + h_), min(pixel.shape[1], x + w_)
        if y1 > y0 and x1 > x0:
            pixel[y0:y1, x0:x1] |= a[y0 - y:y1 - y, x0 - x:x1 - x]

    def auf_land(datei, x, y):
        """Regel 'Gebaeude stehen ganz auf Land': jede Spalte des Sprites ueber Boden (nicht Wasser/Mauer/Hecke)."""
        a = alpha[datei]
        ys, xs = np.nonzero(a)
        ys, xs = ys + y, xs + x
        ok = (ys >= 0) & (ys < lvl.shape[0]) & (xs >= 0) & (xs < lvl.shape[1])
        if not ok.all():
            return False
        return (lvl[ys, xs] == 1).mean() > 0.97

    def fest_setzen(name, X, fy, opt, spiegeln=False, suchen=False, an_wand=False, pruefen=True, melden=False):
        opt = dict(opt)
        datei, h, zu, mitte = sprite(name, spiegeln or opt.pop('spiegeln', False))
        kand = [(X, fy)]
        if suchen:
            kand += sorted(((X + dx * T, fy + dy) for dx in range(-2, 3) for dy in range(-2, 3) if dx or dy),
                           key=lambda k: abs(k[0] - X) / T + abs(k[1] - fy))
        for (kx, ky) in kand:
            tx = int(kx // T)
            if (tx, ky) in gesperrt:
                continue
            if 0 <= ky < rows and 0 <= tx < cols and tx < 60 and cls[ky][tx] == 's' and not opt.get('achse'):
                continue                                    # nichts mitten auf die Sandwege
            if 0 <= ky < rows and 0 <= tx < cols and cls[ky][tx] == 'W' and not opt.get('wald'):
                continue                                    # Waldboden: nur Waldbaeume
            x = raster_x(alpha[datei], kx) if not opt.get('achse') else int(round(kx - mitte))
            y = (ky + 1) * T - 1 - zu
            if not pruefen:
                break
            gross = name.startswith(('haeuser', 'bahnhof/00'))
            if bewerten(lvl, alpha[datei], x, y) and (opt.get('ueberlappen') or frei_px(datei, x, y)) and (not gross or auf_land(datei, x, y)) \
                    and lvl[min(lvl.shape[0] - 1, ky * T + 15), min(lvl.shape[1] - 1, int(kx))] == 1:
                break
        else:
            if melden:
                print('  keine passende Stelle:', name, (X // T, fy))
            return None
        o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [int(kx // T), ky],
             'ebene': 0 if name in FLACH else 1}
        if name in LIEGEND:
            o['liegend'] = True
        if name in WIND:
            o['anim'] = 'wehen'
        if an_wand:
            o.update({'an_wand': True, 'kein_schatten': True, 'keine_verdeckung': True, 'vorrang': True, 'fest_pos': True})
        o.update(opt)
        objekte.append(o)
        belegt.add((int(kx // T), ky))
        if name not in FLACH:
            belegen(datei, x, y)
        return o

    # 1) Burg: das Hauptschloss (PixelLab k10_schloss) ist der Torbau in der Nordmauer, genau auf der Achse.
    datei, h, zu, mitte = sprite('schloss/00')
    SCHLOSS_FUSS = WAND_FUSS + 2 * T                     # Hauptschloss steht 2 Kacheln vor der Mauer im Hof (Nutzer)
    objekte.append({'datei': datei, 'basis': 'schloss/00', 'x': int(round(ACHSE_BURG - mitte)), 'y': SCHLOSS_FUSS - zu,
                    'fuss': h, 'kachel': [76, 39], 'ebene': 1, 'keine_verdeckung': True, 'vorrang': True, 'fest_pos': True, 'anim': 'fahnen_tuch'})
    belegen(datei, int(round(ACHSE_BURG - mitte)), SCHLOSS_FUSS - zu)
    # Rundtuerme (PixelLab k10_schloss2/02, im Stil des Hauptschlosses) in festem Rhythmus: an den Enden der
    # Burgfront (spiegelgleich zur Achse), auf der Ostmauer in gleichen Abstaenden, an den Ecken der Suedmauer
    td, th, tzu, tm = sprite('schloss2/02')
    to, _, _, _ = sprite('schloss2/02_ohne_tuer')          # Tuerme ohne Tuer (Nutzer: Tueren ins Nichts weg)
    tw = alpha[td].shape[1]
    W_, O_ = 63 * T + 8, 88 * T + 8                       # Mitte der West- und Ostmauer (symmetrisch zu 1216)
    # Tuerme an Nord- und Seitenmauern stehen innen im Burghof direkt an der Mauer (Fuss auf dem Hofboden, nicht auf
    # der schmalen Mauerkrone - die Mauer laeuft sichtbar daneben weiter), exakt spiegelgleich zur Achse
    # Tuerme mittig auf der Mauerlinie; die anschliessende Mauer ragt eine Kachel in den Turm hinein (ihre Krone liegt
    # ueber dem untersten Turmstueck), so steht der Turm sichtbar am Boden und nicht auf der Mauer
    tuerme = [(W_, WAND_FUSS + T, True, to), (O_, WAND_FUSS + T, True, to),     # Ecken Nordmauer (1 Kachel vor)
              (W_, 55 * T + 15, True, td), (O_, 55 * T + 15, True, to),         # am Seitentor (West) / gegenueber (Ost)
              (W_, 73 * T + 15, True, td), (O_, 73 * T + 15, True, td)]         # Ecken Suedmauer (Baeume davor)
    for (cx, fy, wand, td) in tuerme:
        xx = int(round(cx - tm))
        objekte.append({'datei': td, 'basis': 'schloss2/02', 'x': xx, 'y': fy - tzu, 'fuss': th,
                        'kachel': [int(cx // T), fy // T], 'ebene': 1, 'vorrang': True, 'fest_pos': True,
                        'anim': 'fahnen_tuch', 'an_wand': True, 'kein_schatten': True, 'keine_verdeckung': True,
                        **({'mauer_davor': T} if fy < 70 * T else {})})
        belegen(td, xx, fy - tzu)
    # Prellboecke an den rechten Gleisenden: gedreht, stehen senkrecht quer zum Gleis, Puffer zum Zug hin
    pd, ph, pzu, pm = sprite('bahn2/07_gedreht')
    pa = alpha[pd]
    pys = np.nonzero(pa.any(axis=1))[0]
    for gl in lay['gleise']:
        yc = gl['y'] * T + 7
        x_ = gl['x'][1] * T - pa.shape[1] - 2 if gl['x'][1] < cols else cols * T - pa.shape[1] - 2
        y_ = int(yc - (pys.min() + pys.max()) / 2)
        objekte.append({'datei': pd, 'basis': 'bahn2/07_gedreht', 'x': int(x_), 'y': y_, 'fuss': ph,
                        'kachel': [int(x_ // T), gl['y']], 'ebene': 1, 'fest_pos': True, 'vorrang': True})
        belegen(pd, int(x_), y_)
    # 2) Zug auf dem unteren Gleis (Raeder auf der Schiene), Lok vorne links (Schienenraeumer zeigt nach links)
    gy = lay['gleise'][1]['y'] * T + 13
    x = 66 * T
    for name in ('bahnhof/01', 'bahnhof/02', 'bahnhof/02'):
        datei, h, zu, mitte = sprite(name)
        objekte.append({'datei': datei, 'basis': name, 'x': x, 'y': gy - zu, 'fuss': h, 'kachel': [x // T, gy // T],
                        'ebene': 1, 'fest_pos': True, 'vorrang': True, **({'anim': 'rauch'} if name == 'bahnhof/01' else {})})
        belegen(datei, x, gy - zu)
        x += alpha[datei].shape[1] + 1
    # 3) Haeuser (Layout: Mitte, Fussreihe)
    for (name, X, fy, _, _) in lay['haeuser']:
        fest_setzen(name, X, fy, {'vorrang': True, **({'anim': HAUS_ANIM[name]} if name in HAUS_ANIM else {})}, melden=True)
    # 4) feste Objekte
    for (name, X, fy, opt) in FEST:
        fest_setzen(name, X, fy, opt, suchen=not opt.get('symm') and not opt.get('achse'), melden=True)
    # 4b) Waldrand wie Karte 01: dichtes, versetztes Raster einzelner Baeume auf dem Waldboden (Baeume duerfen
    #     sich im dichten Wald ueberlappen), am Waldsaum Buesche und Blumen
    wald_neu = []
    # unten laeuft der Wald ueber den Kartenrand hinaus: die suedlichsten Baeume stehen ausserhalb, so dass am
    # unteren Rand nur Kronen zu sehen sind (keine abgeschnittenen Staemme)
    for ay in range(8, rows * T + 40, 15):
        versatz = rnd.randint(0, 10)
        for ax in range(versatz, cols * T, 19):
            px_, py_ = ax + rnd.randint(-5, 5), ay + rnd.randint(-4, 4)
            cx, cy = px_ // T, (py_ + 2) // T
            if not (0 <= cx < cols) or cls[min(cy, rows - 1)][cx] != 'W':
                continue
            name = rnd.choices(list(WALD), weights=list(WALD.values()))[0]
            datei, h, zu, mitte = sprite(name, rnd.random() < 0.5)
            x, y = int(round(px_ - mitte)), py_ + 2 - zu
            if not frei_px(datei, x, y):
                continue
            o = {'datei': datei, 'basis': name, 'x': x, 'y': y, 'fuss': h, 'kachel': [cx, cy], 'ebene': 1,
                 'anim': 'baum', 'wald': True}
            objekte.append(o)
            wald_neu.append(o)
    # Vor den unteren Ecktuermen der Burg stehen Waldbaeume (Fuss unterhalb des Kartenrands) und verdecken die Tueren
    for (cx, name) in ((63 * T + 8 - 10, 'rand/k1-01'), (63 * T + 8 + 12, 'rand/k1-06'),
                       (88 * T + 8 + 10, 'rand/k1-00'), (88 * T + 8 - 12, 'rand/k1-09')):
        datei, h, zu, mitte = sprite(name)
        o = {'datei': datei, 'basis': name, 'x': int(round(cx - mitte)), 'y': rows * T + 6 - zu, 'fuss': h,
             'kachel': [cx // T, rows - 1], 'ebene': 1, 'anim': 'baum', 'wald': True, 'fest_pos': True}
        objekte.append(o)
        wald_neu.append(o)
    for o in wald_neu:
        belegen(o['datei'], o['x'], o['y'])
    for ty in range(rows):
        for tx in range(cols):
            if cls[ty][tx] != 'g':
                continue
            am_wald = any(0 <= ty + dy < rows and 0 <= tx + dx < cols and cls[ty + dy][tx + dx] == 'W'
                          for dx in (-1, 0, 1) for dy in (-1, 0, 1))
            if am_wald and rnd.random() < 0.22:
                fest_setzen(rnd.choices(list(WALDSAUM), weights=list(WALDSAUM.values()))[0],
                            tx * T + rnd.randint(4, 12), ty, {})
    # 5) Baeume in Hainen, Regel 5: Einzelbaeume bekommen Begleiter
    baeume = []
    for (x0, y0, x1, y1, d) in HAINE:
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if cls[ty][tx] == 'g' and rnd.random() < d and (tx, ty) not in belegt:
                    o = fest_setzen(rnd.choice(BAEUME), tx * T + 8, ty, {'spiegeln': rnd.random() < 0.5})
                    if o:
                        if o['basis'] not in STARR:
                            o['anim'] = 'baum'
                        baeume.append(o)
    for o in baeume:
        kx, ky = o['kachel']
        if not [p for p in baeume if p is not o and abs(p['kachel'][0] - kx) <= 3 and abs(p['kachel'][1] - ky) <= 3]:
            for dx in (rnd.choice((-1, 1)), ):
                b = fest_setzen(rnd.choice(BUESCHE[:2]), (kx + dx * 2) * T + 8, ky, {})
                if b:
                    b['begleiter'] = True
            fest_setzen(rnd.choice(BUESCHE[2:]), (kx + rnd.choice((-1, 1))) * T + 8, ky + 1, {'begleiter': True})
    # 6) Kleinkram auf Gras (unregelmaessig, eher wenig), nie auf/neben Strassen und Plaetzen
    namen, gew = list(STREU), list(STREU.values())
    n = 0
    for _ in range(6000):
        if n >= 70:
            break
        tx, ty = rnd.randrange(2, 60), rnd.randrange(3, 72)
        if any(cls[yy][xx] != 'g' for yy in range(ty - 1, ty + 2) for xx in range(tx - 1, tx + 2)):
            continue
        name = rnd.choices(namen, weights=gew)[0]
        if fest_setzen(name, tx * T + 8, ty, {}):
            n += 1
    # Spielzeug im Burghof (nicht auf Weg/Rahmen)
    n = 0
    for _ in range(3000):
        if n >= 6:
            break
        tx, ty = rnd.randrange(61, 85), rnd.randrange(37, 71)
        if any(cls[yy][xx] != 'k' for yy in range(ty - 1, ty + 2) for xx in range(tx - 1, tx + 2)):
            continue
        nm = rnd.choice(SPIELZEUG)
        if fest_setzen(nm, tx * T + 8, ty, {'anim': 'schaukeln', 'amp': 4, 'fest': 0.05} if nm == 'klein/06' else {}):
            n += 1
    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte gesetzt')


def symmetrie():
    """Paare exakt spiegelsymmetrisch zur Achse ihres Platzes; Objekte mit 'achse' genau auf die Achse."""
    pf = os.path.join(OBJ, 'platzierung.json')
    objs = json.load(open(pf))
    for o in objs:
        if o.get('achse'):
            a_ = np.array(Image.open(os.path.join(OBJ, o['datei'])).getchannel('A')) > 128
            xs_ = np.nonzero(a_.any(axis=0))[0]
            o['x'] = int(round(o['achse'] - (xs_.min() + xs_.max() + 1) / 2.0))
    paare = {}
    for o in objs:
        if o.get('symm'):
            paare.setdefault(o['symm'], []).append(o)
    achsen = {'bsl': ACHSE_BAHNHOF, 'bsb': ACHSE_BAHNHOF, 'ul': ACHSE_UHR, 'ub': ACHSE_UHR, 'bl1': ACHSE_BRUNNEN,
              'bl2': ACHSE_BRUNNEN, 'bb': ACHSE_BRUNNEN}
    for name, ps in paare.items():
        if len(ps) != 2:
            print('  Paar unvollstaendig:', name, len(ps))
            continue
        l, r = sorted(ps, key=lambda o: o['x'])
        achse = achsen.get(name, ACHSE_BURG)
        a_ = np.array(Image.open(os.path.join(OBJ, l['datei'])).getchannel('A')) > 128
        xs_ = np.nonzero(a_.any(axis=0))[0]
        # sichtbare Mitte des linken Objekts spiegeln
        ml = l['x'] + (xs_.min() + xs_.max() + 1) / 2.0
        r['x'] = int(round(2 * achse - ml - (xs_.min() + xs_.max() + 1) / 2.0))
        r['y'] = l['y']
    json.dump(objs, open(pf, 'w'), indent=0)
    print('Symmetrie: %d Paare' % len(paare))


if __name__ == '__main__':
    symmetrie() if sys.argv[1:] == ['symmetrie'] else main()
