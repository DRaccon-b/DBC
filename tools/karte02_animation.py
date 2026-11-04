"""Animierte Fassung von Karte 02 (16 Frames, Schleife) und Discord-GIF.

  python3 tools/karte02_animation.py

Animiert: Foerderbaender laufen, Reaktor/Pylone/Generatoren pulsieren gruen bzw. cyan, Feuer in Oefen
und Hochoefen flackert, Rauch steigt aus den Schornsteinen, Signalsaeulen blinken, Laternen flackern.
Ausgabe: maps/karte02/animation/karte02_animiert.webp, karte02_discord.gif, detail_*.gif
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import karte02_bauen as k2
import animation_bauen as ab

OUT = os.path.join(k2.KARTE, 'animation')
DAUER = 170          # ms pro Frame (langsamer als Karte 01)
AUSSCHNITTE = {'reaktor': (58, 4, 92, 34), 'fabrik': (27, 0, 61, 32), 'werkstatt': (26, 48, 62, 73),
               'containerlager': (2, 2, 32, 30)}


def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    frames = []
    for f in range(k2.N_FRAMES):
        frames.append(k2.bauen(frame=f, speichern=False).convert('RGB'))
        print('Frame %d/%d (%.0fs)' % (f + 1, k2.N_FRAMES, time.time() - t0), flush=True)
    frames[0].save(os.path.join(OUT, 'karte02_animiert.webp'), save_all=True, append_images=frames[1:],
                   duration=DAUER, loop=0, lossless=True, method=4)
    alt, alt_dauer = ab.OUT, ab.DAUER
    ab.OUT, ab.DAUER = OUT, DAUER
    ab.discord_gif(frames)
    os.replace(os.path.join(OUT, 'karte01_discord.gif'), os.path.join(OUT, 'karte02_discord.gif'))
    ab.OUT, ab.DAUER = alt, alt_dauer
    for name, (x0, y0, x1, y1) in AUSSCHNITTE.items():
        box = (x0 * 16, y0 * 16, x1 * 16, y1 * 16)
        teil = [fr.crop(box).resize(((x1 - x0) * 32, (y1 - y0) * 32), Image.NEAREST)
                .quantize(colors=255, method=Image.Quantize.MAXCOVERAGE) for fr in frames]
        teil[0].save(os.path.join(OUT, 'detail_%s.gif' % name), save_all=True, append_images=teil[1:],
                     duration=DAUER, loop=0, disposal=1)
    print('fertig')


if __name__ == '__main__':
    main()
