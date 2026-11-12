"""Gezielte Objekt-Korrekturen aus der Agenten-Gesamtpruefung (Nutzer: "kontrolliere alles") -> platzierung.json

  python3 tools/korrektur_a02.py [karteNN ...]

Wird am Ende von regeln_a02.objekte_pruefen aufgerufen (also bei jedem Neubau der Objekte wieder angewendet).
Eintraege je Karte:
  ('weg', basis, x, y)                 Objekt entfernen (Treffer: gleiche basis, Position +-4 px)
  ('setze', basis, x, y, {feld: wert}) Felder setzen (z. B. neue x/y)
  ('weg_box', x0, y0, x1, y1, max_h)   kleine Streudeko (Sprite-Hoehe <= max_h), deren Bild die Box beruehrt, entfernen
  ('weg_basis_box', prefix, x0, y0, x1, y1)  Objekte mit basis-Anfang prefix, deren Bild die Box beruehrt, entfernen
"""
import json, os, sys
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

KORR = {
    'karte20': [
        ('weg', 'klein/02', 291, 251),                                   # Anschlagbrett am Brueckenkopf (halb ueber Wasser)
        ('weg', 'klein/01', 194, 597), ('weg', 'klein/01', 258, 597),   # Vogelscheuchen nicht im Raster
        ('weg', 'klein/01', 162, 645), ('weg', 'klein/01', 290, 645),
    ],
    'karte21': [
        ('weg', 'k01/deko25', 737, 949), ('weg', 'k01/deko27', 685, 968),     # Bueche vor dem Tor
        ('weg', 'k01/deko08', 932, 752), ('weg', 'k01/deko08', 932, 800), ('weg', 'k01/deko08', 932, 848),
        ('weg', 'k01/deko08', 516, 848), ('weg', 'k01/deko10', 451, 733), ('weg', 'k01/deko10', 483, 781),
        ('weg', 'k01/deko10', 483, 877),                                      # Felsen auf Pflaster, in Reihe
        ('weg', 'k01/deko30', 949, 227), ('weg', 'k01/deko04', 1163, 292), ('weg', 'k01/deko27', 1275, 472),
        ('weg_box', 995, 800, 1055, 850, 26),                                 # Blumenklumpen am Stumpf
        ('setze', 'k04/wegweiser', 722, 180, {'x': 690}),                     # nicht in die Feuerstelle
        ('spiegel', 'k01/laterne', 432, 934, 'k01/laterne', 992, 918, 728),   # Paare spiegelsymmetrisch zur Torachse
        ('spiegel', 'lager/banner', 548, 978, 'lager/banner', 900, 978, 728),
        ('spiegel', 'k03/schild', 451, 979, 'k03/schild', 963, 979, 728),
        ('setze', 'k01/laterne', 256, 822, {'y': 838}),                       # Laternen an den Treppen gleich hoch
    ],
    'karte23': [
        ('weg', 'wagen/00', 767, 818), ('weg', 'k01/laterne', 160, 534), ('weg', 'k01/laterne', 240, 678),
        ('weg', 'k01/deko11', 1440, 921),
        ('weg_basis_box', 'k01/baum', 1560, 1130, 1600, 1186),                 # Teleporter rechts frei
    ],
    'karte24': [
        ('weg', 'schrein/01', 1009, 145), ('weg', 'schrein/01', 1201, 145),   # Standartenpaar am Pult/den Saecken
        ('setze', 'mine/00', 1189, 1069, {'x': 1173}),                        # Faesser nicht ueber der Grube
    ],
    'karte25': [
        ('weg', 'k01/deko11', 384, 281),                                      # Fels auf der Klippenkante
    ],
    'karte26': [
        ('weg_box', 980, 486, 1090, 600, 30),                                 # Portal frei
        ('weg_box', 470, 285, 505, 312, 30), ('weg_box', 695, 183, 780, 225, 30), ('weg_box', 968, 362, 1000, 396, 30),
        ('weg_box', 1112, 138, 1132, 166, 30), ('weg_box', 312, 808, 392, 836, 30),
        ('weg_box', 490, 505, 520, 532, 30), ('weg_box', 490, 647, 522, 680, 30), ('weg_box', 311, 551, 343, 582, 30),
        ('weg_box', 805, 683, 840, 712, 30),
    ],
    'karte27': [
        ('weg', 'k01/baum01', 1568, 117), ('weg', 'k01/baum12', 1537, 60), ('weg', 'k01/baum00', 1568, 53),   # Teleporter
        ('weg', 'k01/baum00', 240, 629),                                      # Baum auf dem Grubenrand
    ],
    'karte28': [
        ('weg', 'deko/fels0', 808, 692), ('weg', 'k01/deko14', 812, 730),     # nichts auf dem Obelisken
        ('weg', 'k24/obelisk_gras', 224, 705), ('weg', 'k24/obelisk_liegend', 1424, 152),
        ('weg', 'wald_dunkel/04', 1573, 84), ('weg', 'wald_dunkel/00', 1536, 21),
        ('weg', 'netz/02', 169, 336), ('weg', 'netz/02', 441, 320), ('weg', 'netz/00', 696, 320),
    ],
    'karte29': [
        ('weg', 'k11/felsnadel', 1318, 0),                                    # Teleporter oben rechts frei
    ],
    'karte07': [
        ('setze', 'turm/schwarz_gross', 831, -14, {'y': 2}),                  # Spitze nicht abgeschnitten
        ('setze', 'turm/schwarz_gross', 575, 98, {'x': 591}), ('setze', 'turm/schwarz_gross', 1055, 98, {'x': 1071}),
        ('weg', 'mittel/05', 803, 1106),                                      # Bambus auf dem Weg
    ],
    'karte30': [
        ('weg', 'karte18/strasse/18', 1652, 738), ('weg', 'karte18/strasse/18', 1652, 866),
        ('weg', 'karte18/strasse/18', 1796, 866),                              # Laternen im Riesenrad
        ('weg_basis_box', 'karte01/baeume', 1924, 568, 2028, 1075),            # Waldrand vor den Fassaden
        ('weg_basis_box', 'karte18/baum', 1924, 568, 2028, 1075),
    ],
    'karte31': [
        ('weg_kachel', 'karte18/autos/00', 60, 50),                           # Auto quer auf der Nord-Sued-Strasse
        ('weg_kachel', 'karte18/baum2/01', 30, 55),
        ('weg', 'karte18/strasse/18', 1380, None),
    ],
    'karte32': [
        ('weg_kachel', 'karte09/k8/klein/48', 42, 78), ('weg_kachel', 'karte09/k8/klein/48', 58, 78),
        ('weg_kachel', 'karte09/k8/klein/48', 76, 78),                         # Buesche auf der Mauerkrone
    ],
}


def _bbox(obj_dir, o, cache):
    if o['datei'] not in cache:
        try:
            cache[o['datei']] = Image.open(os.path.join(obj_dir, o['datei'])).getbbox() or (0, 0, 0, 0), \
                Image.open(os.path.join(obj_dir, o['datei'])).height
        except OSError:
            cache[o['datei']] = ((0, 0, 0, 0), 0)
    (a, b, c, d), h = cache[o['datei']]
    return (o['x'] + a, o['y'] + b, o['x'] + c, o['y'] + d), h


def _treffer(o, basis, x, y):
    return o['basis'] == basis and abs(o['x'] - x) <= 4 and (y is None or abs(o['y'] - y) <= 4)


def anwenden(karte):
    liste = KORR.get(karte)
    if not liste:
        return 0
    obj_dir = os.path.join(ROOT, 'assets', 'objekte', karte)
    pf = os.path.join(obj_dir, 'platzierung.json')
    objs = json.load(open(pf))
    cache = {}
    weg = set()
    for e in liste:
        if e[0] == 'weg':
            weg |= {i for i, o in enumerate(objs) if _treffer(o, e[1], e[2], e[3])}
        elif e[0] == 'weg_kachel':
            weg |= {i for i, o in enumerate(objs) if o['basis'] == e[1] and list(o.get('kachel', [])) == [e[2], e[3]]}
        elif e[0] == 'setze':
            for o in objs:
                if _treffer(o, e[1], e[2], e[3]):
                    for k_, v_ in e[4].items():
                        if k_ in ('x', 'y') and 'kachel' in o:
                            o['kachel'][0 if k_ == 'x' else 1] += round((v_ - o[k_]) / 16)
                        o[k_] = v_
        elif e[0] == 'spiegel':                                       # linkes Objekt an der Achse spiegeln (Mitte, Fuss)
            _, bl, xl, yl, br, xr, yr, achse = e
            r = [o for o in objs if _treffer(o, br, xr, yr)]
            for o in objs:
                if _treffer(o, bl, xl, yl) and r:
                    w_l = Image.open(os.path.join(obj_dir, o['datei'])).width
                    w_r = Image.open(os.path.join(obj_dir, r[0]['datei'])).width
                    mitte_r = r[0]['x'] + w_r / 2
                    o['x'] = int(round(2 * achse - mitte_r - w_l / 2))
                    o['y'] = r[0]['y'] + r[0]['fuss'] - o['fuss']
        elif e[0] in ('weg_box', 'weg_basis_box'):
            x0, y0, x1, y1 = e[1:5] if e[0] == 'weg_box' else e[2:6]
            for i, o in enumerate(objs):
                (a, b, c, d), h = _bbox(obj_dir, o, cache)
                if a < x1 and c > x0 and b < y1 and d > y0:
                    if (e[0] == 'weg_box' and h <= e[5] and not o.get('anim') in ('portal',)) or \
                            (e[0] == 'weg_basis_box' and o['basis'].startswith(e[1])):
                        weg.add(i)
    neu = [o for i, o in enumerate(objs) if i not in weg]
    json.dump(neu, open(pf, 'w'), indent=0)
    print('%s: %d Objekte entfernt (Korrekturliste)' % (karte, len(weg)))
    return len(weg)


if __name__ == '__main__':
    for k in (sys.argv[1:] or list(KORR)):
        anwenden(k)
