"""Grosse Einzelobjekte (> 256 px) mit dem PixelLab Pro-Generator (generate-image-v2).

AUSNAHME von der Regel "PixelLab nur Objekt-Creator" (Nutzer, Karte 25): nur fuer Objekte, die groesser als 256 px
sein muessen (Schiff in Sunset Bay). Subjekt-Referenz = Ausschnitt der Vorlage (geschuetzte Symbole vorher
uebermalt), Stil-Referenz = ein vorhandenes Objekt der Karte, damit Pixeldichte, Kontur und Licht passen.

  python3 tools/pixellab_gross.py schiff
"""
import base64, io, json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
from pixellab_objekte import call, FR14

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


def b64(im):
    buf = io.BytesIO(); im.save(buf, 'PNG')
    return base64.b64encode(buf.getvalue()).decode()


def ref(im, beschreibung=None):
    r = {'image': {'type': 'base64', 'base64': b64(im), 'format': 'png'}, 'size': {'width': im.width, 'height': im.height}}
    if beschreibung:
        r['usage_description'] = beschreibung
    return r


AUFTRAEGE = {
    'schiff': {
        'ziel': 'assets/objekte/karte25/schiff',
        'groesse': (480, 304),
        'vorlage': ('assets/vorlagen/karte25_vorlage.png', (1424, 160, 1904, 464)),
        'uebermalen': [(1640, 270, 1720, 330)],                 # Wappen der Vorlage (geschuetztes Design) entfernen
        'stil': 'assets/objekte/karte25/leuchtturm/00.png',
        'text': ('huge dark steel battleship docked in a harbor, seen from the side as a flat 2D profile, bow pointing left '
                 'with a sharp ram, long dark grey riveted steel hull with a thin red stripe along the deck line and a row of '
                 'small glowing purple round portholes, two anchor chains hanging from the bow, on the deck a big double gun '
                 'turret at the front, a tall blocky command tower in the middle with a glowing red visor slit and a pointed '
                 'spire on top, a small golden winged emblem of a simple star with wings on the tower front, a second tower '
                 'at the back with antennas and many small lit windows, ' + FR14),
    },
}
_EIGEN = ('original design, not a copy of any existing ship, seen from the side as a flat 2D profile, bow pointing left, '
          'lying calm on the water line, no water, no background, ')
AUFTRAEGE['schiff_a'] = {'ziel': 'assets/objekte/karte25/schiff_a', 'groesse': (480, 304), 'vorlage': None,
    'stil': 'assets/objekte/karte25/leuchtturm/00.png',
    'text': ('huge sinister dark emperor flagship, ' + _EIGEN + 'black armoured steel hull with gold trim and a row of glowing '
             'crimson round portholes, a sharp ram bow, a tall stepped castle-like bridge tower in the middle with a glowing red '
             'eye window and gold spikes, two smaller towers with pennant flags, heavy anchor chains at the bow, ' + FR14)}
AUFTRAEGE['schiff_b'] = {'ziel': 'assets/objekte/karte25/schiff_b', 'groesse': (480, 304), 'vorlage': None,
    'stil': 'assets/objekte/karte25/leuchtturm/00.png',
    'text': ('large digital world cyber warship, ' + _EIGEN + 'dark gunmetal hull with glowing cyan circuit lines and data '
             'panels, rows of small cyan lit portholes, a curved sleek bow, a central command tower with a big glowing visor and '
             'antenna arrays, a satellite dish at the back, small blinking lights, ' + FR14)}
AUFTRAEGE['schiff_c'] = {'ziel': 'assets/objekte/karte25/schiff_c', 'groesse': (480, 304), 'vorlage': None,
    'stil': 'assets/objekte/karte25/leuchtturm/00.png',
    'text': ('huge old ironclad steam battleship, ' + _EIGEN + 'dark riveted iron hull with a dark red waterline stripe, '
             'round brass portholes, two tall black smokestacks with red bands, a wooden deck with a big round gun turret, '
             'a small command bridge with lit windows, masts with rigging and a dark flag, anchor chains, ' + FR14)}

AUFTRAEGE['wrack'] = {'ziel': 'assets/objekte/karte27/wrack', 'groesse': (320, 240),
    'vorlage': ('assets/objekte/karte25/schiff_a/00_sauber.png', (0, 0, 476, 282)),
    'stil': 'assets/objekte/karte25/leuchtturm/00.png',
    'text': ('crashed wreck of this dark emperor flagship lying on the ground, the hull broken and tilted, bow rammed into '
             'the earth, cracked black armour plates with gold trim, the castle-like bridge tower broken and leaning, red '
             'eye window dark and cracked, torn plates and jagged black debris sticking out, scorch marks, '
             'seen from the side as a flat 2D profile, no background, ' + FR14)}

# ---- Karte 30 Odaiba: grosse Gebaeude (> 256 px) nach der Vorlage, frontal mit Dach von leicht oben
_K30 = ('city building for a sunny bay-side district, daytime, seen from the front with the flat roof visible from slightly '
        'above, clean pixel art, light from the top left, no ground, no background, ')
_K30_STIL = 'assets/objekte/karte18/gebaeude/wohnblock.png'
for _n, _box, _t in (
        ('fernsehturm', (800, 0, 1280, 432), 'big futuristic TV station headquarters: two tall light grey towers with a grid '
         'of blue square windows, between them a lattice frame holding a large silver sphere, below a huge dark blue glass '
         'atrium with an entrance and a wide stone staircase in the middle leading down, '),
        ('buero_lang', (64, 256, 672, 496), 'long six-storey office building, beige cream facade with rows of small blue '
         'windows, a grey flat roof with a parapet, a glass ground floor with a central entrance door, '),
        ('buero_glas', (1408, 512, 1696, 720), 'modern office building with a blue glass curtain wall in horizontal bands, '
         'grey flat roof with parapet, glass entrance in the middle of the ground floor, '),
        ('laeden', (384, 896, 928, 1072), 'long two-storey shopping building, light grey and lavender facade with rows of '
         'warm yellow lit windows, flat grey roof, glass ground floor with two shop entrances with pink awnings, '),
        ('buero_flach', (1024, 896, 1504, 1072), 'long low modern office building with a blue glass curtain wall in four '
         'horizontal bands, flat grey roof with parapet, glass entrance on the ground floor, '),
        ('bahnhof', (48, 1120, 368, 1264), 'small elevated railway station building, light lavender facade, dark blue roof '
         'band, a sign board with the word ODAIBA and a round clock above the golden lit glass entrance, blue windows left '
         'and right, '),
        ('riesenrad', (1552, 688, 1824, 1056), 'big ferris wheel: a white steel ring with thin spokes from the hub, many '
         'small colourful round gondolas hanging around the ring, two white A-frame legs standing on the ground, '),
):
    AUFTRAEGE['k30_' + _n] = {'ziel': 'assets/objekte/karte30/gross_' + _n, 'groesse': (_box[2] - _box[0], _box[3] - _box[1]),
                             'vorlage': ('assets/vorlagen/karte30_vorlage.png', _box), 'stil': _K30_STIL,
                             'text': _t + _K30 + FR14}

_K30_STIL2 = 'assets/objekte/karte30/gross_buero_glas/00.png'                 # gut gelungenes Glasbuero als Stil
for _v in ('a', 'b'):
    AUFTRAEGE['k30_laeden_' + _v] = {
        'ziel': 'assets/objekte/karte30/gross_laeden_' + _v, 'groesse': (544, 176), 'magenta': True, 'stil': _K30_STIL2,
        'vorlage': ('assets/vorlagen/karte30_vorlage.png', (384, 896, 928, 1072)),
        'text': ('long two-storey shopping arcade building, clean crisp pixel art: a flat light grey roof with a parapet edge '
                 'visible from slightly above and a few small rooftop units, a light lavender grey facade with two even rows '
                 'of small windows (some warm yellow lit, most blue glass with white frames), a glass ground floor with dark '
                 'blue window bands and two shop entrances with pink awnings, daytime, sharp outlines, ' + _K30 + FR14)}
    AUFTRAEGE['k30_buero_flach_' + _v] = {
        'ziel': 'assets/objekte/karte30/gross_buero_flach_' + _v, 'groesse': (480, 176), 'magenta': True, 'stil': _K30_STIL2,
        'vorlage': ('assets/vorlagen/karte30_vorlage.png', (1024, 896, 1504, 1072)),
        'text': ('long low modern office building, clean crisp pixel art: a flat grey roof with a parapet edge visible from '
                 'slightly above, a facade of dark blue glass curtain wall in three even horizontal bands separated by light '
                 'grey concrete slabs, regular thin mullions, subtle sky reflections, a glass entrance with a small canopy on '
                 'the ground floor, daytime, sharp outlines, ' + _K30 + FR14)}

for _v in ('c', 'd'):                                                           # ganz im Bild (Nutzer): Leinwand mit Rand
    AUFTRAEGE['k30_laeden_' + _v] = dict(AUFTRAEGE['k30_laeden_a'], ziel='assets/objekte/karte30/gross_laeden_' + _v,
        groesse=(576, 240), vorlage=('assets/vorlagen/karte30_vorlage.png', (368, 848, 944, 1088)),
        text=AUFTRAEGE['k30_laeden_a']['text'] + ' The whole building is fully visible with empty margin around it, '
             'nothing cut off at the top or bottom, the ground floor base line is complete.')
    AUFTRAEGE['k30_buero_flach_' + _v] = dict(AUFTRAEGE['k30_buero_flach_a'], ziel='assets/objekte/karte30/gross_buero_flach_' + _v,
        groesse=(512, 240), vorlage=('assets/vorlagen/karte30_vorlage.png', (1008, 848, 1520, 1088)),
        text=AUFTRAEGE['k30_buero_flach_a']['text'] + ' The whole building is fully visible with empty margin around it, '
             'nothing cut off at the top or bottom, the ground floor base line is complete.')

for _v in ('e', 'f', 'g'):                                                      # Glasbuero mit sichtbaren Seiten (Nutzer)
    AUFTRAEGE['k30_buero_flach_' + _v] = dict(AUFTRAEGE['k30_buero_flach_a'], ziel='assets/objekte/karte30/gross_buero_flach_' + _v,
        groesse=(576, 256), vorlage=('assets/vorlagen/karte30_vorlage.png', (976, 832, 1552, 1088)),
        text=AUFTRAEGE['k30_buero_flach_a']['text'] + ' The building is about 480 pixels wide and centered, with a wide '
             'empty magenta margin on the left, right, top and bottom; both side walls and all four roof corners are '
             'complete and visible, the roof edge wraps around the corners, nothing touches the image border.')

for _v in 'hijklm':                                                             # neu, unbearbeitet (Nutzer): Karte passt sich an
    AUFTRAEGE['k30_buero_flach_' + _v] = dict(AUFTRAEGE['k30_buero_flach_a'], ziel='assets/objekte/karte30/gross_buero_flach_' + _v,
        groesse=(608, 288), vorlage=('assets/vorlagen/karte30_vorlage.png', (960, 816, 1568, 1104)),
        text=('long low modern office building, clean crisp pixel art, centered in the image with a wide empty magenta '
              'margin on all four sides (about 50 pixels left and right, 40 pixels top and bottom), nothing touches the image '
              'border. Flat grey roof with a parapet visible from slightly above, the roof edge wraps cleanly around all four '
              'corners. Both side walls are clearly visible as solid light concrete corner pillars from the roof down to the '
              'ground with a dark outline. Facade of dark blue glass curtain wall in three even horizontal bands between light '
              'grey concrete floor slabs that end flush at the corner pillars, regular thin mullions, a glass entrance with a '
              'small canopy in the middle of the ground floor, complete base line at the bottom, daytime, sharp outlines, '
              + _K30 + FR14))

for _v in 'nopqrs':                                                             # tieferes Dach (Nutzer: oben wirkte gekappt)
    AUFTRAEGE['k30_buero_flach_' + _v] = dict(AUFTRAEGE['k30_buero_flach_a'], ziel='assets/objekte/karte30/gross_buero_flach_' + _v,
        groesse=(560, 288), vorlage=None,
        text=('long low modern four-storey office building, clean crisp pixel art, top-down RPG view from the front and '
              'slightly above, so that a DEEP flat grey rooftop is clearly visible above the facade (the roof surface is about '
              'one third of the building height, with a parapet edge all around, rooftop air conditioning units, a small '
              'stairwell box and pipes). Below the roof: a facade of dark blue glass curtain wall in three even horizontal '
              'bands between light grey concrete floor slabs, light concrete corner pillars on both sides from the roof down '
              'to the ground, a glass entrance with a small canopy in the middle of the ground floor, a dark grey base plinth '
              'at the bottom. The building is about 460 pixels wide, centered, with a wide empty magenta margin on all four '
              'sides, nothing touches the image border, daytime, sharp outlines, ' + _K30 + FR14))

# ---- Karte 31 Highton View Terrace (Nutzer: Haelften generieren und spiegeln, wo moeglich)
_K31 = ('Japanese residential district building, daytime, seen from the front with the flat roof visible from slightly '
        'above, clean crisp pixel art, light from the top left, sharp dark outlines, ')
_K31_STIL = 'assets/objekte/karte30/gross_buero_flach_s/00.png'
_HALB = (' This is only the LEFT HALF of a long symmetric building: the left end wall, roof corner and base are complete, '
         'the building continues straight beyond the RIGHT image border (the right side is cut exactly through the middle '
         'of the facade, no wall there). Wide empty magenta margin on the left, top and bottom.')
_VOLL = ' The whole building is fully visible, centered, with a wide empty magenta margin on all four sides, nothing touches the image border.'
for _n, _box, _gr, _t in (
        ('block_grau_halb', (48, 560, 336, 816), (288, 256), 'long five-storey grey concrete apartment block (danchi): '
         'light grey facade with rows of balconies, some with laundry and boxes, dark blue windows, a stairwell tower '
         'rising above the flat grey roof with rooftop water tanks and air units, entrance doors at the bottom, ' + _HALB),
        ('block_beige_halb', (1072, 560, 1424, 816), (352, 256), 'long five-storey beige apartment block (danchi): warm '
         'beige facade with rows of balconies with railings, some laundry, dark blue windows, a stairwell tower rising above '
         'the flat grey roof with rooftop air units, entrance doors at the bottom, ' + _HALB),
        ('turm', (688, 576, 816, 1184), (160, 640), 'tall narrow grey concrete apartment tower seen from above and the '
         'front: a very long flat grey rooftop stretching far up with two small rooftop units, at the bottom the front '
         'facade with a few small windows, a building number sign and a door, ' + _VOLL),
        ('bahnhof', (0, 1184, 464, 1360), (480, 208), 'small suburban train station building with a dark green roof band, '
         'light facade with a sign board reading HIGHTON and a round clock, blue windows and a glass entrance in the middle, '
         'light grey platform edge, ' + _VOLL),
        ('bruecke', (720, 1200, 1200, 1344), (512, 176), 'pedestrian overpass footbridge: a long straight walkway with teal '
         'green railings and a small sign in the middle, supported by grey pillars, with a staircase going down at the '
         'left end and at the right end, ' + _VOLL),
):
    AUFTRAEGE['k31_' + _n] = {'ziel': 'assets/objekte/karte31/gross_' + _n, 'groesse': _gr, 'magenta': True,
                             'vorlage': ('assets/vorlagen/karte31_vorlage.png', _box), 'stil': _K31_STIL,
                             'text': _t + _K31 + FR14}

for _v in ('b', 'c'):                                                           # Breite passend zur Vorlage
    AUFTRAEGE['k31_bahnhof_' + _v] = dict(AUFTRAEGE['k31_bahnhof'], ziel='assets/objekte/karte31/gross_bahnhof_' + _v,
        groesse=(384, 192), vorlage=('assets/vorlagen/karte31_vorlage.png', (112, 1200, 464, 1360)),
        text=AUFTRAEGE['k31_bahnhof']['text'].replace(_VOLL, '') + ' The building is exactly about 320 pixels wide and '
             '96 pixels tall, centered, with a wide empty magenta margin on all four sides, nothing touches the image border.')
    AUFTRAEGE['k31_bruecke_' + _v] = dict(AUFTRAEGE['k31_bruecke'], ziel='assets/objekte/karte31/gross_bruecke_' + _v,
        groesse=(512, 176), text=AUFTRAEGE['k31_bruecke']['text'].replace(_VOLL, '') + ' The whole bridge including both '
             'staircases is about 440 pixels wide, centered, with a wide empty magenta margin on all four sides.')

# ---- A03 Karte 35 Shinjuku Digital Fog: grosse Gebaeude (> 256 px) nach der Vorlage (Nutzer-Ausnahme Karte 25)
_K35 = ('Tokyo Shinjuku office district building, evening, seen from the front with the flat roof visible from slightly '
        'above, clean crisp pixel art, light from the top left, sharp dark outlines, ')
_K35_STIL = 'assets/objekte/karte30/gross_buero_flach_s/00.png'
_V35 = 'assets/vorlagen/karte35_vorlage.png'
for _n, _box, _gr, _t in (
        ('turm', (46, 29, 238, 368), (224, 384), 'tall slim glass office tower: a light grey flat roof band with a small '
         'rooftop air conditioning unit and a parapet visible from slightly above, below it a tall facade of dark blue glass '
         'curtain wall in many even horizontal floor bands with thin light grey mullions, light concrete corner pillars on both '
         'sides, a glass lobby with a double entrance door in the middle of the ground floor, grey base plinth, ' + _VOLL),
        ('buero_oben_halb', (504, 37, 856, 135), (400, 176), 'very long low glass office building: a deep light grey flat '
         'roof with a parapet and two rooftop air conditioning units visible from slightly above, a facade of one tall band '
         'of dark blue glass windows with thin mullions, light concrete end pillar, ' + _HALB),
        ('buero_mitte', (720, 420, 1100, 555), (416, 192), 'long low glass office building: a light grey flat roof with a '
         'parapet and a rooftop air conditioning unit visible from slightly above, a facade of dark blue glass curtain wall in '
         'two even horizontal bands, light concrete corner pillars on both sides, a glass entrance in the middle of the '
         'ground floor, grey base plinth, ' + _VOLL),
        ('buero_unten_halb', (680, 1080, 935, 1240), (320, 224), 'long three-storey glass office building: a light grey flat '
         'roof with a parapet and two rooftop air conditioning units visible from slightly above, a facade of dark blue glass '
         'curtain wall in three even horizontal bands, light concrete end pillar, grey base plinth, ' + _HALB),
):
    AUFTRAEGE['k35_' + _n] = {'ziel': 'assets/objekte/karte35/gross_' + _n, 'groesse': _gr, 'magenta': True,
                             'vorlage': (_V35, _box), 'stil': _K35_STIL, 'text': _t + _K35 + FR14}

for _v in ('b', 'c'):                                                           # Turm mit Rand, ohne Boden (Pruefung)
    AUFTRAEGE['k35_turm_' + _v] = dict(AUFTRAEGE['k35_turm'], ziel='assets/objekte/karte35/gross_turm_' + _v,
        groesse=(256, 400), text=AUFTRAEGE['k35_turm']['text'].replace(_VOLL, '') + ' The tower is exactly about 160 '
        'pixels wide and 310 pixels tall, centered, with a wide empty magenta margin of at least 40 pixels on all four '
        'sides: the complete flat roof with its parapet and all corners is visible at the top, the grey base plinth ends '
        'cleanly at the bottom, NO pavement, NO ground, NO sidewalk tiles, nothing touches the image border.')

for _v in ('b', 'c'):                                                           # Glasbuero Mitte vollstaendig (Nutzer: Kanten)
    AUFTRAEGE['k35_buero_mitte_' + _v] = dict(AUFTRAEGE['k35_buero_mitte'], ziel='assets/objekte/karte35/gross_buero_mitte_' + _v,
        groesse=(480, 256), text=AUFTRAEGE['k35_buero_mitte']['text'].replace(_VOLL, '') + ' The building is about 380 '
        'pixels wide and 160 pixels tall, centered, with a wide empty magenta margin of at least 40 pixels on all four '
        'sides: both light concrete corner pillars are complete with their dark outline on the outer side, the roof eave '
        'wraps cleanly around both upper corners, the base plinth ends cleanly at both sides, nothing touches the image border.')

for _v in ('d', 'e'):                                                           # kleiner: passt zwischen Bruecke und Strasse
    AUFTRAEGE['k35_buero_mitte_' + _v] = dict(AUFTRAEGE['k35_buero_mitte'], ziel='assets/objekte/karte35/gross_buero_mitte_' + _v,
        groesse=(416, 224), text=AUFTRAEGE['k35_buero_mitte']['text'].replace(_VOLL, '') + ' A compact two-storey '
        'building, about 340 pixels wide and only 130 pixels tall (low and wide), centered, with a wide empty magenta '
        'margin of at least 36 pixels on all four sides: both light concrete corner pillars are complete with their dark '
        'outline on the outer side, the roof eave wraps cleanly around both upper corners, the base plinth ends cleanly '
        'at both sides, nothing touches the image border.')

for _v in ('f', 'g'):                                                           # Leinwand 456: fuellt fast ganz -> ~450 px breit
    AUFTRAEGE['k35_buero_mitte_' + _v] = dict(AUFTRAEGE['k35_buero_mitte_b'], ziel='assets/objekte/karte35/gross_buero_mitte_' + _v,
        groesse=(456, 200))

# ---- A03 Karte 36 Shinjuku Backstreets: lange Gebaeude als linke Haelfte (gespiegelt auf Vorlagenbreite)
_K36 = ('Tokyo Shinjuku backstreet building, daytime, seen from the front with the flat roof visible from slightly above, '
        'clean crisp pixel art, light from the top left, sharp dark outlines, ')
_V36 = 'assets/vorlagen/karte36_vorlage.png'
for _n, _box, _gr, _t in (
        ('beige_halb_hoch', (60, 40, 300, 232), (288, 176), 'long four-storey Japanese apartment and office block: a light '
         'grey flat roof band with a parapet and one rooftop air conditioning unit, a warm beige facade with three even rows of '
         'tall narrow windows with white frames, a dark blue glass ground floor shop front, light end pillar, ' + _HALB),
        ('beige_halb_flach', (60, 444, 240, 592), (288, 144), 'long three-storey Japanese apartment block: a light grey flat '
         'roof band with a parapet and a rooftop unit, a warm beige facade with two even rows of tall narrow windows with white '
         'frames, a dark blue glass ground floor shop front, light end pillar, ' + _HALB),
        ('lila_halb', (650, 40, 800, 195), (160, 144), 'three-storey Japanese apartment building: a light grey flat roof band '
         'with a parapet and a rooftop unit, a soft lavender facade with two rows of narrow windows with white frames, a dark '
         'blue glass ground floor, light end pillar, ' + _HALB),
        ('flach_halb', (108, 860, 256, 945), (160, 96), 'low one-storey Japanese shop building: a light grey flat roof band '
         'with a parapet and a rooftop unit visible from slightly above, a dark blue glass shop front with thin mullions, '
         'light end pillar, ' + _HALB),
):
    AUFTRAEGE['k36_' + _n] = {'ziel': 'assets/objekte/karte36/gross_' + _n, 'groesse': _gr, 'magenta': True,
                             'vorlage': (_V36, _box), 'stil': 'assets/objekte/karte35/wohnblock_b/00.png',
                             'text': _t + _K36 + FR14}

for _n, _gr in (('beige_halb_hoch', (288, 232)), ('beige_halb_flach', (288, 200))):   # hoehere Leinwand (angeschnitten)
    AUFTRAEGE['k36_' + _n + '_b'] = dict(AUFTRAEGE['k36_' + _n], ziel='assets/objekte/karte36/gross_' + _n + '_b',
        groesse=_gr, text=AUFTRAEGE['k36_' + _n]['text'] + ' The complete roof edge is visible at the top and the complete '
        'grey base plinth at the bottom, with empty magenta space above the roof and below the base.')

AUFTRAEGE['k36_lila_halb_b'] = dict(AUFTRAEGE['k36_lila_halb'], ziel='assets/objekte/karte36/gross_lila_halb_b',
    groesse=(160, 200), text=AUFTRAEGE['k36_lila_halb']['text'] + ' The complete roof edge is visible at the top and the '
    'complete grey base plinth at the bottom, with empty magenta space above the roof and below the base.')

# ---- A03 Karte 39 West Shinjuku Siege
_V39 = 'assets/vorlagen/karte39_vorlage.png'
AUFTRAEGE['k39_turm'] = {'ziel': 'assets/objekte/karte39/gross_turm', 'groesse': (240, 512), 'magenta': True,
    'vorlage': (_V39, (1320, 300, 1500, 740)), 'stil': 'assets/objekte/karte35/wohnblock_b/00.png',
    'text': 'tall modern Tokyo glass office tower, about 165 pixels wide and 430 pixels tall, centered with an empty '
            'magenta margin of at least 30 pixels on all sides: a light grey flat roof with a parapet and one rooftop '
            'unit visible from slightly above at the top, ten storeys of dark steel-blue glass window bands with light '
            'concrete floor slabs and corner pillars, a two-storey lobby at the bottom with a lavender band and a glass '
            'entrance door in the middle, grey base plinth, daytime, clean crisp pixel art, light from the top left, '
            'sharp dark outlines, both corner pillars complete with dark outline, nothing touches the image border, ' + FR14}
AUFTRAEGE['k39_bruecke'] = {'ziel': 'assets/objekte/karte39/gross_bruecke', 'groesse': (512, 176), 'magenta': True,
    'vorlage': (_V39, (232, 570, 700, 700)), 'stil': 'assets/objekte/karte35/bruecke_a/00.png',
    'text': 'long Japanese pedestrian overpass seen from the side and slightly above, about 450 pixels wide and 110 '
            'pixels tall, centered with an empty magenta margin of at least 24 pixels on all sides: a straight flat deck '
            'with teal steel railings in the middle on four slim grey pillars, a small white sign in the middle of the '
            'deck, a long diagonal staircase with teal railings going down at the left end and another one at the '
            'right end, light grey deck surface, clean crisp pixel art, light from the top left, sharp dark outlines, '
            'NO road, NO ground, nothing touches the image border, ' + FR14}

for _v, _gr in (('', (176, 144)), ('_b', (176, 160))):
    AUFTRAEGE['k39_beige_flach_halb' + _v] = {'ziel': 'assets/objekte/karte39/gross_beige_flach_halb' + _v, 'groesse': _gr,
        'magenta': True, 'vorlage': (_V39, (1150, 60, 1300, 186)), 'stil': 'assets/objekte/karte35/wohnblock_b/00.png',
        'text': 'long two-storey Tokyo office building: a light grey flat roof band with a parapet and one small rooftop '
                'unit visible from slightly above, an upper floor with a warm beige facade and a row of tall narrow windows '
                'with white frames, a dark blue glass ground floor shop front with thin mullions, light end pillar, '
                + _HALB + ' Tokyo daytime, clean crisp pixel art, light from the top left, sharp dark outlines, The '
                'complete roof edge is visible at the top and the complete grey base plinth at the bottom, with empty '
                'magenta space above the roof and below the base, ' + FR14}

AUFTRAEGE['k39_bruecke_b'] = dict(AUFTRAEGE['k39_bruecke'], ziel='assets/objekte/karte39/gross_bruecke_b',
    text='modern Tokyo pedestrian footbridge over a road, seen from the front and slightly above: a long straight walkway '
         'deck with light grey concrete sides and a glass-and-steel railing on top, a small blue station sign in the '
         'middle, the deck rests on two pairs of round concrete columns, at both ends a straight staircase descends '
         'diagonally to the ground with its own railing, about 450 pixels wide and 110 pixels tall, centered with an '
         'empty magenta margin of at least 24 pixels on all sides, clean crisp pixel art, light from the top left, '
         'sharp dark outlines, NO road, NO ground, nothing touches the image border, ' + FR14)
AUFTRAEGE['k39_bruecke_c'] = dict(AUFTRAEGE['k39_bruecke'], ziel='assets/objekte/karte39/gross_bruecke_c',
    text='Japanese elevated pedestrian bridge with a dark green steel truss railing and a light grey deck, seen from '
         'the side and slightly above, flat middle span on four slim steel legs, long stairs going down at the left and '
         'right ends parallel to the deck, a small name plate in the middle, about 450 pixels wide and 110 pixels tall, '
         'centered with an empty magenta margin of at least 24 pixels on all sides, clean crisp pixel art, light from '
         'the top left, sharp dark outlines, NO road, NO ground, nothing touches the image border, ' + FR14)
AUFTRAEGE['k39_turm_b'] = dict(AUFTRAEGE['k39_turm'], ziel='assets/objekte/karte39/gross_turm_b',
    text='tall modern Tokyo office skyscraper seen from the front with the flat roof visible from slightly above, about '
         '160 pixels wide and 410 pixels tall, centered with an empty magenta margin of at least 30 pixels on all sides: '
         'light beige stone frame with a regular grid of blue reflective windows, a rooftop with a parapet, helipad '
         'marking and antenna, a glass lobby with a revolving door at the bottom, grey base plinth, daytime, clean crisp '
         'pixel art, light from the top left, sharp dark outlines, both side walls complete with dark outline, nothing '
         'touches the image border, ' + FR14)
AUFTRAEGE['k39_turm_c'] = dict(AUFTRAEGE['k39_turm'], ziel='assets/objekte/karte39/gross_turm_c',
    text='slender modern glass office tower in West Shinjuku seen from the front with the roof visible from slightly '
         'above, about 160 pixels wide and 410 pixels tall, centered with an empty magenta margin of at least 30 pixels on '
         'all sides: teal-blue glass curtain wall with thin silver vertical mullions, a stepped crown at the top with '
         'rooftop equipment, a two-storey stone podium with a wide glass entrance at the bottom, grey base, daytime, clean '
         'crisp pixel art, light from the top left, sharp dark outlines, nothing touches the image border, ' + FR14)

_BR = (' about 450 pixels wide, centered with an empty magenta margin of at least 24 pixels on all sides, clean crisp pixel '
       'art matching a top-down Japanese city RPG map, light from the top left, sharp dark outlines, NO road, NO ground, '
       'nothing touches the image border, ')
AUFTRAEGE['k39_bruecke_d'] = dict(AUFTRAEGE['k39_bruecke'], ziel='assets/objekte/karte39/gross_bruecke_d',
    groesse=(512, 192), text='Japanese pedestrian overpass seen from above in a top-down RPG view: a straight light grey '
         'walkway deck crossing horizontally with teal steel railings on both long sides, at each end the deck turns into '
         'a staircase that goes down towards the viewer, grey square columns visible under the deck,' + _BR + FR14)
AUFTRAEGE['k39_bruecke_e'] = dict(AUFTRAEGE['k39_bruecke'], ziel='assets/objekte/karte39/gross_bruecke_e',
    text='modern Shinjuku pedestrian bridge seen from the front and slightly above: a long horizontal walkway with a light '
         'grey floor, a teal-green steel frame and light blue glass panels as railing, a small sign in the middle, two '
         'pairs of slim teal columns, at both ends a straight staircase with teal railings goes diagonally down to the '
         'ground, about 110 pixels tall,' + _BR + FR14)
AUFTRAEGE['k39_bruecke_f'] = dict(AUFTRAEGE['k39_bruecke'], ziel='assets/objekte/karte39/gross_bruecke_f',
    text='wide modern concrete pedestrian deck bridge seen from the front and slightly above: a broad light concrete '
         'walkway with low parapet walls, small planters with green shrubs along the parapet, two thick rectangular '
         'concrete piers, gentle ramps with railings down to the ground at both ends, about 110 pixels tall,' + _BR + FR14)


def main(name):
    a = AUFTRAEGE[name]
    w, h = a['groesse']
    v = None
    if a.get('vorlage'):
        pf, box = a['vorlage']
        v = Image.open(os.path.join(ROOT, pf)).convert('RGB').crop(box)
        d = ImageDraw.Draw(v)
        for (x0, y0, x1, y1) in a.get('uebermalen', []):
            d.rectangle((x0 - box[0], y0 - box[1], x1 - box[0], y1 - box[1]), fill=(46, 46, 58))
    stil = Image.open(os.path.join(ROOT, a['stil'])).convert('RGBA')
    magenta = a.get('magenta', False)                                # Hintergrund selbst freistellen (helle Scheiben bleiben)
    req = {'description': a['text'] + (' The building stands on a plain flat solid magenta (#ff00ff) background.' if magenta else ''),
           'image_size': {'width': w, 'height': h}, 'no_background': not magenta,
           'style_image': ref(stil), 'style_options': {'color_palette': False, 'outline': True, 'detail': True}}
    if v is not None:
        req['reference_images'] = [ref(v, 'subject and layout of the ship: shape, proportions, towers, colours')]
    r = call('POST', '/v2/generate-image-v2', req)
    jid = r['background_job_id']
    print(name, 'Auftrag', jid)
    for _ in range(90):
        time.sleep(10)
        try:
            j = call('GET', '/v2/background-jobs/%s' % jid)
        except urllib.error.HTTPError:
            continue
        if j.get('status') == 'completed':
            break
        if j.get('status') == 'failed':
            raise SystemExit('fehlgeschlagen: %s' % json.dumps(j)[:500])
    else:
        raise SystemExit('Timeout')
    ziel = os.path.join(ROOT, a['ziel'])
    os.makedirs(ziel, exist_ok=True)
    json.dump(j, open(os.path.join(ziel, 'antwort.json'), 'w'), indent=1, default=str)
    lr = j.get('last_response') or {}
    bilder = lr.get('images') or lr.get('image') or []
    if isinstance(bilder, dict):
        bilder = [bilder]
    n = 0
    for i, b in enumerate(bilder):
        data = b.get('base64') if isinstance(b, dict) else b
        if not data:
            continue
        im = Image.open(io.BytesIO(base64.b64decode(data))).convert('RGBA')
        if magenta:
            import numpy as np
            from collections import deque
            ar = np.array(im).astype(int)
            mg = (ar[..., 0] > 170) & (ar[..., 2] > 170) & (ar[..., 1] < 110)          # magentafarbene Pixel
            hh, ww = mg.shape                                                           # nur vom Rand her erreichbares
            weg = np.zeros_like(mg); q = deque()                                        # Magenta ist Hintergrund
            for yy in range(hh):
                for xx in (0, ww - 1):
                    if mg[yy, xx] and not weg[yy, xx]:
                        weg[yy, xx] = True; q.append((yy, xx))
            for xx in range(ww):
                for yy in (0, hh - 1):
                    if mg[yy, xx] and not weg[yy, xx]:
                        weg[yy, xx] = True; q.append((yy, xx))
            while q:
                yy, xx = q.popleft()
                for y2, x2 in ((yy - 1, xx), (yy + 1, xx), (yy, xx - 1), (yy, xx + 1)):
                    if 0 <= y2 < hh and 0 <= x2 < ww and mg[y2, x2] and not weg[y2, x2]:
                        weg[y2, x2] = True; q.append((y2, x2))
            rand = ~weg & (np.roll(weg, 1, 0) | np.roll(weg, -1, 0) | np.roll(weg, 1, 1) | np.roll(weg, -1, 1))
            ar[weg, 3] = 0
            saum = rand & (ar[..., 0] > 140) & (ar[..., 2] > 140) & (ar[..., 1] < ar[..., 0] - 40)   # Magenta-Saum weg
            ar[saum, 3] = 0
            im = Image.fromarray(ar.astype(np.uint8))
        im.save(os.path.join(ziel, '%02d.png' % i)); n += 1
    if v is not None:
        v.save(os.path.join(ziel, 'referenz.png'))
    print(name, '%d Bild(er) ->' % n, a['ziel'])


if __name__ == '__main__':
    main(sys.argv[1])
