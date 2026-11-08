"""Animationsplan Karte 18 (The Fog-Bound City): Uebersicht mit nummerierten Stellen + jede Animation einzeln
(4 Bilder, Regel: hoechstens 4 Animationsbilder).

  python3 tools/karte18_animplan.py  ->  maps/karte18/animation/animationsplan.png, animationen_einzeln.gif
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import karte18_bauen as kb

OUT = os.path.join(kb.KARTE, 'animation')
T = 16
STELLEN = [   # (Titel, Ausschnitt in Kacheln x0, y0, x1, y1)
    ('1 Nebel zieht', (118, 44, 136, 60)),
    ('2 Meer: Wellen', (60, 99, 84, 108)),
    ('3 Kanal: Wellen', (124, 86, 134, 100)),
    ('4 Laternen + Lichtkreis', (90, 34, 100, 42)),
    ('5 Leuchtreklame', (14, 11, 30, 19)),
    ('6 Teleporter', (128, 38, 136, 46)),
    ('7 Ampeln', (28, 22, 40, 28)),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    objs = json.load(open(os.path.join(kb.OBJ, 'platzierung.json')))
    for name, titel in (('boot', '8 Boot schaukelt'), ('fahne18', '9 Fahnen (nur Tuch)'), ('automat', '10 Automaten')):
        for o in objs:
            if o.get('anim') == name:
                sp = Image.open(os.path.join(kb.OBJ, o['datei']))
                STELLEN.append((titel, ((o['x'] - 12) // T, (o['y'] - 12) // T, (o['x'] + sp.width + 28) // T,
                                        (o['y'] + sp.height + 28) // T)))
                break
    frames = [kb.bauen(frame=f, speichern=False).convert('RGB') for f in range(kb.N_FRAMES)]
    plan = frames[0].copy().convert('RGBA')
    plan.alpha_composite(Image.new('RGBA', plan.size, (0, 0, 0, 70)))
    d = ImageDraw.Draw(plan)
    for o in objs:
        if o.get('anim'):
            sp = Image.open(os.path.join(kb.OBJ, o['datei']))
            d.rectangle((o['x'], o['y'], o['x'] + sp.width, o['y'] + sp.height), outline=(120, 230, 255, 255), width=1)
    for t, (x0, y0, x1, y1) in STELLEN:
        d.rectangle((x0 * T, y0 * T, x1 * T, y1 * T), outline=(255, 80, 200, 255), width=3)
        d.text((x0 * T + 4, y0 * T + 3), t.split()[0], fill=(255, 255, 255, 255))
    plan.resize((plan.width // 2, plan.height // 2), Image.LANCZOS).save(os.path.join(OUT, 'animationsplan.png'))
    S, B, spalten = 3, 300, 4
    zeilen = (len(STELLEN) + spalten - 1) // spalten
    bilder = []
    for f in frames:
        g = Image.new('RGB', (spalten * B, zeilen * (B + 20)), (16, 16, 24))
        dg = ImageDraw.Draw(g)
        for i, (t, (x0, y0, x1, y1)) in enumerate(STELLEN):
            aus = f.crop((x0 * T, y0 * T, x1 * T, y1 * T))
            fak = min(S, (B - 8) / aus.width, (B - 8) / aus.height)
            aus = aus.resize((max(1, int(aus.width * fak)), max(1, int(aus.height * fak))), Image.NEAREST)
            gx, gy = (i % spalten) * B, (i // spalten) * (B + 20)
            dg.text((gx + 6, gy + 4), t, fill=(240, 240, 240))
            g.paste(aus, (gx + (B - aus.width) // 2, gy + 20 + (B - aus.height) // 2))
        bilder.append(g)
    from karte18_animation import gemeinsame_palette
    bilder = gemeinsame_palette(bilder)                     # gemeinsame Palette: Statisches flimmert nicht
    bilder[0].save(os.path.join(OUT, 'animationen_einzeln.gif'), save_all=True, append_images=bilder[1:],
                   duration=kb.BILDDAUER, loop=0)
    print('Animationsplan ->', OUT)


if __name__ == '__main__':
    main()
