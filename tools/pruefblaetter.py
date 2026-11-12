"""Pruefblaetter fuer alle animierten Objekte einer Karte aus der echten 16-Bilder-Animation.
  python3 tools/pruefblaetter.py karteNN [zielordner]  -> zielordner/karteNN/<nr>_<basis>.png (Bilder 0,3,6,9,12 + rote Differenzmaske, vergroessert)
Je (basis, anim/teil) ein Exemplar (max. 3 Exemplare, wenn gespiegelt/verschieden)."""
import json, os, sys
import numpy as np
from PIL import Image, ImageSequence, ImageDraw
R = '/home/user/DBC'
karte = sys.argv[1]
OUT = os.path.join(sys.argv[2] if len(sys.argv) > 2 else '/tmp/pruef', karte)
os.makedirs(OUT, exist_ok=True)
fr = [np.array(f.convert('RGB')) for f in ImageSequence.Iterator(Image.open('%s/maps/%s/animation/%s_animiert_16.webp' % (R, karte, karte)))]
objs = json.load(open('%s/assets/objekte/%s/platzierung.json' % (R, karte)))
gesehen = {}
n = 0
for o in objs:
    a = o.get('anim') or o.get('teil')
    if not a:
        continue
    key = (o['basis'], a, '_m.' in o['datei'])
    if gesehen.get(key, 0) >= 1:
        continue
    gesehen[key] = 1
    w, h = Image.open('%s/assets/objekte/%s/%s' % (R, karte, o['datei'])).size
    x0, y0 = max(0, o['x'] - 10), max(0, o['y'] - 10)
    x1, y1 = min(fr[0].shape[1], o['x'] + w + 10), min(fr[0].shape[0], o['y'] + h + 10)
    if x1 <= x0 or y1 <= y0:
        continue
    cs = [f[y0:y1, x0:x1] for f in fr]
    d = np.max([np.abs(c.astype(int) - cs[0].astype(int)).sum(2) for c in cs], 0) > 0
    dm = (cs[0] // 3).copy(); dm[d] = (255, 0, 0)
    teile = [cs[i] for i in (0, 3, 6, 9, 12)] + [dm]
    sc = 4 if max(w, h) < 48 else (3 if max(w, h) < 90 else 2)
    pad = np.zeros((y1 - y0, 3, 3), np.uint8)
    zeile = np.concatenate(sum([[t, pad] for t in teile], [])[:-1], 1)
    im = Image.fromarray(zeile).resize((zeile.shape[1] * sc, zeile.shape[0] * sc), Image.NEAREST)
    kopf = Image.new('RGB', (im.width, 14), (0, 0, 0))
    ImageDraw.Draw(kopf).text((2, 1), '%s anim=%s teil=%s datei=%s x=%d y=%d (Bilder 0,3,6,9,12 | rot=bewegt)' % (
        o['basis'], o.get('anim'), o.get('teil'), o['datei'], o['x'], o['y']), fill=(255, 255, 0))
    ges = Image.new('RGB', (im.width, im.height + 14)); ges.paste(kopf, (0, 0)); ges.paste(im, (0, 14))
    n += 1
    ges.save(os.path.join(OUT, '%03d_%s_%s.png' % (n, o['basis'].replace('/', '-'), a)))
print(karte, n, 'Blaetter ->', OUT)
