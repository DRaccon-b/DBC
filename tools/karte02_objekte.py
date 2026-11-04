"""Objekte fuer Karte 02 (Factorial Town): feste Positionen aus der Vorlage + verstreute Kleinteile.

  python3 tools/karte02_objekte.py && python3 tools/karte02_bauen.py

Sprites: assets/objekte/karte02/<gruppe>/NN.png (PixelLab-Objekt-Manager, tools/pixellab_objekte.py,
Gruppen k2_*), prozedurale Sprites (Container, Portalkran, Laterne) in assets/objekte/karte02/abgeleitet/.
Jedes Objekt bekommt einen Bodenfuss passend zum Untergrund (Beton/Metall: Kontaktschatten und
Schmutz, Gras: Halme). Verstreute Objekte nur mit Pixel-Kollision und auf freiem Beton.
Animationsarten: feuer, rauch, reaktor, blinken, laterne (siehe animieren()).
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import industrie as ind
import bauwerke

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte02')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte02')
T = 16

# Art fuer den Bodenfuss (bauwerke.bodenfuss)
FUSS = {'klein': 'klein', 'mini': 'klein', 'mittel': 'stein', 'ortho': 'stein', 'hoch': 'stein',
        'turm': 'stein', 'reaktor': 'stein', 'abgeleitet': 'stein'}

# Feste Objekte: (sprite, Anker-x in Kacheln (Mitte), Anker-y = unterste Kachelzeile, Optionen)
KRAN_WEG = 26                                   # Fahrweg der Katze nach links/rechts (px)
FEST = [
    # Containerlager oben links (hinten zuerst)
    ('C:rot:0', 5.5, 6, {}), ('C:blau:1', 5.5, 8, {}), ('C:orange:0', 10.5, 8, {}),
    ('C:gruen:0', 24.5, 6, {}), ('C:orange:1', 24.5, 8, {}),
    ('C:blau:0', 6.5, 15, {}), ('C:gruen:1', 6.5, 19, {}),
    ('KRAN', 18.5, 21, {'anim': 'kran'}),
    ('klein/11', 10, 19, {}),                              # Gabelstapler
    ('ortho/00', 20, 26, {}),                              # LKW
    ('klein/12', 26, 15, {}), ('klein/12', 26, 44, {}),    # Kabeltrommeln
    # Fabrikhof: Pressen ueber den Foerderbaendern, Roboterarme
    ('mittel/10', 33, 15, {'anim': 'portal'}), ('mittel/10', 43, 15, {'anim': 'portal'}),
    ('mittel/10', 53, 15, {'anim': 'portal'}),
    ('klein/09', 36, 12, {'anim': 'greifarm'}), ('klein/10', 30, 19, {'anim': 'greifarm'}),
    ('klein/09', 46, 12, {'anim': 'greifarm'}), ('klein/10', 40, 19, {'anim': 'greifarm'}),
    ('klein/09', 56, 12, {'anim': 'greifarm'}), ('klein/10', 50, 19, {'anim': 'greifarm'}),
    ('klein/09', 56.5, 21, {'anim': 'greifarm'}),
    ('klein/08', 37.5, 29, {}), ('klein/08', 43.5, 29, {}),
    ('klein/24', 54, 25, {}),
    # Tanklager oben rechts
    ('ortho/03', 64, 9, {}), ('ortho/04', 69, 9, {}), ('hoch/00', 73.5, 9, {}), ('hoch/03', 78.5, 9, {}),
    ('hoch/01', 83.5, 9, {'anim': 'rauch', 'rauch': [0.5, 0.03]}),
    ('ortho/05', 87, 9, {}), ('ortho/15', 90.5, 9, {}),
    # Reaktor mit Pylonen und Generatoren
    ('reaktor/00', 75.5, 31, {'anim': 'reaktor'}),
    ('turm/03', 67.5, 30, {'anim': 'reaktor'}), ('turm/03', 83.5, 30, {'anim': 'reaktor'}),
    ('mittel/00', 67, 38, {'anim': 'reaktor'}), ('mittel/01', 84.5, 38, {'anim': 'reaktor'}),
    ('mittel/00', 66.5, 50, {'anim': 'reaktor'}), ('mittel/01', 85, 50, {'anim': 'reaktor'}),
    # Platz links und Strasse
    ('hoch/02', 4.6, 34, {'anim': 'blinken'}), ('hoch/02', 4.6, 46, {'anim': 'blinken'}),
    ('ortho/09', 8, 34, {}), ('klein/22', 5.5, 33, {}),
    ('ortho/01', 21, 44, {}),                               # zweiter LKW
    ('klein/11', 5, 61, {}),
    ('mini/04', 13.5, 59, {}), ('mini/04', 14.5, 59, {}), ('mini/24', 9.5, 63, {}),
    # Werkstatt unten: Oefen, Hochoefen, Schornsteine, Schrott
    ('mittel/03', 31, 54, {'anim': 'feuer', 'rauch': [0.5, 0.0]}), ('mittel/02', 47, 58, {'anim': 'feuer', 'rauch': [0.5, 0.0]}),
    ('turm/01', 39, 69, {'anim': 'feuer'}), ('abgeleitet/hochofen', 51.5, 71, {'anim': 'feuer', 'rauch': [0.5, 0.0]}),
    ('hoch/01', 44.5, 71, {'anim': 'rauch', 'rauch': [0.5, 0.03]}), ('hoch/01', 33.5, 67, {'anim': 'rauch', 'rauch': [0.5, 0.03]}),
    ('hoch/01', 47.5, 44, {'anim': 'rauch', 'rauch': [0.5, 0.03]}),   # Schornstein auf dem Backsteinhaus
    ('mittel/05', 30.5, 71, {}),
    # Schrottplatz unten rechts
    ('mittel/04', 64.5, 70, {}), ('mittel/06', 68.5, 71, {}), ('mittel/05', 78, 71, {}),
    ('mittel/07', 71.5, 64, {}), ('mittel/08', 74, 70, {}), ('ortho/06', 83, 68, {}), ('mittel/11', 77, 64, {}),
    # Containerlager unten links
    ('C:orange:1', 15.5, 64, {}), ('C:gruen:0', 20.5, 62, {}), ('C:orange:0', 20.5, 64, {}),
    ('C:gruen:1', 5.5, 69, {}), ('C:orange:1', 5.5, 71, {}), ('C:rot:1', 10.5, 71, {}),
    ('ortho/12', 30, 64, {}),
]
# Hochspannungsleitung: Masten an der Ostmauer (Anker-Kachel), Leitung vom rechten Reaktor-Pylon
MASTEN = [(91, 18), (91, 31), (91, 45), (91, 58), (91, 70)]
# Warnschilder (Dreieck mit !) an Gefahrenstellen
SCHILDER = [(12, 22), (26, 11), (29, 56), (49, 60), (41, 70), (54, 70), (79, 69),
            (62, 10), (25, 46), (24, 61), (58, 26), (70, 62)]
LATERNEN = [(16, 34), (24, 34), (32, 34), (40, 34), (49, 34), (56, 34), (18, 41), (26, 41), (34, 41), (45, 41), (7, 41),
            # Hoefe: Containerlager, Fabrikhof, Werkstatt, Tanklager, Reaktorplatz-Rand, unten links
            (12, 11), (27, 21), (30, 25), (46, 27), (57, 25), (36, 51), (58, 51), (28, 61), (59, 66),
            (61, 13), (88, 13), (17, 67), (9, 57), (65, 59), (86, 63)]
# Kleinteile, die verstreut werden (Gruppe mini; Nummern werden nach Sichtung eingetragen)
STREU = ['mini/00', 'mini/01', 'mini/02', 'mini/03', 'mini/15', 'mini/00', 'mini/01', 'mini/04', 'mini/10',
         'mini/09', 'mini/14', 'mini/08', 'mini/11', 'mini/12', 'mini/55', 'mini/63', 'mini/13', 'mini/17',
         'mini/26', 'mini/29', 'mini/25', 'mini/50', 'mini/53', 'mini/36', 'mini/37', 'mini/32', 'mini/19',
         'mini/16', 'mini/35', 'mini/42']


# Farben, die animiert werden und deshalb beim Farbabgleich unveraendert bleiben muessen
SCHUTZ = {(0xc8, 0x3a, 0x1e), (0xe8, 0x70, 0x2a), (0xf5, 0xb0, 0x42), (0xff, 0xf2, 0xa0),
          (0x2f, 0x8f, 0x5a), (0x4f, 0xd0, 0x7a), (0x9a, 0xf5, 0xb0), (0x2f, 0xc7, 0xd8), (0x7f, 0xf0, 0xf5),
          (0xe6, 0xff, 0xff)}
UMGEBUNG = (125, 136, 144)                      # mittleres Beton-Grau der Karte


def harmonisieren(im, entsaettigen=0.14, mischen=0.07, boden_ao=0.18):
    """Objekt an die Szene angleichen: etwas weniger Saettigung, leicht zur Umgebungsfarbe gemischt,
    unten etwas dunkler (Umgebungsverdeckung). Animierte Leuchtfarben bleiben exakt erhalten."""
    a = np.array(im.convert('RGBA')).astype(np.float32)
    rgb_ = a[..., :3]
    schutz = np.zeros(a.shape[:2], bool)
    for c in SCHUTZ:
        schutz |= (np.abs(rgb_ - np.array(c)) < 0.5).all(axis=2)
    grau = rgb_.mean(axis=2, keepdims=True)
    neu = rgb_ + (grau - rgb_) * entsaettigen
    neu = neu * (1 - mischen) + np.array(UMGEBUNG) * mischen
    h = a.shape[0]
    zeilen = np.nonzero((a[..., 3] > 0).any(axis=1))[0]
    if len(zeilen):
        y0, y1 = zeilen.min(), zeilen.max()
        hoehe = max(1, y1 - y0)
        t = np.clip((np.arange(h) - (y1 - hoehe * 0.25)) / (hoehe * 0.25), 0, 1)[:, None, None]
        neu = neu * (1 - boden_ao * t)
    a[..., :3] = np.where(schutz[..., None], rgb_, np.clip(neu, 0, 255))
    return Image.fromarray(a.astype(np.uint8))


def lade(name, cache={}):
    if name not in cache:
        cache[name] = Image.open(os.path.join(OBJ, name + '.png')).convert('RGBA')
    return cache[name]


def prozedural():
    """Container-, Kran- und Laternen-Sprites erzeugen (abgeleitet/)."""
    os.makedirs(os.path.join(OBJ, 'abgeleitet'), exist_ok=True)
    for f in ind.CONTAINER:
        for v in (0, 1):
            ind.container_sprite(f, v).save(os.path.join(OBJ, 'abgeleitet', 'container_%s_%d.png' % (f, v)))
    ind.kran_sprite(176, 144, ind.container_sprite('rot', 1)).save(os.path.join(OBJ, 'abgeleitet', 'kran.png'))
    for f in range(16):                         # Animation: Katze faehrt mit dem Container hin und her
        dx = round(KRAN_WEG * math.sin(2 * math.pi * f / 16))
        ind.kran_sprite(176, 144, ind.container_sprite('rot', 1), dx).save(
            os.path.join(OBJ, 'abgeleitet', 'kran_f%02d.png' % f))
    bauwerke.laterne_bild().save(os.path.join(OBJ, 'abgeleitet', 'laterne.png'))
    mast, punkte = ind.strommast_sprite()
    mast.save(os.path.join(OBJ, 'abgeleitet', 'strommast.png'))
    json.dump(punkte, open(os.path.join(OBJ, 'abgeleitet', 'strommast_punkte.json'), 'w'))
    # Hochofen ohne den seitlich angeklebten Steinhaufen und ohne eingezeichneten Rauch
    ho = Image.open(os.path.join(OBJ, 'turm', '00.png')).convert('RGBA')
    hp = ho.load()
    for y in range(ho.height):
        for x in range(ho.width):
            if x >= 60 or y < 8:
                hp[x, y] = (0, 0, 0, 0)
    ho.crop(ho.getbbox()).save(os.path.join(OBJ, 'abgeleitet', 'hochofen.png'))


def main():
    prozedural()
    rnd = random.Random(7)
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    tm = json.load(open(os.path.join(KARTE, 'tilemap.json')))
    cls = tm['klassen']
    cols, rows = lay['groesse']
    MW, MH = cols * T, rows * T
    b = np.array(Image.open(os.path.join(KARTE, 'terrain_basis.png')).convert('RGB')).astype(np.int16)
    gras_maske = (b[..., 1] > b[..., 0] + 25) & (b[..., 1] > b[..., 2] + 25)

    # Bauwerke: Gebaeude, Mauern, Schienen, Baender, Rohre, Strasse -> fuer Streuobjekte tabu
    bau = np.zeros((MH, MW), bool)
    for g in lay['gebaeude'] + lay['mauern']:
        x0, y0, x1, y1 = g['r']
        bau[y0 * T:(y1 + 1) * T + 4, x0 * T:(x1 + 1) * T + 4] = True
    for k in ('schienen', 'foerderbaender', 'rohre'):
        for l in lay.get(k, []):
            pts = l['pfad'] if 'pfad' in l else [l['von'], l['bis']]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                bau[min(ay, by) * T:(max(ay, by) + 2) * T, min(ax, bx) * T:(max(ax, bx) + 2) * T] = True
    for z in lay['boden']:
        if z['art'] in ('asphalt', 'gehweg'):
            x0, y0, x1, y1 = z['r']
            bau[y0 * T:(y1 + 1) * T, x0 * T:(x1 + 1) * T] = True
    for m in lay.get('markierungen', []):
        x0, y0, x1, y1 = m['r']
        bau[y0 * T:(y1 + 1) * T, x0 * T:(x1 + 1) * T] = True
    for (dx_, dy_) in tm.get('dellen', []):              # Dellen bleiben frei
        bau[dy_ * T:(dy_ + 1) * T, dx_ * T:(dx_ + 1) * T] = True
    belegt = np.zeros((MH, MW), bool)
    objekte = []

    def boden_bei(ax, ay):
        x, y = min(max(int(ax), 0), MW - 1), min(max(int(ay) - 1, 0), MH - 1)
        if gras_maske[y, x]:
            return 'gras'
        k = cls[y // T][x // T]
        return 'metall' if k == 'm' else 'beton'

    def sprite_name(name):
        if name.startswith('C:'):
            _, f, v = name.split(':')
            return 'abgeleitet/container_%s_%s' % (f, v)
        if name == 'KRAN':
            return 'abgeleitet/kran'
        return name

    def setze(name, ax, ay, fest=True, opt=None):
        opt = opt or {}
        basis = sprite_name(name)
        gruppe = basis.split('/')[0]
        boden = boden_bei(ax, ay)
        vname = 'varianten/%s_%s' % (basis.replace('/', '-'), boden)
        pfad = os.path.join(OBJ, vname + '.png')
        if not os.path.exists(pfad):
            os.makedirs(os.path.join(OBJ, 'varianten'), exist_ok=True)
            quelle = lade(basis) if basis == 'abgeleitet/strommast' else harmonisieren(lade(basis))
            bauwerke.bodenfuss(quelle, boden, FUSS.get(gruppe, 'stein')).save(pfad)
        im = lade(vname)
        x, y = int(ax - im.width // 2), int(ay + 3 - im.height)
        a = np.array(im.getchannel('A')) >= 200
        xs0, ys0, xs1, ys1 = max(0, x), max(0, y), min(MW, x + im.width), min(MH, y + im.height)
        a = a[ys0 - y:ys1 - y, xs0 - x:xs1 - x]
        if not fest and ((belegt[ys0:ys1, xs0:xs1] | bau[ys0:ys1, xs0:xs1]) & a).any():
            return None
        belegt[ys0:ys1, xs0:xs1] |= a
        o = {'datei': vname + '.png', 'basis': basis, 'x': x, 'y': y, 'fuss': im.height, 'ebene': 1}
        o.update({k: v for k, v in opt.items()})
        if basis == 'abgeleitet/kran':
            pass                                     # offenes Geruest: Schatten nur unter den Fahrwerken (s. u.)
        elif gruppe in ('ortho', 'mittel', 'hoch', 'turm', 'reaktor', 'abgeleitet'):
            o['schatten'] = [int(im.width * 0.8), max(5, im.width // 8)]
        objekte.append(o)
        return o

    for name, tx, ty, opt in FEST:
        setze(name, tx * T, ty * T + 15, True, opt)
    for o in objekte:                                # Kran-Frames mit gleichem Bodenfuss
        if o['basis'] == 'abgeleitet/kran':
            boden = o['datei'].rsplit('_', 1)[1][:-4]
            for f in range(16):
                ziel = os.path.join(OBJ, 'varianten', 'abgeleitet-kran_f%02d_%s.png' % (f, boden))
                bauwerke.bodenfuss(harmonisieren(lade('abgeleitet/kran_f%02d' % f)), boden, 'stein').save(ziel)
    for o in list(objekte):                          # Fahrwerk-Schatten des Krans als unsichtbare Hilfsobjekte
        if o['basis'] == 'abgeleitet/kran':
            for dx in (8, 176 - 8):
                objekte.append({'datei': 'abgeleitet/leer.png', 'basis': 'schatten', 'x': o['x'] + dx + 2 - 1,
                                'y': o['y'] + o['fuss'] - 6, 'fuss': 6, 'ebene': 0, 'schatten': [26, 6]})
    Image.new('RGBA', (2, 2), (0, 0, 0, 0)).save(os.path.join(OBJ, 'abgeleitet', 'leer.png'))
    for tx, ty in SCHILDER:
        setze('klein/08', tx * T + 8, ty * T + 14, False)
    leitung = []
    punkte = json.load(open(os.path.join(OBJ, 'abgeleitet', 'strommast_punkte.json')))
    for tx, ty in MASTEN:
        o = setze('abgeleitet/strommast', tx * T, ty * T + 14, True)
        leitung.append([[o['x'] + 2 + px_, o['y'] + py_] for px_, py_ in punkte])
    # Anschluss am rechten Reaktor-Pylon (Spitze) und Weiterfuehrung aus der Karte nach unten
    pylon = [o for o in objekte if o['basis'] == 'turm/03']
    if pylon:
        p_ = max(pylon, key=lambda o: o['x'])
        spitze = [p_['x'] + Image.open(os.path.join(OBJ, p_['datei'])).width // 2, p_['y'] + 6]
        leitung.insert(0, [spitze] * 4)
    leitung.append([[x, rows * T + 40] for x, _ in leitung[-1]])
    json.dump({'masten': leitung, 'hoehe': 84}, open(os.path.join(OBJ, 'leitungen.json'), 'w'))
    for tx, ty in LATERNEN:
        o = setze('abgeleitet/laterne', tx * T + 8, ty * T + 12, True, {'anim': 'laterne'})
        o['schatten'] = [18, 5]

    # verstreute Kleinteile: wenige, bevorzugt nahe an Gebaeuden/Objekten (wie abgestellt), nicht mitten auf Flaechen
    from PIL import ImageFilter
    besetzt = Image.fromarray(((belegt | bau) * 255).astype(np.uint8))
    weit = np.array(besetzt.filter(ImageFilter.MaxFilter(29))) > 0
    eng = np.array(besetzt.filter(ImageFilter.MaxFilter(5))) > 0
    nah = weit & ~eng
    gesetzt, versuche = 0, 0
    while gesetzt < 85 and versuche < 9000 and STREU:
        versuche += 1
        cx, cy = rnd.randrange(3, cols - 3), rnd.randrange(4, rows - 3)
        if cls[cy][cx] != 'b':
            continue
        px_, py_ = cx * T + rnd.randint(3, 13), cy * T + rnd.randint(8, 15)
        if not nah[py_, px_]:
            continue
        if setze(rnd.choice(STREU), px_, py_, False):
            gesetzt += 1

    json.dump(objekte, open(os.path.join(OBJ, 'platzierung.json'), 'w'), indent=0)
    print(len(objekte), 'Objekte gesetzt')


# ---------------------------------------------------------------- Animation (von karte02_bauen.animation)
FEUER = [(0xc8, 0x3a, 0x1e), (0xe8, 0x70, 0x2a), (0xf5, 0xb0, 0x42), (0xff, 0xf2, 0xa0)]
GRUEN = [(0x2f, 0x8f, 0x5a), (0x4f, 0xd0, 0x7a), (0x9a, 0xf5, 0xb0)]


def animieren(img, objs, frame):
    a = np.array(img)
    puls = 0.5 + 0.5 * math.sin(frame / 16 * 2 * math.pi)
    for o in objs:
        anim = o.get('anim')
        if anim not in ('feuer', 'reaktor', 'blinken'):
            continue
        sp = Image.open(os.path.join(OBJ, o['datei']))
        x0, y0 = max(0, o['x']), max(0, o['y'])
        x1, y1 = min(a.shape[1], o['x'] + sp.width), min(a.shape[0], o['y'] + sp.height)
        reg = a[y0:y1, x0:x1]
        rr = reg[..., :3].astype(np.int16)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        if anim == 'feuer':
            stufe = (((yy * 2 + xx * 3 + frame * 5) % 7) > 3).astype(int) * 2 - 1
            for i, c in enumerate(FEUER):
                m = (rr == c).all(axis=2)
                ziel = np.clip(i + stufe, 0, len(FEUER) - 1)
                for j, cz in enumerate(FEUER):
                    reg[m & (ziel == j), :3] = cz
        elif anim == 'reaktor':
            for c in GRUEN:
                m = (rr == c).all(axis=2)
                dunkel = np.array([v * 0.6 for v in c]); hell = np.array([min(255, v + 60) for v in c])
                reg[m, :3] = (dunkel + (hell - dunkel) * (0.3 + 0.7 * puls)).astype(np.uint8)
        elif anim == 'blinken':
            m = ((rr[..., 0] > 150) & (rr[..., 1] < 110) & (rr[..., 2] < 90))
            if (frame // 4) % 2:
                reg[m, :3] = (reg[m, :3] * 0.45).astype(np.uint8)
        a[y0:y1, x0:x1] = reg
    img.paste(Image.fromarray(a))
    # Feuer: warmer Lichtschein vor der Ofenoeffnung (pulsierend) und aufsteigende Funken
    from PIL import ImageDraw as _D
    glut = Image.new('RGBA', img.size, (0, 0, 0, 0))
    gd = _D.Draw(glut)
    a2 = np.array(img)
    for i, o in enumerate(objs):
        if o.get('anim') != 'feuer':
            continue
        sp = Image.open(os.path.join(OBJ, o['datei']))
        x0, y0 = max(0, o['x']), max(0, o['y'])
        reg = a2[y0:y0 + sp.height, x0:x0 + sp.width, :3].astype(np.int16)
        m = np.zeros(reg.shape[:2], bool)
        for c in FEUER:
            m |= (reg == c).all(axis=2)
        ys, xs = np.nonzero(m)
        if len(xs) < 3:
            continue
        fx, fy = x0 + xs.mean(), y0 + ys.max()
        flack = 0.75 + 0.25 * math.sin(frame * 2.1 + i * 1.3) * math.sin(frame * 0.9 + i)
        for r, alpha in ((22, 34), (15, 46), (9, 60)):
            gd.ellipse((fx - r, fy - r * 0.45 + 4, fx + r, fy + r * 0.45 + 4), fill=(255, 150, 60, int(alpha * flack)))
        rnd = random.Random(i * 31)
        for k in range(5):                         # Funken steigen auf und verloeschen
            t = ((frame + k * 3 + rnd.randint(0, 15)) % 16) / 16
            sx = fx + rnd.uniform(-5, 5) + math.sin(t * 7 + k) * 2
            sy = y0 + ys.min() - t * 22
            farbe = (255, 242, 160) if t < 0.4 else (245, 176, 66) if t < 0.75 else (200, 80, 40)
            if t < 0.9:
                gd.point((sx, sy), fill=farbe + (255,))
    img.alpha_composite(glut)
    # Rauch aus Schornsteinen: Woelkchen steigen auf und werden groesser und blasser
    from PIL import ImageDraw
    rauch = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(rauch)
    for i, o in enumerate(objs):
        if 'rauch' not in o:
            continue
        sp_w = Image.open(os.path.join(OBJ, o['datei'])).width
        sx = o['x'] + sp_w * o['rauch'][0]
        sy = o['y'] + 4
        for k in range(4):
            t = ((frame + k * 4 + i * 3) % 16) / 16
            r = 3 + t * 7
            px, py = sx + t * 14 + math.sin(t * 6 + i) * 2, sy - t * 34
            alpha = int(150 * (1 - t))
            d.ellipse((px - r, py - r * 0.8, px + r, py + r * 0.8), fill=(205, 212, 216, alpha))
            d.ellipse((px - r * 0.6, py - r * 0.7, px + r * 0.2, py - r * 0.1), fill=(232, 236, 238, alpha))
    img.alpha_composite(rauch)


if __name__ == '__main__':
    main()
