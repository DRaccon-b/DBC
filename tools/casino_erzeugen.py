"""PixelLab-Erzeugung fuer die Casino-Karten (tools/casino_themen.py): zwei Wang-Tilesets und die Objekte je Karte.

  python3 tools/casino_erzeugen.py 57            # alles fuer Karte 57
  python3 tools/casino_erzeugen.py 57 tiles      # nur Tilesets
  python3 tools/casino_erzeugen.py 57 objekte    # nur Objekte

Tilesets: assets/tilesets/pixellab/casinoNN_a.json/.png (Hintergrund <-> Boden) und casinoNN_b (Boden <-> Akzent; der
Boden von A ist Referenz und Basiskachel von B, damit beide Sets denselben Boden haben). Pro-Modus, 16 px, Ecken in
45 Grad (roundness 2, Regel 6b). Objekte: assets/objekte/karteNN/o32|o48|o96/NN.png (Objekt-Creator, frontal).
"""
import base64, io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import pixellab_tileset as pt
import pixellab_objekte as po
from casino_themen import THEMEN, FR

STIL = 'cozy colorful casino, ' + FR


def _mit_wiederholung(f):
    """PixelLab antwortet bei vielen parallelen Auftraegen mit 429/5xx: warten und erneut versuchen."""
    import time, urllib.error

    def g(*a, **k):
        for i in range(12):
            try:
                return f(*a, **k)
            except urllib.error.HTTPError as e:
                if e.code not in (429, 500, 502, 503, 504) or i == 11:
                    raise
                time.sleep(min(120, 10 * (i + 1)))
    return g


pt.call = _mit_wiederholung(pt.call)
po.call = _mit_wiederholung(po.call)


def tileset(name, req):
    pf = os.path.join(pt.OUT, name + '.json')
    if os.path.exists(pf):
        print(name, 'vorhanden'); return json.load(open(pf))
    st, d = pt.call('POST', '/create-tileset', req)
    tid = d.get('tileset_id') or d.get('id') or (d.get('tileset') or {}).get('id')
    print(name, st, tid)
    if 'tileset' in d and d['tileset'].get('tiles'):
        pt.speichern(d, name, tid)
    else:
        pt.speichern(pt.warte(tid), name, tid)
    return json.load(open(pf))


def voll_kachel(ts, art):
    """Base64 der Kachel, deren vier Ecken alle 'art' sind."""
    for t in ts['tileset']['tiles']:
        if all(v == art for v in t['corners'].values()):
            return t['image']['base64']


def tiles(nr):
    th = THEMEN[nr]
    basis = {'tile_size': {'width': 16, 'height': 16}, 'view': 'high top-down', 'mode': 'pro', 'roundness': 2}
    a = dict(basis, lower_description=th['bg'], upper_description=th['boden'], transition_size=th['kante'],
             transition_description='clean edge, no thick outline', lower_walkable=False, upper_walkable=True)
    A = tileset('casino%d_a' % nr, a)
    ref = voll_kachel(A, 'upper')
    b = dict(basis, lower_description=th['boden'], upper_description=th['akzent'], transition_size=0.0,
             transition_description='thin neat border, no thick outline', lower_walkable=True, upper_walkable=True)
    if ref:
        b['lower_reference_image'] = {'type': 'base64', 'base64': ref, 'format': 'png'}
    tileset('casino%d_b' % nr, b)


def objekte(nr):
    th = THEMEN[nr]
    gruppen = {}
    for k, (txt, gr) in th['objekte'].items():
        gruppen.setdefault(gr, []).append((k, txt))
    namen = {}
    for gr, liste in sorted(gruppen.items()):
        gruppe = 'k%d_o%d' % (nr, gr)
        ziel = os.path.join(po.ROOT, 'assets', 'objekte', 'karte%d' % nr, 'o%d' % gr)
        if not os.path.exists(os.path.join(ziel, 'uebersicht.png')):
            req = {'description': STIL, 'size': gr, 'view': 'top-down',
                   'item_descriptions': [txt + ', ' + STIL for _, txt in liste]}
            d = po.call('POST', '/v2/create-1-direction-object', req)
            oid = d['object_id']
            print(gruppe, 'Objekt', oid)
            d = po.warte(oid)
            po.speichern(gruppe, *po.herunterladen(oid, d))
        for i, (k, _) in enumerate(liste):
            namen[k] = 'o%d/%02d.png' % (gr, i)
    json.dump(namen, open(os.path.join(po.ROOT, 'assets', 'objekte', 'karte%d' % nr, 'namen.json'), 'w'), indent=1)


if __name__ == '__main__':
    nr = int(sys.argv[1])
    was = sys.argv[2] if len(sys.argv) > 2 else 'alles'
    if was in ('alles', 'tiles'):
        tiles(nr)
    if was in ('alles', 'objekte'):
        objekte(nr)
