"""Animationsplan Karte 13: Uebersicht mit allen animierten Stellen + jede Animation einzeln als GIF-Kachel.

  python3 tools/karte14_animplan.py  ->  maps/karte14/animation/animationsplan.png, animationen_einzeln.gif
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import karte13_bauen as kb

OUT = os.path.join(kb.KARTE, 'animation')
T = 16
NAMEN = {'rotlicht': 'rote Lichter blinken', 'lampe': 'Laterne leuchtet', 'glimmen': 'Reaktor/Kristall glimmt',
         'feuer': 'Ofen: Feuer', 'konsole': 'Konsole: Lampen blinken', 'funken': 'Wrack: Funken spruehen',
         'ampel_blinken': 'kaputte Ampel blinkt', 'wehen': 'Gras: im Wind'}


def main():
    os.makedirs(OUT, exist_ok=True)
    lay = json.load(open(os.path.join(kb.KARTE, 'layout.json')))
    objs = json.load(open(os.path.join(kb.OBJ, 'platzierung.json')))
    # Ausschnitte: Gelaende-Effekte + je ein Beispiel jeder Objekt-Animation (alle Instanzen im Plan markiert)
    bx, by = lay['boss']
    tps = lay['teleporter']
    stellen = [('Boss-Kreis: Segmentring dreht, Kern pulsiert', (bx * T - 72, by * T - 72, bx * T + 72, by * T + 72))]
    for tp in tps:
        stellen.append(('Teleporter: pulsiert', (tp['x'] * T - 16, max(0, tp['y'] * T - 24), (tp['x'] + tp['b']) * T + 16, (tp['y'] + tp['h']) * T)))
    rauch_o = [o for o in objs if o.get('rauch')]
    if rauch_o:
        o = rauch_o[0]
        sp = Image.open(os.path.join(kb.OBJ, o['datei']))
        stellen.append(('Schornstein: Rauch steigt auf', (o['x'] - 16, o['y'] - 48, o['x'] + sp.width + 36, o['y'] + sp.height + 4)))
    gesehen = {}
    for o in objs:
        an = o.get('anim')
        if not an:
            continue
        sp = Image.open(os.path.join(kb.OBJ, o['datei']))
        box = (o['x'] - 10, o['y'] - 10, o['x'] + sp.width + 10, o['y'] + sp.height + 10)
        gesehen.setdefault((an, o['basis'] if an not in ('rotlicht', 'glimmen') else o['basis'].split('/')[0] + ('' if an == 'glimmen' else o['basis'])), (o, box))
    for (an, b), (o, box) in sorted(gesehen.items()):
        if an == 'treiben' and b != 'wolken':
            continue
        stellen.append(('%s (%s)' % (NAMEN.get(an, an), o['basis']), box))
    stellen = [(t, tuple(int(round(v)) for v in b)) for (t, b) in stellen]
    frames = [kb.bauen(frame=f, speichern=False).convert('RGB') for f in range(kb.N_FRAMES)]
    # Uebersicht
    plan = frames[0].copy().convert('RGBA')
    plan.alpha_composite(Image.new('RGBA', plan.size, (0, 0, 0, 90)))
    d = ImageDraw.Draw(plan)
    farben = {'rotlicht': (255, 70, 80), 'lampe': (255, 220, 120), 'glimmen': (150, 220, 255), 'feuer': (255, 150, 60),
              'konsole': (120, 255, 200), 'funken': (255, 250, 150), 'ampel_blinken': (255, 190, 60), 'wehen': (120, 230, 100)}
    for o in objs:
        an = o.get('anim')
        if an:
            sp = Image.open(os.path.join(kb.OBJ, o['datei']))
            d.rectangle((o['x'], o['y'], o['x'] + sp.width, o['y'] + sp.height), outline=farben.get(an, (255, 255, 255)) + (255,), width=2)
    for (t, b) in stellen[:len(tps) + 2]:
        d.rectangle(b, outline=(255, 80, 200, 255), width=3)
    ly = 1120 - 18 * (len(farben) + 1) - 12
    d.rectangle((8, ly - 6, 330, 1112), fill=(10, 10, 14, 230))
    for i, (an, c) in enumerate(list(farben.items()) + [('gelaende', (255, 80, 200))]):
        d.rectangle((14, ly + i * 18, 26, ly + i * 18 + 12), outline=c + (255,), width=2)
        d.text((34, ly + i * 18), NAMEN.get(an, 'Boss-Kreis, Teleporter, Rauch'), fill=(240, 240, 240, 255))
    plan.save(os.path.join(OUT, 'animationsplan.png'))
    # Einzel-GIF: Raster aus allen Ausschnitten, je 2x, beschriftet
    Z = 2
    kacheln = []
    stellen = [(t, tuple(int(round(v)) for v in b)) for (t, b) in stellen]
    for (t, b) in stellen:
        w, h = (b[2] - b[0]) * Z, (b[3] - b[1]) * Z
        kacheln.append((t, b, w, h))
    spalten = 4
    zw = max(k[2] for k in kacheln)
    zellen_h = []
    for r in range(0, len(kacheln), spalten):
        zellen_h.append(max(k[3] for k in kacheln[r:r + spalten]) + 22)
    W, Hh = spalten * (zw + 10), sum(zellen_h)
    bilder = []
    for fr in frames:
        img = Image.new('RGB', (W, Hh), (20, 18, 26))
        dd = ImageDraw.Draw(img)
        y = 0
        for r in range(0, len(kacheln), spalten):
            for c, (t, b, w, h) in enumerate(kacheln[r:r + spalten]):
                x = c * (zw + 10)
                img.paste(fr.crop(b).resize((w, h), Image.NEAREST), (x, y + 20))
                dd.text((x + 3, y + 4), t, fill=(240, 220, 160))
            y += zellen_h[r // spalten]
        bilder.append(img.quantize(colors=255, method=Image.Quantize.MAXCOVERAGE))
    bilder[0].save(os.path.join(OUT, 'animationen_einzeln.gif'), save_all=True, append_images=bilder[1:], duration=170, loop=0,
                   disposal=1)
    print(len(stellen), 'Animationen', (W, Hh))


if __name__ == '__main__':
    main()
