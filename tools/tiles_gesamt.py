"""Alle Kacheln und Objekte aller Karten in einem Ordner, am 16x16-Raster -> maps/tiles_gesamt/ + 2 ZIPs

  python3 tools/tiles_gesamt.py

Quelle: die Tilesets der Karten (maps/karteNN/tileset/, Format von tools/tileset_export.py; Karte 01 im alten Format
mit boden_tiles.png / ueberlagerung_tiles.png / objekte/). Gleiche Kacheln (Pixel fuer Pixel) werden nur einmal
abgelegt; index.json sagt fuer jede Kachel und jedes Objekt, aus welchen Karten es stammt.

  boden/statisch.png                  alle unbewegten Bodenkacheln, 64 je Zeile
  boden/karte01_ueberlagerung.png     Ueberlagerungs-Kacheln von Karte 01 (ueber dem Spieler)
  boden/animiert_4bilder.png          animierte Bodenkacheln mit 4 Bildern: Bild 0..3 untereinander, je Bild gleicher Platz
  boden/animiert_4bilder_frames/      dieselben Bilder einzeln
  boden/animiert_16bilder.png (+ _frames/)   animierte Bodenkacheln mit 16 Bildern (aeltere Karten)
  objekte/statisch.png                alle Objekte im eigenen Kachelblock (Regalpackung, 64 Kacheln breit)
  objekte/animiert_4bilder.png / _16bilder.png (+ _frames/)   animierte Objekte, Bilder untereinander
  objekte/karte01/                    Objekt-Sprites von Karte 01 (einzeln)
  index.json, README.md, vorschau.png
ZIPs: maps/tiles_gesamt_teil1.zip (Boden statisch + 4 Bilder, alle Blaetter, Objekte statisch + 4 Bilder) und
maps/tiles_gesamt_teil2.zip (Einzelbilder der 16-Bilder-Animationen, animierte Objekte mit 16 Bildern) - je unter 50 MB.
"""
import hashlib, json, os, shutil, zipfile
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MAPS = os.path.join(ROOT, 'maps')
OUT = os.path.join(MAPS, 'tiles_gesamt')
T = 16
B = 64                                            # Kacheln je Zeile in den Sammelblaettern
NAMEN = {'karte01': 'Wald und Strand', 'karte02': 'Factorial Town', 'karte03': 'Server Desert', 'karte04': 'Gear Savanna',
         'karte05': 'Freezeland', 'karte06': 'Startkarte', 'karte07': 'The Holy Peaks', 'karte08': 'Overdell',
         'karte09': "Vamdemon's Keep", 'karte10': 'Toy Town', 'karte11': 'Spiral Mountain: Dark Ocean',
         'karte12': 'Spiral Mountain: Puppet Woods', 'karte13': 'Spiral Mountain: Machine City',
         'karte14': 'Spiral Mountain: Summit', 'karte15': "Apocalymon's Realm", 'karte16': 'The Network',
         'karte17': 'Our War Game!', 'karte18': 'The Fog-Bound City', 'karte19': 'Revenge', 'karte20': 'Startdorf',
         'karte21': 'Digi-Egg Valley', 'karte23': 'Harvest Hills', 'karte24': "The Kaiser's Canyon", 'karte25': 'Sunset Bay',
         'karte26': "The Kaiser's Fortress", 'karte27': 'Destiny Lake', 'karte28': 'Tower Forest',
         'karte29': 'The Sea of Darkness', 'karte30': 'Odaiba', 'karte31': 'Highton View Terrace', 'karte32': 'Dream Ruins',
         'karte33': 'The World of Dreams'}


def kacheln_aus(img, anzahl=None, start_reihe=0, breite=None):
    a = np.array(img.convert('RGBA'))
    w = breite or a.shape[1] // T
    out = []
    reihen = a.shape[0] // T
    for r in range(start_reihe, reihen):
        for c in range(w):
            k = a[r * T:(r + 1) * T, c * T:(c + 1) * T]
            if k.shape[:2] != (T, T):
                continue
            out.append(k)
            if anzahl is not None and len(out) >= anzahl:
                return out
    return out


def leer(k):
    return k[..., 3].max() == 0


def blatt(kacheln, breite=B):
    n = max(1, len(kacheln))
    reihen = (n + breite - 1) // breite
    a = np.zeros((reihen * T, breite * T, 4), np.uint8)
    for i, k in enumerate(kacheln):
        r, c = divmod(i, breite)
        a[r * T:(r + 1) * T, c * T:(c + 1) * T] = k
    return Image.fromarray(a, 'RGBA')


def regal(bloecke, breite=B):
    """Regalpackung: Bloecke (Breite/Hoehe in Kacheln) zeilenweise, hoechste zuerst -> Positionen in Kacheln."""
    reihenfolge = sorted(range(len(bloecke)), key=lambda i: (-bloecke[i][1], -bloecke[i][0]))
    pos = [None] * len(bloecke)
    x = y = zh = 0
    for i in reihenfolge:
        w, h = bloecke[i]
        w = min(w, breite)
        if x + w > breite:
            x, y, zh = 0, y + zh, 0
        pos[i] = (x, y)
        x += w
        zh = max(zh, h)
    return pos, y + zh


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for d in ('boden', 'objekte'):
        os.makedirs(os.path.join(OUT, d))
    karten = sorted(k for k in os.listdir(MAPS) if k.startswith('karte') and os.path.isdir(os.path.join(MAPS, k, 'tileset')))
    stat, stat_herkunft = [], {}                               # hash -> index
    ueber, ueber_h = [], {}
    anim = {4: [], 16: []}                                     # je Bildzahl: Liste von Bildfolgen
    anim_h = {4: {}, 16: {}}
    herkunft_anim = {4: [], 16: []}
    stat_karten = []
    obj_stat, obj_anim = [], {4: [], 16: []}                  # (Kachelblock-Bild bzw. Bildfolge, Infos)
    obj_hash = {}
    k01_obj = []
    for karte in karten:
        td = os.path.join(MAPS, karte, 'tileset')
        if karte == 'karte01':                                 # altes Format
            for k in kacheln_aus(Image.open(os.path.join(td, 'boden_tiles.png'))):
                if leer(k):
                    continue
                h = hashlib.md5(k.tobytes()).hexdigest()
                if h not in stat_herkunft:
                    stat_herkunft[h] = len(stat); stat.append(k); stat_karten.append(set())
                stat_karten[stat_herkunft[h]].add(karte)
            for k in kacheln_aus(Image.open(os.path.join(td, 'ueberlagerung_tiles.png'))):
                if leer(k):
                    continue
                h = hashlib.md5(k.tobytes()).hexdigest()
                if h not in ueber_h:
                    ueber_h[h] = len(ueber); ueber.append(k)
            k01_obj = sorted(f for f in os.listdir(os.path.join(td, 'objekte')) if f.endswith('.png'))
            print(karte, 'altes Format:', len(stat), 'Kacheln bisher', flush=True)
            continue
        br = json.load(open(os.path.join(td, 'boden_raster.json')))
        n_bild = br['animationsbilder']
        ah = br['animationsbereich_hoehe_kacheln']
        bt = Image.open(os.path.join(td, 'boden_tileset.png'))
        bw = br.get('breite_kacheln', 32)
        for k in kacheln_aus(bt, br['unbewegte_kacheln'], start_reihe=ah, breite=bw):
            h = hashlib.md5(k.tobytes()).hexdigest()
            if h not in stat_herkunft:
                stat_herkunft[h] = len(stat); stat.append(k); stat_karten.append(set())
            stat_karten[stat_herkunft[h]].add(karte)
        if br['animierte_kacheln']:
            ba = np.array(Image.open(os.path.join(td, 'boden_tileset_animiert.png')).convert('RGBA'))
            fh = ah * T
            nb = n_bild if n_bild in (4, 16) else 4
            for i in range(br['animierte_kacheln']):
                r, c = divmod(i, bw)
                folge = [ba[f * fh + r * T:f * fh + (r + 1) * T, c * T:(c + 1) * T] for f in range(n_bild)]
                if n_bild not in (4, 16):
                    folge = [folge[f * n_bild // 4] for f in range(4)]
                h = hashlib.md5(b''.join(x.tobytes() for x in folge)).hexdigest()
                if h not in anim_h[nb]:
                    anim_h[nb][h] = len(anim[nb]); anim[nb].append(folge); herkunft_anim[nb].append(set())
                herkunft_anim[nb][anim_h[nb][h]].add(karte)
        if not os.path.exists(os.path.join(td, 'objekte_tileset.json')):   # Karte ohne Objekte (z. B. 17)
            print(karte, len(stat), 'Boden statisch (keine Objekte)', flush=True)
            continue
        oj = json.load(open(os.path.join(td, 'objekte_tileset.json')))
        os_ = np.array(Image.open(os.path.join(td, 'objekte_tileset.png')).convert('RGBA'))
        oa_p = os.path.join(td, 'objekte_tileset_animiert.png')
        oa = np.array(Image.open(oa_p).convert('RGBA')) if os.path.exists(oa_p) else None
        oah = oj.get('animationsbereich_hoehe_kacheln', 0) * T
        onb = oj.get('animationsbilder', 4)
        for o in oj['objekte']:
            s = o['slot_kacheln']
            x0, y0, w, h = s['x'] * T, s['y'] * T, s['breite'] * T, s['hoehe'] * T
            if o.get('animation') and oa is not None and y0 + h <= oah:
                folge = [oa[f * oah + y0:f * oah + y0 + h, x0:x0 + w] for f in range(onb)]
                if onb not in (4, 16):
                    folge = [folge[f * onb // 4] for f in range(4)]
                nb = onb if onb in (4, 16) else 4
                hs = hashlib.md5(b''.join(x.tobytes() for x in folge)).hexdigest()
                if hs in obj_hash:
                    obj_hash[hs]['karten'].append(karte); continue
                info = {'name': o['name'], 'karte': karte, 'karten': [karte], 'animation': o['animation'],
                        'breite': s['breite'], 'hoehe': s['hoehe'], 'bilder': nb}
                obj_hash[hs] = info
                obj_anim[nb].append((folge, info))
            else:
                bild = os_[y0:y0 + h, x0:x0 + w]
                if bild.shape[:2] != (h, w) or bild[..., 3].max() == 0:
                    continue
                hs = hashlib.md5(bild.tobytes()).hexdigest()
                if hs in obj_hash:
                    obj_hash[hs]['karten'].append(karte); continue
                info = {'name': o['name'], 'karte': karte, 'karten': [karte], 'animation': None,
                        'breite': s['breite'], 'hoehe': s['hoehe']}
                obj_hash[hs] = info
                obj_stat.append((bild, info))
        print(karte, len(stat), 'Boden statisch,', len(anim[4]) + len(anim[16]), 'animiert,', len(obj_stat),
              'Objekte,', len(obj_anim[4]) + len(obj_anim[16]), 'animierte Objekte', flush=True)
    index = {'kachel': T, 'karten': {k: NAMEN.get(k, k) for k in karten}, 'boden_statisch': [], 'boden_animiert': {},
             'objekte_statisch': [], 'objekte_animiert': {}}
    # --- Boden
    blatt(stat).save(os.path.join(OUT, 'boden', 'statisch.png'), optimize=True)
    index['boden_statisch'] = [{'i': i, 'x': i % B, 'y': i // B, 'karten': sorted(stat_karten[i])} for i in range(len(stat))]
    if ueber:
        blatt(ueber).save(os.path.join(OUT, 'boden', 'karte01_ueberlagerung.png'), optimize=True)
    for nb in (4, 16):
        if not anim[nb]:
            continue
        frames = [blatt([f[b] for f in anim[nb]]) for b in range(nb)]
        fd = os.path.join(OUT, 'boden', 'animiert_%dbilder_frames' % nb)
        os.makedirs(fd)
        for b, fr in enumerate(frames):
            fr.save(os.path.join(fd, 'frame_%02d.png' % b), optimize=True)
        ges = Image.new('RGBA', (frames[0].width, frames[0].height * nb))
        for b, fr in enumerate(frames):
            ges.paste(fr, (0, b * fr.height))
        ges.save(os.path.join(OUT, 'boden', 'animiert_%dbilder.png' % nb), optimize=True)
        index['boden_animiert']['%d' % nb] = {'bildhoehe_kacheln': frames[0].height // T, 'kacheln': [
            {'i': i, 'x': i % B, 'y': i // B, 'karten': sorted(herkunft_anim[nb][i])} for i in range(len(anim[nb]))]}
    # --- Objekte statisch
    pos, hoehe = regal([(i['breite'], i['hoehe']) for _, i in obj_stat])
    a = np.zeros((max(1, hoehe) * T, B * T, 4), np.uint8)
    for (bild, info), (x, y) in zip(obj_stat, pos):
        h_, w_ = bild.shape[:2]
        w_ = min(w_, B * T - x * T)
        a[y * T:y * T + h_, x * T:x * T + w_] = bild[:, :w_]
        info.update({'x': x, 'y': y})
        index['objekte_statisch'].append(info)
    Image.fromarray(a, 'RGBA').save(os.path.join(OUT, 'objekte', 'statisch.png'), optimize=True)
    for nb in (4, 16):
        if not obj_anim[nb]:
            continue
        pos, hoehe = regal([(i['breite'], i['hoehe']) for _, i in obj_anim[nb]])
        frames = [np.zeros((max(1, hoehe) * T, B * T, 4), np.uint8) for _ in range(nb)]
        for (folge, info), (x, y) in zip(obj_anim[nb], pos):
            for b in range(nb):
                h_, w_ = folge[b].shape[:2]
                w_ = min(w_, B * T - x * T)
                frames[b][y * T:y * T + h_, x * T:x * T + w_] = folge[b][:, :w_]
            info.update({'x': x, 'y': y})
        index['objekte_animiert']['%d' % nb] = {'bildhoehe_kacheln': hoehe, 'objekte': [i for _, i in obj_anim[nb]]}
        fd = os.path.join(OUT, 'objekte', 'animiert_%dbilder_frames' % nb)
        os.makedirs(fd)
        for b, fr in enumerate(frames):
            Image.fromarray(fr, 'RGBA').save(os.path.join(fd, 'frame_%02d.png' % b), optimize=True)
        Image.fromarray(np.concatenate(frames, 0), 'RGBA').save(
            os.path.join(OUT, 'objekte', 'animiert_%dbilder.png' % nb), optimize=True)
    if k01_obj:
        d = os.path.join(OUT, 'objekte', 'karte01')
        os.makedirs(d)
        for f in k01_obj:
            shutil.copy(os.path.join(MAPS, 'karte01', 'tileset', 'objekte', f), os.path.join(d, f))
    json.dump(index, open(os.path.join(OUT, 'index.json'), 'w'), ensure_ascii=False, indent=1)
    # --- Vorschau (verkleinert) und README
    v = Image.open(os.path.join(OUT, 'boden', 'statisch.png'))
    o = Image.open(os.path.join(OUT, 'objekte', 'statisch.png'))
    vor = Image.new('RGBA', (v.width + o.width + 16, max(v.height, o.height)), (30, 30, 40, 255))
    vor.alpha_composite(v, (0, 0)); vor.alpha_composite(o, (v.width + 16, 0))
    vor.thumbnail((2400, 2400))
    vor.save(os.path.join(OUT, 'vorschau.png'))
    n_anim = {nb: len(anim[nb]) for nb in (4, 16)}
    n_oanim = {nb: len(obj_anim[nb]) for nb in (4, 16)}
    readme = README % dict(karten=len(karten), stat=len(stat), ueber=len(ueber), a4=n_anim[4], a16=n_anim[16],
                           obj=len(obj_stat), oa4=n_oanim[4], oa16=n_oanim[16], k01=len(k01_obj),
                           liste='\n'.join('- %s - %s' % (k, NAMEN.get(k, k)) for k in karten))
    open(os.path.join(OUT, 'README.md'), 'w').write(readme)
    # --- ZIPs
    for alt_ in ('tiles_gesamt_1_boden.zip', 'tiles_gesamt_2_objekte.zip'):
        if os.path.exists(os.path.join(MAPS, alt_)):
            os.remove(os.path.join(MAPS, alt_))
    teil1 = ['boden/statisch.png', 'boden/karte01_ueberlagerung.png', 'boden/animiert_4bilder.png',
             'boden/animiert_4bilder_frames', 'boden/animiert_16bilder.png', 'objekte/statisch.png', 'objekte/karte01',
             'objekte/animiert_4bilder.png', 'objekte/animiert_4bilder_frames']
    teil2 = ['boden/animiert_16bilder_frames', 'objekte/animiert_16bilder.png', 'objekte/animiert_16bilder_frames']
    for name, teile in (('tiles_gesamt_teil1.zip', teil1), ('tiles_gesamt_teil2.zip', teil2)):
        p = os.path.join(MAPS, name)
        with zipfile.ZipFile(p, 'w', zipfile.ZIP_DEFLATED) as z:
            for f in ('README.md', 'index.json', 'vorschau.png'):
                z.write(os.path.join(OUT, f), os.path.join('tiles_gesamt', f))
            for t in teile:
                if os.path.isfile(os.path.join(OUT, t)):
                    z.write(os.path.join(OUT, t), os.path.join('tiles_gesamt', t))
                    continue
                for wurzel, _, dateien in os.walk(os.path.join(OUT, t)):
                    for f in sorted(dateien):
                        q = os.path.join(wurzel, f)
                        z.write(q, os.path.join('tiles_gesamt', os.path.relpath(q, OUT)))
        print(name, '%.1f MB' % (os.path.getsize(p) / 1e6))


README = """# Alle Tiles (16 x 16) - %(karten)s Karten

Alle Kacheln und Objekte aus den Tilesets der Karten in einem Ordner, am 16x16-Raster. Gleiche Kacheln (Pixel fuer
Pixel) liegen nur einmal vor; `index.json` sagt fuer jede Kachel und jedes Objekt, aus welchen Karten es stammt.

| Ordner/Datei | Inhalt |
|---|---|
| `boden/statisch.png` | %(stat)s unbewegte Bodenkacheln, 64 je Zeile |
| `boden/karte01_ueberlagerung.png` | %(ueber)s Ueberlagerungs-Kacheln von Karte 01 (liegen ueber dem Spieler) |
| `boden/animiert_4bilder.png` + `_frames/` | %(a4)s animierte Bodenkacheln, 4 Bilder (Bild 0-3 untereinander, gleicher Platz) |
| `boden/animiert_16bilder.png` + `_frames/` | %(a16)s animierte Bodenkacheln, 16 Bilder (aeltere Karten) |
| `objekte/statisch.png` | %(obj)s Objekte, jedes in seinem eigenen Kachelblock (Breite/Hoehe in index.json) |
| `objekte/animiert_4bilder.png` + `_frames/` | %(oa4)s animierte Objekte, 4 Bilder |
| `objekte/animiert_16bilder.png` + `_frames/` | %(oa16)s animierte Objekte, 16 Bilder |
| `objekte/karte01/` | %(k01)s Objekt-Sprites von Karte 01 einzeln |
| `index.json` | Position (x, y in Kacheln), Groesse, Animation und Herkunft jeder Kachel / jedes Objekts |
| `vorschau.png` | verkleinerte Uebersicht |

Animierte Blaetter: alle Bilder einer Animation liegen untereinander; Bild b einer Kachel steht bei
y + b x (Bildhoehe), x gleich. Laufzeit: 4 Bilder 250 ms, 16 Bilder 110-170 ms je Bild.

Aufteilung (je unter 50 MB): `tiles_gesamt_teil1.zip` enthaelt alle Blaetter (Boden statisch, Ueberlagerung, Boden
4 und 16 Bilder als Gesamtblatt, Objekte statisch und 4 Bilder) samt Einzelbildern der 4-Bilder-Animationen;
`tiles_gesamt_teil2.zip` enthaelt die Einzelbilder der 16-Bilder-Bodenanimation und die animierten Objekte mit 16
Bildern. Beide ZIPs in denselben Ordner entpacken - sie ergaenzen sich zu `tiles_gesamt/`.

Karten:
%(liste)s

Erzeugt mit `tools/tiles_gesamt.py` aus `maps/karteNN/tileset/`.
"""

if __name__ == '__main__':
    main()
