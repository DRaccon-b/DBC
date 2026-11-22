"""Karte 06 (Startkarte) in der Weihnachtsausgabe (Nutzer): ganze Karte voller Schnee, der Riesenbrunnen in der Mitte
wird durch einen gleich grossen Weihnachtsbaum ersetzt. Jede Schnee-Kachel ist die Original-Kachel in der
Xmas-Edition, erzeugt mit PixelLab (edit-image-pixen): Gras, Sandweg, Kopfstein, Betonplatten.

  python3 tools/karte06_xmas.py kacheln    # PixelLab: Grundkacheln -> assets/basis_xmas/
  python3 tools/karte06_xmas.py objekte    # PixelLab: alle Objekte mit Schnee -> assets/objekte/karte06_xmas/
  python3 tools/karte06_xmas.py baum       # PixelLab: Weihnachtsbaum in Brunnengroesse
  python3 tools/karte06_xmas.py bauen      # -> maps/karte06_xmas/terrain.png

Der Bau nutzt karte06_bauen unveraendert (gleiche Uebergaenge, Wege, Teich, Zaun); nur die Grundkacheln und die
Objekt-Sprites werden gegen die Xmas-Fassungen getauscht.
"""
import json, os, shutil, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
XK = os.path.join(ROOT, 'assets', 'basis_xmas')
OBJ_ALT = os.path.join(ROOT, 'assets', 'objekte', 'karte06')
OBJ_NEU = os.path.join(ROOT, 'assets', 'objekte', 'karte06_xmas')
KARTE_NEU = os.path.join(ROOT, 'maps', 'karte06_xmas')

STIL = ' Keep the exact same pixel art style, size and layout; it must stay a seamless 16x16 ground tile.'
GRUNDKACHELN = {   # Name: (Pfadmuster, Anzahl, Umfaerbung aus karte06_bauen, Anweisung)
    'gras': ('assets/basis/gras_%d.png', 5, None,
             'Christmas winter edition of this grass ground tile: covered by fresh soft snow, white with light blue '
             'shading and a few tiny green grass tips poking through.'),
    'sand': ('assets/basis/sand_%d.png', 5, None,
             'Christmas winter edition of this sandy dirt path tile: a trampled snowy path, light grey-beige packed '
             'snow with a little brown dirt showing through.'),
    'kies': ('assets/karte03/basis/kies_%d.png', 5, 'beige',
             'Christmas winter edition of this cobblestone pavement tile: the same warm grey-beige stones with small '
             'snow caps on top and snow in the gaps.'),
    'platz': ('assets/karte02/basis/platz_%d.png', 3, 'platten',
              'Christmas winter edition of this concrete slab tile: a light dusting of snow and frost on the slabs, '
              'the seams still visible.'),
}


def _umfaerben(art, a):
    import karte06_bauen as k6
    if art == 'beige':
        return k6.beige(a)
    if art == 'platten':
        return a * np.array([0.82, 0.88, 1.0]) + np.array([20, 24, 30])
    return a


def kacheln():
    from pixellab_edit import bearbeiten
    os.makedirs(XK, exist_ok=True)
    auftraege = []
    for name, (muster, n, umf, anweisung) in GRUNDKACHELN.items():
        for v in range(n):
            ziel = os.path.join(XK, '%s_%d.png' % (name, v))
            if os.path.exists(ziel):
                continue
            a = np.array(Image.open(os.path.join(ROOT, muster % v)).convert('RGB')).astype(np.float32)
            a = np.clip(_umfaerben(umf, a), 0, 255).astype(np.uint8)
            mosaik = Image.fromarray(np.tile(a, (3, 3, 1)))             # 3x3 gekachelt: Mitte bleibt nahtlos
            auftraege.append((mosaik, anweisung + STIL, ziel))

    def eins(t):
        mosaik, anw, ziel = t
        out = bearbeiten(mosaik, anw, hintergrund=True)
        out.convert('RGB').crop((16, 16, 32, 32)).save(ziel)
        print('  ', os.path.basename(ziel))
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(eins, auftraege))


OBJ_ANWEISUNG = ('Christmas winter edition of this exact object: add fresh white snow on its top surfaces (roofs, '
                 'tree crowns, ledges, tops), a few icicles where fitting; keep the exact same shape, size, outline, '
                 'position and pixel art style, do not add new objects.')


def objekte():
    from pixellab_edit import bearbeiten
    p = json.load(open(os.path.join(OBJ_ALT, 'platzierung.json')))
    dateien = sorted(set(o['datei'] for o in p if not o['datei'].startswith('varianten/brunnen-')))
    todo = [d for d in dateien if not os.path.exists(os.path.join(OBJ_NEU, d))]

    def eins(d):
        alt = Image.open(os.path.join(OBJ_ALT, d)).convert('RGBA')
        neu = bearbeiten(alt, OBJ_ANWEISUNG, hintergrund=False)
        # Umriss bleibt: nur Pixel innerhalb der Original-Silhouette (plus 1 px fuer Schneekappen oben)
        a_alt = np.array(alt)[..., 3] > 0
        rein = a_alt.copy()
        rein[:-1] |= a_alt[1:]
        n = np.array(neu)
        n[~rein] = 0
        os.makedirs(os.path.dirname(os.path.join(OBJ_NEU, d)), exist_ok=True)
        Image.fromarray(n).save(os.path.join(OBJ_NEU, d))
        print('  ', d)
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(eins, todo))


def baum():
    """Weihnachtsbaum in Groesse des Riesenbrunnens (PixelLab Objekt-Creator, Zielgroesse, nie skaliert)."""
    import pixellab_objekte as po
    gruppe = 'k06x_baum'
    ziel = os.path.join(OBJ_NEU, 'xmasbaum')
    if os.path.exists(os.path.join(ziel, 'uebersicht.png')):
        return
    beschr = ('huge decorated christmas tree standing on a round snowy cobblestone pedestal, golden star on top, red '
              'and gold baubles, warm glowing string lights, wrapped presents at its base, ' + po.FR14)
    req = {'description': beschr, 'size': 224, 'view': 'top-down', 'item_descriptions': [beschr]}
    d = po.call('POST', '/v2/create-1-direction-object', req)
    oid = d['object_id']
    print(gruppe, oid)
    d = po.warte(oid)
    ims, ids = po.herunterladen(oid, d)
    os.makedirs(ziel, exist_ok=True)
    for i, im in enumerate(ims):
        im.save(os.path.join(ziel, '%02d.png' % i))
    ims[0].save(os.path.join(ziel, 'uebersicht.png'))


def bauen():
    import karte06_bauen as k6
    os.makedirs(KARTE_NEU, exist_ok=True)
    shutil.copy(os.path.join(k6.KARTE, 'layout.json'), os.path.join(KARTE_NEU, 'layout.json'))
    ersatz = {os.path.normpath(os.path.join(ROOT, m)): name for name, (m, n, u, a) in GRUNDKACHELN.items()}
    orig = k6.kacheln

    def kacheln_xmas(pfad, n, umfaerben=None):
        name = ersatz.get(os.path.normpath(pfad))
        if name is None:
            return orig(pfad, n, umfaerben)
        return [np.array(Image.open(os.path.join(XK, '%s_%d.png' % (name, v))).convert('RGB')) for v in AUSWAHL[name]]
    k6.kacheln = kacheln_xmas
    # Objekte: Xmas-Sprites, Brunnen -> Weihnachtsbaum
    p = json.load(open(os.path.join(OBJ_ALT, 'platzierung.json')))
    neu = []
    for o in p:
        o = dict(o)
        if o['datei'].startswith('varianten/brunnen-'):
            baum_ = Image.open(os.path.join(OBJ_NEU, 'xmasbaum', '%02d.png' % BAUM_NR)).convert('RGBA')
            baum_ = baum_.crop(baum_.getbbox())
            baum_.save(os.path.join(OBJ_NEU, 'xmasbaum_gesetzt.png'))
            alt = Image.open(os.path.join(OBJ_ALT, o['datei']))
            fuss_y = o['y'] + o['fuss']                                  # gleicher Fuss, gleiche Mitte wie der Brunnen
            mx = o['x'] + alt.width / 2.0
            o.update({'datei': 'xmasbaum_gesetzt.png', 'basis': 'xmasbaum', 'x': int(round(mx - baum_.width / 2.0)),
                      'y': fuss_y - baum_.height + 1, 'fuss': baum_.height - 1, 'anim': 'lampe'})
        neu.append(o)
    json.dump(neu, open(os.path.join(OBJ_NEU, 'platzierung.json'), 'w'), indent=0)
    k6.KARTE, k6.OBJ = KARTE_NEU, OBJ_NEU
    k6.bauen()


BAUM_NR = 0
AUSWAHL = {'gras': [0, 1, 3, 4], 'sand': [0, 1], 'kies': [0, 3], 'platz': [0, 1, 2]}   # zueinander passende Varianten

if __name__ == '__main__':
    {'kacheln': kacheln, 'objekte': objekte, 'baum': baum, 'bauen': bauen}[sys.argv[1]]()
