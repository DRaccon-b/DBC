"""Xmas-Edition fuer beliebige Karten (Nutzer: wie die Startkarte 06 - ganze Karte voller Schnee, jede Schnee-Kachel und
jedes verschneite Objekt mit PixelLab aus dem Original erzeugt).

  python3 tools/xmas.py aufzeichnen karteNN   # welche Bilddateien laedt der Bau? -> maps/karteNN_xmas/dateien.json
  python3 tools/xmas.py erzeugen karteNN      # PixelLab: Xmas-Fassung jeder Datei -> assets_xmas/<gleicher Pfad>
  python3 tools/xmas.py bauen karteNN         # Karte mit den Xmas-Dateien bauen -> maps/karteNN_xmas/terrain.png

Funktionsweise: PIL.Image.open wird umgelenkt - jede Datei unter assets/, fuer die es unter assets_xmas/ eine
Xmas-Fassung gibt, wird durch diese ersetzt. Der Bau der Karte selbst bleibt unveraendert (gleiche Wege, Uebergaenge,
Objektpositionen). Bodenkacheln werden als 3x3-Mosaik bearbeitet und die Mitte genommen (bleibt nahtlos).
"""
import importlib, io, json, os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ASSETS = os.path.join(ROOT, 'assets')
XMAS = os.path.join(ROOT, 'assets_xmas')
_open = Image.open
_log = None


def _umgelenkt(fp, *a, **k):
    if isinstance(fp, (str, os.PathLike)):
        p = os.path.normpath(os.path.abspath(str(fp)))
        if p.startswith(ASSETS + os.sep):
            if _log is not None:
                _log.add(os.path.relpath(p, ASSETS))
            x = os.path.join(XMAS, os.path.relpath(p, ASSETS))
            if _log is None and os.path.exists(x):
                return _open(x, *a, **k)
    return _open(fp, *a, **k)


def _modul(karte):
    nr = karte.replace('karte', '')
    if nr == '01':
        import karte_bauen as m
    else:
        m = importlib.import_module('karte%s_bauen' % nr)
    return m


def _umlenken(m, karte):
    ziel = os.path.join(ROOT, 'maps', karte + '_xmas')
    os.makedirs(ziel, exist_ok=True)
    quelle = getattr(m, 'KARTE', os.path.join(ROOT, 'maps', karte))
    import shutil
    for f in os.listdir(quelle):                                         # Layout/Hoehen der Originalkarte mitnehmen
        if f.endswith(('.json', '.npy')) and not os.path.exists(os.path.join(ziel, f)):
            shutil.copy(os.path.join(quelle, f), os.path.join(ziel, f))
    for attr in ('KARTE', 'OUT_DIR', 'MAP_DIR'):
        if hasattr(m, attr):
            setattr(m, attr, ziel)
    return ziel


def aufzeichnen(karte):
    global _log
    _log = set()
    Image.open = _umgelenkt
    m = _modul(karte)
    ziel = _umlenken(m, karte)
    try:
        m.bauen(frame=0, speichern=False)
    finally:
        Image.open = _open
    dateien = sorted(_log)
    _log = None
    json.dump(dateien, open(os.path.join(ziel, 'dateien.json'), 'w'), indent=0)
    print(karte, len(dateien), 'Dateien')
    return dateien


BODEN_WOERTER = {
    'wasser': 'the water is frozen into smooth light blue ice with white frost streaks and faint cracks, no waves',
    'meer': 'the sea gets drifting ice floes and a cold dark blue tone, a little frost at the edges',
    'sand': 'a trampled snowy path, packed snow slightly more blue-grey than fresh snow, subtle tread marks, low contrast',
    'weg': 'a trampled snowy path, packed snow slightly more blue-grey than fresh snow, subtle tread marks, low contrast',
    'gras': 'covered by fresh soft snow, white with light blue shading and a few tiny grass tips poking through',
    'kies': 'the same stones with small snow caps and snow in the gaps',
    'stein': 'the same stones with small snow caps and snow in the gaps',
    'platz': 'a light dusting of snow and frost, the seams still visible',
    'asphalt': 'dark asphalt with a thin layer of slushy snow along the edges and some frost, mostly still dark',
}
BODEN_STANDARD = ('keep the original material, colours and pattern clearly visible and unchanged; only add a few soft '
                  'patches of snow and white frost along edges, seams and cracks. Do not add dots, circles or any new pattern')


def _ist_kachel(rel, im):
    return not rel.startswith('objekte' + os.sep) and im.size[0] <= 64 and im.size[1] <= 64


def _anweisung_boden(rel):
    name = os.path.basename(rel).lower()
    for w, t in BODEN_WOERTER.items():
        if w in name:
            return t
    return BODEN_STANDARD


OBJ_ANWEISUNG = ('Christmas winter edition of this exact object: add fresh white snow on its top surfaces (roofs, '
                 'tree crowns, ledges, tops), a few icicles where fitting; keep the exact same shape, size, outline, '
                 'position and pixel art style, do not add new objects.')


def _eine(rel):
    try:
        _eine_(rel)
    except Exception as e:                                             # eine Datei darf den Rest nicht aufhalten
        print('  FEHLER', rel, str(e)[:120], flush=True)


def _eine_(rel):
    from pixellab_edit import bearbeiten
    quelle = os.path.join(ASSETS, rel)
    ziel = os.path.join(XMAS, rel)
    if os.path.exists(ziel):
        return
    im = _open(quelle)
    modus = im.mode
    im = im.convert('RGBA')
    os.makedirs(os.path.dirname(ziel), exist_ok=True)
    if _ist_kachel(rel, im):
        w, h = im.size
        a = np.array(im)
        deckend = (a[..., 3] == 255).all()
        if deckend and w * 3 <= 256 and h * 3 <= 256:
            mosaik = Image.fromarray(np.tile(a, (3, 3, 1)))
            out = bearbeiten(mosaik, 'Christmas winter edition of this ground tile: ' + _anweisung_boden(rel) +
                             '. Keep the exact same pixel art style and size; it must stay a seamless ground tile.',
                             hintergrund=True)
            out = out.crop((w, h, 2 * w, 2 * h))
        else:
            out = bearbeiten(im, 'Christmas winter edition: ' + _anweisung_boden(rel) +
                             '. Keep the exact same pixel art style, size and outline.', hintergrund=not deckend)
            if not deckend:
                o = np.array(out); o[a[..., 3] == 0] = 0; out = Image.fromarray(o)
    else:
        if max(im.size) > 256:
            print('  zu gross, uebersprungen:', rel); return
        out = bearbeiten(im, OBJ_ANWEISUNG, hintergrund=False)
        a = np.array(im)[..., 3] > 0
        rein = a.copy(); rein[:-1] |= a[1:]                               # Umriss bleibt (+1 px Schneekappe oben)
        o = np.array(out); o[~rein] = 0; out = Image.fromarray(o)
    if modus == 'RGB':
        out = out.convert('RGB')
    out.save(ziel)
    print('  ', rel, flush=True)


def erzeugen(karte, ausnahmen=()):
    ziel = os.path.join(ROOT, 'maps', karte + '_xmas')
    dateien = json.load(open(os.path.join(ziel, 'dateien.json')))
    todo = [d for d in dateien if not os.path.exists(os.path.join(XMAS, d)) and not any(x in d for x in ausnahmen)]
    print(karte, len(todo), 'Dateien fuer PixelLab')
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(_eine, todo))


def bauen(karte, frame=None):
    Image.open = _umgelenkt
    try:
        m = _modul(karte)
        ziel = _umlenken(m, karte)
        img = m.bauen(frame=frame, speichern=frame is None)
    finally:
        Image.open = _open
    return img


if __name__ == '__main__':
    befehl, karte = sys.argv[1], sys.argv[2]
    {'aufzeichnen': aufzeichnen, 'erzeugen': erzeugen, 'bauen': bauen}[befehl](karte)
