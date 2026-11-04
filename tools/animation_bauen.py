"""Animierte Fassung von Karte 01 (16 Frames, Schleife).

  python3 tools/animation_bauen.py

Animiert: Wasser (Fluss fliesst, Teich/Meer schwappen), glitzernder Schaum an Ufern,
fallender Wasserfall mit brodelnder Gischt und Nebel, pulsierende Runen, flackerndes
Lagerfeuer, Gras/Schilf/Farne/Blumen im Wind, wippende Seerosen, Schmetterlinge,
flackernde Laternen. Ausgabe in maps/karte01/animation/:
  karte01_animiert.webp   ganze Karte, verlustfrei
  karte01_discord.gif     ganze Karte als GIF unter 10 MB (Discord-Limit)
  detail_*.gif            Ausschnitte 3x vergroessert
  kacheln/*.png           Wasser-Grundkacheln als 16-Frame-Streifen (fuer eine Engine)
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageChops
import karte_bauen as kb

OUT = os.path.join(kb.KARTE, 'animation')
DAUER = 110          # ms pro Frame
AUSSCHNITTE = {      # Name: (x0, y0, x1, y1) in Kacheln
    'wasserfall': (50, 18, 70, 34),
    'teich': (40, 46, 70, 66),
    'strand': (0, 86, 40, 108),
    'lager': (84, 88, 106, 100),
    'wiese': (8, 30, 34, 46),
    'laternen': (26, 16, 58, 36),
}


def discord_gif(frames, ziel_mb=9.5):
    """Ganze Karte als GIF fuer Discord (Limit 10 MB): eine gemeinsame 256-Farben-Palette fuer alle
    Frames (kein Flackern, kein Dithering), Pillow speichert je Frame nur den geaenderten Bereich.
    Wird die Datei zu gross, wird mit ganzzahligem Faktor verkleinert (Pixelart bleibt scharf)."""
    probe = Image.new('RGB', (frames[0].width * 2, frames[0].height))
    probe.paste(frames[0], (0, 0)); probe.paste(frames[len(frames) // 2], (frames[0].width, 0))
    pal = probe.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    # erst volle Aufloesung mit allen Frames, dann volle Aufloesung mit jedem 2. Frame (doppelte
    # Bildzeit, gleiche Geschwindigkeit), erst zuletzt halbe Groesse
    for skala, schritt in ((1, 1), (1, 2), (2, 1)):
        bilder = [(fr if skala == 1 else fr.resize((fr.width // skala, fr.height // skala), Image.NEAREST))
                  .quantize(palette=pal, dither=Image.Dither.NONE) for fr in frames[::schritt]]
        pfad = os.path.join(OUT, 'karte01_discord.gif')
        bilder[0].save(pfad, save_all=True, append_images=bilder[1:], duration=DAUER * schritt, loop=0,
                       optimize=False)
        mb = os.path.getsize(pfad) / 1e6
        print('Discord-GIF %dx%d, %d Frames: %.1f MB' % (bilder[0].width, bilder[0].height, len(bilder), mb))
        if mb <= ziel_mb:
            return


def main():
    os.makedirs(os.path.join(OUT, 'kacheln'), exist_ok=True)
    frames = []
    t0 = time.time()
    for f in range(kb.N_FRAMES):
        frames.append(kb.bauen(frame=f, speichern=False).convert('RGB'))
        print('Frame %d/%d (%.0fs)' % (f + 1, kb.N_FRAMES, time.time() - t0), flush=True)
    frames[0].save(os.path.join(OUT, 'karte01_animiert.webp'), save_all=True, append_images=frames[1:],
                   duration=DAUER, loop=0, lossless=True, method=4)
    discord_gif(frames)
    for name, (x0, y0, x1, y1) in AUSSCHNITTE.items():
        box = (x0 * kb.T, y0 * kb.T, x1 * kb.T, y1 * kb.T)
        teil = [fr.crop(box).resize(((x1 - x0) * kb.T * 3, (y1 - y0) * kb.T * 3), Image.NEAREST)
                .quantize(colors=255, method=Image.Quantize.MAXCOVERAGE) for fr in frames]
        teil[0].save(os.path.join(OUT, 'detail_%s.gif' % name), save_all=True, append_images=teil[1:],
                     duration=DAUER, loop=0, disposal=1)
    # Wasser-Grundkacheln als Frame-Streifen
    for art in ('wasser', 'meer'):
        for i in range(5):
            k = Image.open(os.path.join(kb.BASIS, '%s_%d.png' % (art, i))).convert('RGBA')
            for modus in ('fluss', 'schwappen'):
                if art == 'meer' and modus == 'fluss':
                    continue
                streifen = Image.new('RGBA', (kb.T * kb.N_FRAMES, kb.T))
                for f in range(kb.N_FRAMES):
                    dx, dy = (0, f) if modus == 'fluss' else (kb.PENDEL[f], 0)
                    streifen.paste(ImageChops.offset(k, dx, dy), (f * kb.T, 0))
                streifen.save(os.path.join(OUT, 'kacheln', '%s_%d_%s.png' % (art, i, modus)))
    print('fertig')


if __name__ == '__main__':
    main()
