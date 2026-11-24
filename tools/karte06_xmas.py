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
    'eis': ('assets/basis/wasser_%d.png', 2, None,
            'Christmas winter edition of this pond water tile: the water is frozen solid into smooth light blue ice '
            'with a few white frost streaks and faint cracks, no waves.'),
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


_K6 = None


def bauen_vorbereiten():
    global _K6
    if _K6 is not None:
        return _K6
    import karte06_bauen as k6
    os.makedirs(KARTE_NEU, exist_ok=True)
    shutil.copy(os.path.join(k6.KARTE, 'layout.json'), os.path.join(KARTE_NEU, 'layout.json'))
    ersatz = {os.path.normpath(os.path.join(ROOT, m)): name for name, (m, n, u, a) in GRUNDKACHELN.items()}
    orig = k6.kacheln

    def kacheln_xmas(pfad, n, umfaerben=None):
        name = ersatz.get(os.path.normpath(pfad))
        if name is None:
            return orig(pfad, n, umfaerben)
        datei = 'weg' if name == 'sand' else name                       # Nutzer: Wege ruhiger (zweite PixelLab-Runde 'weg')
        ks = [np.array(Image.open(os.path.join(XK, '%s_%d.png' % (datei, v))).convert('RGB')) for v in AUSWAHL[name]]
        if name == 'sand':                                             # gedreht/gespiegelt: kein sichtbares Raster
            k = ks[0]
            ks = [k, np.rot90(k, 1).copy(), np.rot90(k, 2).copy(), k[:, ::-1].copy(), np.rot90(k, 3).copy()]
        return ks
    k6.kacheln = kacheln_xmas
    # Nutzer: Teich zugefroren - das Wasser des vertieften Teichs wird durch die PixelLab-Eiskachel ersetzt
    # (Helligkeit der Tiefenstufen bleibt erhalten, Erdrand und Steg bleiben), ohne Wellen-Animation
    import wasser_vertieft
    if not getattr(wasser_vertieft, '_xmas', False):
        orig_v = wasser_vertieft.vertiefen
        eis = [np.array(Image.open(os.path.join(XK, 'eis_%d.png' % v)).convert('RGB')).astype(np.float32) for v in (0, 1)]

        def vertiefen_eis(img, region, frame=None, maske=None, **kw):
            out = orig_v(img, region, None, maske=maske, **kw)
            a = np.array(out.convert('RGB')).astype(np.float32)
            Hh, W = a.shape[:2]
            tex = np.zeros_like(a)
            for y in range(0, Hh, 16):
                for x in range(0, W, 16):
                    tex[y:y + 16, x:x + 16] = eis[((x // 16) * 7 + (y // 16) * 3) % 2][:min(16, Hh - y), :min(16, W - x)]
            blau = (a[..., 2] > a[..., 0] + 25) & (a[..., 2] > a[..., 1])
            if maske is not None:
                blau &= maske
            hell = a[..., :3].mean(-1, keepdims=True)
            ref = np.median(hell[blau]) if blau.any() else 1.0
            f = np.clip(0.75 + 0.25 * hell / max(ref, 1.0), 0.6, 1.1)
            a[blau] = np.clip(tex * f, 0, 255)[blau]
            return Image.fromarray(a.astype(np.uint8)).convert(out.mode)
        wasser_vertieft.vertiefen = vertiefen_eis
        wasser_vertieft._xmas = True
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
    _K6 = k6
    return k6


def bild(frame=None):
    k6 = bauen_vorbereiten()
    img = k6.bauen(frame=frame, speichern=frame is None)
    if frame is not None:
        import karte05_bauen as k5
        img = img.convert('RGBA')
        xmas_lichter(img, frame)                                       # Lichterkette blinkt, Stern pulsiert
        eis_glitzern(img, frame)                                       # Eis auf dem See glitzert
        k5.schneefall(img, frame)                                      # Nutzer: Xmas - es schneit
    return img


def xmas_lichter(img, frame):
    """Weihnachtsbaum: die bunten Lichter (gesaettigte helle Pixel in der Krone) blinken in vier Gruppen versetzt,
    der Stern an der Spitze pulsiert mit weichem Schein. Nur die Lichtpixel aendern sich (Regel: nur die Lichtquelle)."""
    import math
    from PIL import ImageDraw, ImageFilter
    p = json.load(open(os.path.join(OBJ_NEU, 'platzierung.json')))
    o = next((o for o in p if o.get('basis') == 'xmasbaum'), None)
    if o is None:
        return
    sp = np.array(Image.open(os.path.join(OBJ_NEU, o['datei'])).convert('RGBA')).astype(int)
    a = np.array(img).astype(int)
    h, w = sp.shape[:2]
    x0, y0 = o['x'], o['y']
    r, g, b = sp[..., 0], sp[..., 1], sp[..., 2]
    mx, mn = sp[..., :3].max(-1), sp[..., :3].min(-1)
    licht = (sp[..., 3] > 0) & (mx > 170) & (mx - mn > 70)
    stern_zeilen = int(h * 0.12)
    stern = licht.copy(); stern[stern_zeilen:] = False
    licht[:stern_zeilen] = False
    ys, xs = np.nonzero(licht)
    gruppe = ((xs * 7 + ys * 13) // 5) % 4
    an = gruppe == (frame % 4)
    aus = gruppe == ((frame + 2) % 4)
    Y, X = ys + y0, xs + x0
    ok = (Y >= 0) & (Y < a.shape[0]) & (X >= 0) & (X < a.shape[1])
    a[Y[ok & an], X[ok & an], :3] = np.minimum(255, sp[ys[ok & an], xs[ok & an], :3] * 1.35 + 40)
    a[Y[ok & aus], X[ok & aus], :3] = (sp[ys[ok & aus], xs[ok & aus], :3] * 0.55).astype(int)
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    sy, sx = np.nonzero(stern)
    if len(sy):                                                        # Stern: weicher Schein, pulsiert
        cx, cy = x0 + int(sx.mean()), y0 + int(sy.mean())
        k = 0.5 + 0.5 * math.sin(2 * math.pi * frame / 16.0)
        glow = Image.new('RGBA', out.size, (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse((cx - 14, cy - 14, cx + 14, cy + 14), fill=(255, 230, 120, int(60 + 70 * k)))
        glow = glow.filter(ImageFilter.GaussianBlur(5))
        out = out.convert('RGBA'); out.alpha_composite(glow)
    img.paste(out.convert(img.mode))


def eis_glitzern(img, frame):
    """Zugefrorener See: einzelne Eiskristalle blitzen kurz auf (je Stelle eigener Takt, nahtlos ueber 16 Bilder)."""
    pf = os.path.join(KARTE_NEU, 'wasser.npy')
    if not os.path.exists(pf):
        return
    a = np.array(img)
    Hh, W = a.shape[:2]
    m = np.unpackbits(np.load(pf))[:Hh * W].reshape(Hh, W).astype(bool)
    rs = np.random.RandomState(606)
    ys, xs = np.nonzero(m)
    if not len(ys):
        return
    idx = rs.choice(len(ys), min(60, len(ys)), replace=False)
    phase = rs.randint(0, 16, len(idx))
    for i, ph in zip(idx, phase):
        t = (frame - ph) % 16
        if t > 2:
            continue
        y, x = ys[i], xs[i]
        stark = 1.0 if t == 1 else 0.55
        for dy, dx, f in ((0, 0, 1.0), (-1, 0, 0.6), (1, 0, 0.6), (0, -1, 0.6), (0, 1, 0.6)):
            Y, X = y + dy, x + dx
            if 0 <= Y < Hh and 0 <= X < W and m[Y, X]:
                k = stark * f
                a[Y, X, :3] = (a[Y, X, :3] * (1 - k) + 255 * k).astype(np.uint8)
    img.paste(Image.fromarray(a))


def animation():
    import animation_bauen as ab
    out = os.path.join(KARTE_NEU, 'animation')
    os.makedirs(out, exist_ok=True)
    frames = [bild(f).convert('RGB') for f in range(16)]
    frames[0].save(os.path.join(out, 'karte06_xmas_animiert.webp'), save_all=True, append_images=frames[1:],
                   duration=170, loop=0, lossless=True, method=4)
    ab.OUT, ab.DAUER = out, 110
    ab.discord_gif(frames)
    os.replace(os.path.join(out, 'karte01_discord.gif'), os.path.join(out, 'karte06_xmas_discord_16.gif'))
    ab.DAUER = 440
    ab.discord_gif(frames[::4])
    os.replace(os.path.join(out, 'karte01_discord.gif'), os.path.join(out, 'karte06_xmas_discord.gif'))
    print('Animation fertig')


BAUM_NR = 0
AUSWAHL = {'gras': [0, 1, 3, 4], 'sand': [2], 'kies': [0, 3], 'platz': [0, 1, 2]}   # zueinander passende Varianten

if __name__ == '__main__':
    {'kacheln': kacheln, 'objekte': objekte, 'baum': baum, 'bauen': lambda: bild(None), 'animation': animation}[sys.argv[1]]()
