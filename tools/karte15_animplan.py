"""Animationsplan Karte 15 (Apocalymon's Realm): Uebersicht mit nummerierten Stellen + jede Animation einzeln
(4 Bilder, Regel: hoechstens 4 Animationsbilder).

  python3 tools/karte15_animplan.py  ->  maps/karte15/animation/animationsplan.png, animationen_einzeln.gif
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import karte15_bauen as kb

OUT = os.path.join(kb.KARTE, 'animation')
T = 16
STELLEN = [   # (Titel, Ausschnitt in px)
    ('1 Sterne funkeln (Leere)', (40, 300, 140, 380)),
    ('2 Datenstriche flackern', (0, 140, 110, 220)),
    ('3 Inselkante glimmt magenta', (100, 220, 200, 300)),
    ('4 Leuchtadern im Felsbauch', (140, 440, 290, 580)),
    ('5 Bodenrisse: Licht pulsiert', (230, 200, 410, 400)),
    ('6 Teleporter pulsiert', (272, 584, 368, 640)),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    objs = json.load(open(os.path.join(kb.OBJ, 'platzierung.json')))
    for o in objs:                                                # 7: ein Beispiel der schwebenden Brocken
        if o.get('anim') == 'schweben':
            sp = Image.open(os.path.join(kb.OBJ, o['datei']))
            STELLEN.append(('7 Brocken schweben (alle %d)' % sum(1 for p in objs if p.get('anim') == 'schweben'),
                            (o['x'] - 8, o['y'] - 8, o['x'] + sp.width + 8, o['y'] + sp.height + 8)))
            break
    frames = [kb.bauen(frame=f, speichern=False).convert('RGB') for f in range(kb.N_FRAMES)]
    plan = frames[0].copy().convert('RGBA')
    plan.alpha_composite(Image.new('RGBA', plan.size, (0, 0, 0, 80)))
    d = ImageDraw.Draw(plan)
    for o in objs:
        if o.get('anim'):
            sp = Image.open(os.path.join(kb.OBJ, o['datei']))
            d.rectangle((o['x'], o['y'], o['x'] + sp.width, o['y'] + sp.height), outline=(120, 230, 255, 255), width=1)
    for t, b in STELLEN[:6]:
        d.rectangle(b, outline=(255, 80, 200, 255), width=2)
        d.text((b[0] + 3, b[1] + 2), t.split()[0], fill=(255, 255, 255, 255))
    plan.resize((plan.width * 2, plan.height * 2), Image.NEAREST).save(os.path.join(OUT, 'animationsplan.png'))
    # Einzel-GIF: alle Ausschnitte 3x vergroessert im Raster, mit Titel
    S, B = 3, 340
    spalten = 4
    zeilen = (len(STELLEN) + spalten - 1) // spalten
    bilder = []
    for f in frames:
        g = Image.new('RGB', (spalten * B, zeilen * (B + 20)), (16, 16, 24))
        dg = ImageDraw.Draw(g)
        for i, (t, b) in enumerate(STELLEN):
            aus = f.crop(b)
            fak = min(S, (B - 8) / aus.width, (B - 8) / aus.height)
            aus = aus.resize((int(aus.width * fak), int(aus.height * fak)), Image.NEAREST)
            x0, y0 = (i % spalten) * B, (i // spalten) * (B + 20)
            dg.text((x0 + 6, y0 + 4), t, fill=(240, 240, 240))
            g.paste(aus, (x0 + (B - aus.width) // 2, y0 + 20 + (B - aus.height) // 2))
        bilder.append(g)
    bilder[0].save(os.path.join(OUT, 'animationen_einzeln.gif'), save_all=True, append_images=bilder[1:], duration=220, loop=0)
    frames[0].save(os.path.join(OUT, 'gesamt.gif'), save_all=True, append_images=frames[1:], duration=220, loop=0)
    print('Animationsplan ->', OUT)


if __name__ == '__main__':
    main()
