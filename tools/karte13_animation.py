"""Animierte Fassung von Karte 13 (Spiral Mountain: Machine City) und Discord-GIF.

  python3 tools/karte13_animation.py

Animiert: Boss-Kreis, Teleporter, Giftwasser (Lichtnetz, Blasen), rote Lichter (Warnleuchten, Funkturm, Tor-Auge,
Panzertueren, Mech-Kopf), Reaktoren, Konsolen, Laternen, Funken am Drachen-Wrack, Rauch, Ofen, kaputte Ampeln, Kristalle.
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import karte13_bauen as k3
import animation_bauen as ab

OUT = os.path.join(k3.KARTE, 'animation')
DAUER = 170
AUSSCHNITTE = {'festung': (24, 0, 56, 30), 'hof_rechts': (52, 0, 80, 30), 'stadt': (24, 28, 64, 60)}



def main():
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    frames = []
    for f in range(k3.N_FRAMES):
        frames.append(k3.bauen(frame=f, speichern=False).convert('RGB'))
        print('Frame %d/%d (%.0fs)' % (f + 1, k3.N_FRAMES, time.time() - t0), flush=True)
    frames[0].save(os.path.join(OUT, 'karte13_animiert.webp'), save_all=True, append_images=frames[1:],
                   duration=DAUER, loop=0, lossless=True, method=4)
    alt, alt_dauer = ab.OUT, ab.DAUER
    ab.OUT, ab.DAUER = OUT, DAUER
    ab.discord_gif(frames)
    os.replace(os.path.join(OUT, 'karte01_discord.gif'), os.path.join(OUT, 'karte13_discord.gif'))
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
