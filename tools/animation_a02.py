"""Animierte Fassung einer A02-Karte (ohne eigenes Animationsskript) und Discord-GIF - 4 Bilder (Regel), 250 ms.

  python3 tools/animation_a02.py karte21        (karte21, karte23 ... karte27, karte30)

Ruft karteNN_bauen.bauen(frame=f, speichern=False) fuer jedes Bild auf (alles, was die Karte animiert: Wasser,
Wasserfaelle, Laternen, Feuer, Baeume im Wind, Portale ...), speichert maps/karteNN/animation/karteNN_animiert.webp
und karteNN_discord.gif (2x vergroessert, unter 10 MB) sowie optionale Detail-GIFs (DETAILS).
Zum Schluss wird geprueft, welche Objekte sich zwischen den Bildern wirklich veraendern (Regel: jedes animierte
Objekt bewegt sich im GIF).
"""
import importlib, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import animation_bauen as ab

DETAILS = {   # Kachel-Ausschnitte (x0, y0, x1, y1) fuer Detail-GIFs
    'karte30': {'riesenrad': (94, 40, 120, 68), 'strand': (40, 82, 80, 110)},
}


def main(karte):
    k = importlib.import_module('%s_bauen' % karte)
    n = getattr(k, 'N_FRAMES', 4)
    dauer = getattr(k, 'BILDDAUER', 250)
    out = os.path.join(k.KARTE, 'animation')
    os.makedirs(out, exist_ok=True)
    t0 = time.time()
    frames = []
    for f in range(n):
        frames.append(k.bauen(frame=f, speichern=False).convert('RGB'))
        print('%s Frame %d/%d (%.0fs)' % (karte, f + 1, n, time.time() - t0), flush=True)
    frames[0].save(os.path.join(out, '%s_animiert.webp' % karte), save_all=True, append_images=frames[1:],
                   duration=dauer, loop=0, lossless=True, method=4)
    alt = (ab.OUT, ab.DAUER)
    ab.OUT, ab.DAUER = out, dauer
    ab.discord_gif([fr.resize((fr.width * 2, fr.height * 2), Image.NEAREST) for fr in frames])
    os.replace(os.path.join(out, 'karte01_discord.gif'), os.path.join(out, '%s_discord.gif' % karte))
    ab.OUT, ab.DAUER = alt
    for name, (x0, y0, x1, y1) in DETAILS.get(karte, {}).items():
        box = (x0 * 16, y0 * 16, x1 * 16, y1 * 16)
        teil = [fr.crop(box).resize(((x1 - x0) * 32, (y1 - y0) * 32), Image.NEAREST)
                .quantize(colors=255, method=Image.Quantize.MAXCOVERAGE) for fr in frames]
        teil[0].save(os.path.join(out, 'detail_%s.gif' % name), save_all=True, append_images=teil[1:],
                     duration=dauer, loop=0, disposal=1)
    # Pruefung: bewegt sich jedes animierte Objekt?
    arr = [np.asarray(fr).astype(int) for fr in frames]
    pf = os.path.join(os.path.dirname(k.KARTE), '..', 'assets', 'objekte', karte, 'platzierung.json')
    stumm = []
    if os.path.exists(pf):
        for o in json.load(open(pf)):
            if not o.get('anim'):
                continue
            try:
                w, h = Image.open(os.path.join(os.path.dirname(pf), o['datei'])).size
            except OSError:
                continue
            x0, y0 = max(0, o['x']), max(0, o['y'])
            x1, y1 = min(arr[0].shape[1], o['x'] + w), min(arr[0].shape[0], o['y'] + h)
            if x1 <= x0 or y1 <= y0:
                continue
            diff = max(np.abs(arr[i][y0:y1, x0:x1] - arr[0][y0:y1, x0:x1]).sum() for i in range(1, len(arr)))
            if diff == 0:
                stumm.append('%s (%s)' % (o['basis'], o['anim']))
    gif = os.path.join(out, '%s_discord.gif' % karte)
    print('%s fertig: %d Bilder, GIF %.1f MB, %d animierte Objekte ohne Bewegung%s' % (
        karte, n, os.path.getsize(gif) / 1e6, len(stumm), (': ' + ', '.join(sorted(set(stumm)))) if stumm else ''))


if __name__ == '__main__':
    main(sys.argv[1])
