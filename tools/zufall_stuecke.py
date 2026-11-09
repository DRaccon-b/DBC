"""Vorgefertigte Kartenstuecke fuer Zufallskarten im Stil von Karte 01 (Wald, Wiese, Sandweg, Teich).

  python3 tools/zufall_stuecke.py        (prueft alle Stuecke und zeichnet maps/zufall/stuecke_uebersicht.png)

Prinzip (wie bei Kachel-Dungeons a la Path of Exile): Ein Stueck ist ein Gelaenderaster aus 14x14 Kacheln
(oder ein Vielfaches, z. B. die Bossarena mit 2x2 Feldern = 28x28). Jede Seite eines Feldes hat einen
Kantentyp, der direkt aus den aeusseren zwei Kachelreihen abgelesen wird:

  Z  zu      FFFFFFFFFFFFFF   Wald, kein Durchgang
  W  Waldweg FFFFGGPPGGFFFF   schmaler Weg durch eine Waldluecke
  O  offen   FFGGGGPPGGGGFF   breite Wiese mit Weg

Weil die Kanten genormt sind, passen zwei Stuecke immer nahtlos zusammen, wenn ihre Kantentypen
gleich sind. Der Weg (P) liegt an jeder offenen Kante auf den Spalten 6-7 (Mitte), dadurch passen auch
gedrehte und gespiegelte Stuecke. Innen ist alles frei: Wege in Boegen und Diagonalen (Regel 6), Teiche,
Lichtungen. Jedes Stueck wird automatisch in bis zu 8 Lagen (4 Drehungen x Spiegelung) verwendet.

Zeichen: F Wald, G Wiese, P Sandweg, W Teich (Wasser, vertieft wie auf Karte 01).
objekte: feste Objekte (Sprite aus assets/objekte/karte01, Ankerzelle x, y = Fuss mitte unten) -
         werden mit dem Stueck gedreht; das Sprite selbst bleibt aufrecht.
drehen:  180 = nur um 180 Grad drehen (und spiegeln), z. B. wenn Objektpaare symmetrisch stehen muessen.
symmetrie: (achse, a, b) = Objekt a und b stehen nach dem Einrasten exakt spiegelgleich zu Objekt achse.
typ:     start | boss | normal | wald     gewicht: wie oft das Stueck gewaehlt wird
"""
import os
from PIL import Image

OBJ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'objekte', 'karte01')
N = 14                       # Kacheln je Feld
KANTE = {'Z': 'FFFFFFFFFFFFFF', 'W': 'FFFFGGPPGGFFFF', 'O': 'FFGGGGPPGGGGFF'}

STUECKE = [
    {'name': 'weg_bogen', 'typ': 'normal', 'gewicht': 3, 'raster': [
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFGGPPGGGGFFF',
        'FFGGPPGGGGGGFF',
        'FFGPPGGGGGGGFF',
        'FFGPPGGGGGGFFF',
        'FFGGPPGGGGFFFF',
        'FFFGGPPGGGFFFF',
        'FFFFGGPPGGGFFF',
        'FFFFGGGPPGGGFF',
        'FFFGGGGGPPGGFF',
        'FFFFGGGPPGGGFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF']},
    {'name': 'wiese_teich', 'typ': 'normal', 'gewicht': 2, 'raster': [
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGGGPPGGFF',
        'FFGGWWGGPPGGFF',
        'FFGWWWGGPPGGFF',
        'FFGWWWGGPPGGFF',
        'FFGGWGGPPGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF']},
    {'name': 'weg_zu_wiese', 'typ': 'normal', 'gewicht': 2, 'raster': [
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFGGGGPPGGFFF',
        'FFFGGGGPPGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGPPGGGGGFF',
        'FFGGGPPGGGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF']},
    {'name': 'teich_am_weg', 'typ': 'normal', 'gewicht': 2, 'raster': [
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFGGGPPGGGFFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGPPPPWWGFF',
        'FFGGGPPPWWWGFF',
        'FFGGGPPPWWWGFF',
        'FFGGGGPPPWWGFF',
        'FFGGGGPPGGGGFF',
        'FFFGGGGPPGGGFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF']},
    {'name': 'weg_ecke', 'typ': 'normal', 'gewicht': 3, 'raster': [
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFGGGPPGGGFFF',
        'FFFGGGGPPGGGGG',
        'FFFGGGGGPPGGGG',
        'FFFGGGGGGPPPPP',
        'FFFFGGGGGGPPPP',
        'FFFFFGGGGGGGGG',
        'FFFFFFGGGGGGGG',
        'FFFFFFFGGGGFFF',
        'FFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFF']},
    {'name': 'wiese_ecke', 'typ': 'normal', 'gewicht': 2, 'raster': [
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGGG',
        'FFGGGGGPPGGGGG',
        'FFGGGGGPPGGGGG',
        'FFGGGGGGPPGGGG',
        'FFFGGGGGGPPPPP',
        'FFFGGGGGGGPPPP',
        'FFFFGGGGGGGGGG',
        'FFFFGGGGGGGGGG',
        'FFFFFGGGGGGGGG',
        'FFFFFFGGGGGGGG',
        'FFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFF']},
    {'name': 'weg_gabel', 'typ': 'normal', 'gewicht': 3, 'raster': [
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFGGGPPGGGFFF',
        'FFFGGGPPGGGGGG',
        'FFGGGPPGGGGGGG',
        'FFGGGPPGGPPPPP',
        'FFGGGPPPPPPPPP',
        'FFGGGGPPPGGGGG',
        'FFFGGGPPGGGGGG',
        'FFFGGGGPPGGFFF',
        'FFFFGGGPPGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF']},
    {'name': 'wiese_kreuz', 'typ': 'normal', 'gewicht': 1, 'raster': [
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF',
        'GGGGGGGPPGGGGG',
        'GGGGGGGPPGGGGG',
        'GGGGGGPPGGGGGG',
        'GGGGGGPPGGGGGG',
        'PPGGGGPPGGGGPP',
        'PPPPPPPPPPPPPP',
        'GGGPPPPPPPPPGG',
        'GGGGGGPPGGGGGG',
        'GGGGGGGPPGGGGG',
        'GGGGGGGPPGGGGG',
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF']},
    {'name': 'weg_kreuz', 'typ': 'normal', 'gewicht': 1, 'raster': [
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGGPPGFFFF',
        'GGGGGGGPPGGGGG',
        'GGGGGGPPPGGGGG',
        'PPPGGGPPGGGPPP',
        'PPPPPPPPPPPPPP',
        'GGGGPPPPPPPPGG',
        'GGGGGGPPGGGGGG',
        'FFFFGGPPGGFFFF',
        'FFFFGGGPPGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF']},
    {'name': 'ecke_weg_wiese', 'typ': 'normal', 'gewicht': 3, 'raster': [
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGGPPGGGGG',
        'FFFGGGGPPGGGGG',
        'FFFGGGGGPPGGGG',
        'FFFGGGGGPPGGGG',
        'FFFGGGGGGPPPPP',
        'FFFFGGGGGPPPPP',
        'FFFFGGGGGGGGGG',
        'FFFFGGGGGGGGGG',
        'FFFFFGGGGGGGGG',
        'FFFFFFGGGGGGGG',
        'FFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFF']},
    {'name': 'wiese_gabel', 'typ': 'normal', 'gewicht': 3, 'raster': [
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGGGPPGGGG',
        'FFGGGGGGPPGGGG',
        'FFGGGGGGPPPPPP',
        'FFGGGGGPPPPPPP',
        'FFGGGGGPPGGGGG',
        'FFGGGGPPGGGGGG',
        'FFGGGGPPGGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF']},
    {'name': 'wiese_rosabaum', 'typ': 'normal', 'gewicht': 2,
     'objekte': [('gross/01', 4, 5)], 'raster': [
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGGGPPGGFF',
        'FFGGGGGGPPGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGPPGGGGGFF',
        'FFGGGPPGGGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF']},
    {'name': 'sackgasse_findling', 'typ': 'normal', 'gewicht': 2,
     'objekte': [('gross/09', 4, 9), ('gross/01', 8, 5)], 'raster': [
        'FFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFF',
        'FFFFFFGGGGFFFF',
        'FFFFGGGGGGGGFF',
        'FFFGGGGGGGGGFF',
        'FFGGGGGGGGGGFF',
        'FFGGGGGGGGGGFF',
        'FFGGGGGGGGGGFF',
        'FFGGGGGGPPGGFF',
        'FFGGGGGGPPGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF']},
    {'name': 'lichtung_runenbaum', 'typ': 'normal', 'gewicht': 2,
     'objekte': [('gross/00', 7, 6)], 'raster': [
        'FFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFF',
        'FFFFGGGGGGFFFF',
        'FFFGGGGGGGGFFF',
        'FFGGGGGGGGGGFF',
        'FFGGGGGGGGGGFF',
        'FFGGGGGGGGGGFF',
        'FFGGGGPPPGGGFF',
        'FFFGGGGPPGGGFF',
        'FFFGGGGPPGGFFF',
        'FFFFGGGPPGGFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF']},
    {'name': 'sackgasse_teich', 'typ': 'normal', 'gewicht': 2, 'raster': [
        'FFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFF',
        'FFFFFGGGGFFFFF',
        'FFFGGGGGGGGFFF',
        'FFGGGWWWWGGGFF',
        'FFGGWWWWWWGGFF',
        'FFGGWWWWWWGGFF',
        'FFGGGWWWWGGGFF',
        'FFGGGGGPPGGGFF',
        'FFFGGGGPPGGGFF',
        'FFFFGGPPPGGFFF',
        'FFFFGGGPPGGFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF']},
    {'name': 'sackgasse_wiese', 'typ': 'normal', 'gewicht': 2, 'raster': [
        'FFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFF',
        'FFFFFGGGGGFFFF',
        'FFFGGGGGGGGFFF',
        'FFFGGGGGGGGGFF',
        'FFGGGGGGGGGGFF',
        'FFGGGGGGGGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGGPPGGGFF',
        'FFGGGGPPGGGGFF',
        'FFGGGGPPGGGGFF']},
    {'name': 'sackgasse_brunnen', 'typ': 'normal', 'gewicht': 1,
     'objekte': [('zufall_brunnen/00', 7, 6)], 'raster': [
        'FFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFF',
        'FFFFFGGGGGFFFF',
        'FFFFGGGGGGGFFF',
        'FFFGGGGGGGGGFF',
        'FFFGGGGGGGGGFF',
        'FFFGGGGPPGGGFF',
        'FFFFGGPPGGGFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGGPPGFFFF',
        'FFFFGGGPPGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF']},
    {'name': 'start_lager', 'typ': 'start', 'gewicht': 1,
     'objekte': [('zufall_portal/01', 4, 5), ('gross/14', 9, 5), ('gross/13', 6, 11)], 'raster': [
        'FFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFF',
        'FFFFGGGGGGFFFF',
        'FFFGGGGGGGGGFF',
        'FFGGGGGGGGGGFF',
        'FFGGGGGGGGGGFF',
        'FFGGGGGGGGGGFF',
        'FFGGGGGGGGGGFF',
        'FFGGGGGPPGGGFF',
        'FFFGGGGPPGGGFF',
        'FFFFGGPPGGGFFF',
        'FFFFGGGPPGFFFF',
        'FFFFGGPPGGFFFF',
        'FFFFGGPPGGFFFF']},
    {'name': 'boss_dschungelbaum', 'typ': 'boss', 'gewicht': 1, 'drehen': 180,
     'symmetrie': [(0, 1, 2)],
     'objekte': [('dschungel/00', 13, 11), ('gross/09', 7, 16), ('gross/09', 19, 16)], 'raster': [
        'FFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        'FFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        'FFFFFFFFFGGGGGGGGGGFFFFFFFFF',
        'FFFFFFFFGGGGGGGGGGGGFFFFFFFF',
        'FFFFFFFGGGGGGGGGGGGGGFFFFFFF',
        'FFFFFFGGGGGGGGGGGGGGGGFFFFFF',
        'FFFFFGGGGGGGGGGGGGGGGGGFFFFF',
        'FFFFGGGGGGGGGGGGGGGGGGGGFFFF',
        'FFFFGGGGGGGGGGGGGGGGGGGGFFFF',
        'FFFFGGGGGGGGGGGGGGGGGGGGFFFF',
        'FFFFGGGGGGGGGGGGGGGGGGGGFFFF',
        'FFFGGGGGGGGGGGGGGGGGGGGGGFFF',
        'FFFFGGGGGGGGGGGGGGGGGGGGFFFF',
        'FFFFGGGGGGGGGGGGGGGGGGGGFFFF',
        'FFFFGGGGGGGGGGGGGGGGGGGGFFFF',
        'FFFFGGGGGGGGGPPGGGGGGGGGFFFF',
        'FFFFFGGGGGGGGPPGGGGGGGGFFFFF',
        'FFFFFFGGGGGGPPGGGGGGGGFFFFFF',
        'FFFFFFFGGGGPPGGGGGGGGFFFFFFF',
        'FFFFFFFFGGPPGGGGGGGGFFFFFFFF',
        'FFFFFFFGGPPGGGGGGGGFFFFFFFFF',
        'FFFFFFGGPPGGFFFFFFFFFFFFFFFF',
        'FFFFFGGPPGGFFFFFFFFFFFFFFFFF',
        'FFFFGGPPGGFFFFFFFFFFFFFFFFFF',
        'FFFFGGPPGGFFFFFFFFFFFFFFFFFF',
        'FFFFGGPPGGFFFFFFFFFFFFFFFFFF']},
    {'name': 'wald', 'typ': 'wald', 'gewicht': 1, 'raster': ['F' * N] * N},
]


# ---------------------------------------------------------------- Kanten, Drehen, Spiegeln
def kanten(raster):
    """Kantentypen aller Aussenseiten: {(fx, fy, seite): typ}, seite in N O S W (Nord/Ost/Sued/West)."""
    h, w = len(raster) // N, len(raster[0]) // N
    out = {}
    for fy in range(h):
        for fx in range(w):
            x0, y0 = fx * N, fy * N
            seiten = {}
            if fy == 0:
                seiten['N'] = [raster[y0 + d][x0:x0 + N] for d in (0, 1)]
            if fy == h - 1:
                seiten['S'] = [raster[y0 + N - 1 - d][x0:x0 + N] for d in (0, 1)]
            if fx == 0:
                seiten['W'] = [''.join(raster[y0 + i][x0 + d] for i in range(N)) for d in (0, 1)]
            if fx == w - 1:
                seiten['O'] = [''.join(raster[y0 + i][x0 + N - 1 - d] for i in range(N)) for d in (0, 1)]
            for s, (a, b) in seiten.items():
                typ = next((t for t, k in KANTE.items() if a == k and b == k), None)
                if typ is None:
                    raise ValueError('Kante %s von Feld (%d,%d) passt zu keinem Typ: %s / %s' % (s, fx, fy, a, b))
                out[(fx, fy, s)] = typ
    return out


def drehen(st):
    """90 Grad im Uhrzeigersinn."""
    r = st['raster']
    H, W = len(r), len(r[0])
    neu = [''.join(r[H - 1 - y][x] for y in range(H)) for x in range(W)]
    obj = [(n, H - 1 - y, x) for n, x, y in st.get('objekte', [])]
    return dict(st, raster=neu, objekte=obj)


def spiegeln(st):
    r = st['raster']
    W = len(r[0])
    return dict(st, raster=[z[::-1] for z in r], objekte=[(n, W - 1 - x, y) for n, x, y in st.get('objekte', [])])


def lagen(st):
    """Alle verschiedenen Lagen (4 Drehungen x Spiegelung) eines Stuecks, mit Kanten."""
    out, gesehen = [], set()
    for sp in (False, True):
        s = spiegeln(st) if sp else st
        for d in range(4):
            if st.get('drehen') == 180 and d % 2:
                s = drehen(s)
                continue
            key = '\n'.join(s['raster'])
            if key not in gesehen:
                gesehen.add(key)
                out.append(dict(s, lage='%s%d' % ('s' if sp else '', d * 90), kanten=kanten(s['raster']),
                                felder=(len(s['raster'][0]) // N, len(s['raster']) // N)))
            s = drehen(s)
    return out


def alle_lagen():
    return [l for st in STUECKE for l in lagen(st)]


def pruefen():
    for st in STUECKE:
        r = st['raster']
        assert len(r) % N == 0 and all(len(z) == len(r[0]) and len(r[0]) % N == 0 for z in r), st['name']
        assert all(c in 'FGPW' for z in r for c in z), st['name']
        k = kanten(r)
        # keine 1 Kachel schmale Grasinsel zwischen Weg und Wasser (wird sonst ein loser Grasfleck im Sand)
        for y in range(len(r)):
            for x in range(len(r[0])):
                if r[y][x] != 'G':
                    continue
                for (ax, ay), (bx, by) in (((x - 1, y), (x + 1, y)), ((x, y - 1), (x, y + 1))):
                    if 0 <= ax and 0 <= ay and bx < len(r[0]) and by < len(r):
                        assert {r[ay][ax], r[by][bx]} != {'P', 'W'}, ('Grasinsel', st['name'], x, y)
        for n, x, y in st.get('objekte', []):
            assert r[y][x] == 'G', (st['name'], n, x, y)
        for l in lagen(st):                       # feste Objekte duerfen sich in keiner Lage beruehren (4 px Abstand)
            boxen = []
            rl = l['raster']
            for n, x, y in l.get('objekte', []):
                # Fuss frei: vor (suedlich) und neben dem Fuss 2 Kacheln kein Wald, sonst verdecken Waldbaeume den Stamm
                for dx in (-1, 0, 1):
                    for dy in (0, 1, 2):
                        yy, xx = y + dy, x + dx
                        assert not (0 <= yy < len(rl) and 0 <= xx < len(rl[0]) and rl[yy][xx] == 'F'), \
                            ('Fuss am Waldrand', st['name'], l['lage'], n, x, y)
                w, h = Image.open(os.path.join(OBJ, n + '.png')).size
                boxen.append((n, x * 16 + 8 - w / 2 - 4, y * 16 + 14 - h - 4, x * 16 + 8 + w / 2 + 4, y * 16 + 14 + 4))
            for i in range(len(boxen)):
                for j in range(i + 1, len(boxen)):
                    a, b = boxen[i], boxen[j]
                    assert a[3] <= b[1] or b[3] <= a[1] or a[4] <= b[2] or b[4] <= a[2], \
                        (st['name'], l['lage'], a[0], b[0])
        print('%-20s %dx%d Felder, %d Lagen, Kanten %s' % (st['name'], len(r[0]) // N, len(r) // N, len(lagen(st)),
                                                         ''.join(k[(0, 0, s)] if (0, 0, s) in k else '-' for s in 'NOSW')))


FARBE = {'F': (46, 110, 62), 'G': (120, 200, 96), 'P': (226, 196, 140), 'W': (60, 110, 200)}


def bild(raster, px=4):
    from PIL import Image
    im = Image.new('RGB', (len(raster[0]) * px, len(raster) * px))
    for y, z in enumerate(raster):
        for x, c in enumerate(z):
            im.paste(FARBE[c], (x * px, y * px, (x + 1) * px, (y + 1) * px))
    return im


def uebersicht(pfad):
    from PIL import Image, ImageDraw
    px, rand = 6, 24
    breite = sum(len(s['raster'][0]) * px + rand for s in STUECKE) + rand
    zeilen, x, y, hmax, plaetze = [], rand, rand, 0, []
    for s in STUECKE:
        w, h = len(s['raster'][0]) * px, len(s['raster']) * px
        if x + w > 1100:
            x, y, hmax = rand, y + hmax + rand + 14, 0
        plaetze.append((s, x, y))
        x += w + rand
        hmax = max(hmax, h)
    im = Image.new('RGB', (1100 + rand, y + hmax + rand + 14), (30, 34, 40))
    d = ImageDraw.Draw(im)
    for s, x, y in plaetze:
        im.paste(bild(s['raster'], px), (x, y + 14))
        d.text((x, y), s['name'], fill=(230, 230, 230))
        for n, ox, oy in s.get('objekte', []):
            d.rectangle((x + ox * px, y + 14 + oy * px, x + ox * px + px - 1, y + 14 + oy * px + px - 1), fill=(220, 40, 60))
    im.save(pfad)


if __name__ == '__main__':
    pruefen()
    ziel = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'maps', 'zufall')
    os.makedirs(ziel, exist_ok=True)
    uebersicht(os.path.join(ziel, 'stuecke_uebersicht.png'))
    print('Lagen gesamt:', len(alle_lagen()))
