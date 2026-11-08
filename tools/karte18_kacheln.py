"""16x16-Grundkacheln fuer Karte 18 (The Fog-Bound City) - nach der Vorlage, Abendlicht im Nebel (kuehle Toene).

  python3 tools/karte18_kacheln.py   ->  assets/karte18/basis/<art>_<v>.png, vorschau.png

  s Asphalt (feine Koernung, Flicken, Risse)   g Gehweg (graue Pflastersteine 8x4 im Verband)
  p Platz (lavendel, grosse Platten 16x16 mit leichter Farbstreuung)   q Platz links (kleine Platten 8x8)
  c Mittelweg (Schachbrett 8x8)   t Terrasse (helle Platten)   n Rasen   d Sand   x Sperrflaeche (schraffiert)
  b Gleisbett (Schotter, Schwellen)   k Kaikante (Steinquader)   h Holzsteg (Planken senkrecht)   w Wasser (Grund)
  nebel (Nebel-Grundton)   m Mittelstreifen-Erde (unter der Hecke)
"""
import os, random
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'assets', 'karte18', 'basis')
H = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(c1, c2, t):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c1, c2))


def kachel(art, v):
    r = random.Random(1800 + v * 31 + ord(art[0]) * 7)
    im = Image.new('RGB', (16, 16))
    px = im.load()

    def fl(c):
        for y in range(16):
            for x in range(16):
                px[x, y] = c

    def platten(gw, gh, basis, licht, schatten, fuge, versatz=0):
        """GBA-Handheld-Stil: saubere Platten gw x gh, je Platte 1 px Licht oben/links, 1 px Schatten
        unten/rechts innen, Fuge 1 px unten/rechts; kein Rauschen."""
        for y in range(16):
            for x in range(16):
                xo = (x + (versatz if (y // gh) % 2 else 0)) % gw
                yo = y % gh
                if yo == gh - 1 or xo == gw - 1:
                    c = fuge
                elif yo == gh - 2 or xo == gw - 2:
                    c = schatten
                elif yo == 0 or xo == 0:
                    c = licht
                else:
                    c = basis
                px[x, y] = c

    if art == 's':                                   # Asphalt: ruhig, nur ein feines festes Korn
        fl(H('#3c4150'))
        for (x, y) in ((3, 2), (11, 5), (6, 9), (14, 12), (1, 13), (9, 15))[:3 + v % 4]:
            px[x, y] = H('#474c5c')
    elif art == 'g':                                 # Gehweg: helle quadratische Platten 8x8
        platten(8, 8, H('#a9adbb'), H('#c9ccd8'), H('#9498a8'), H('#73778a'))
    elif art == 'p':                                 # grosser Platz: Lavendel-Platten 16x16 mit Einlage
        platten(16, 16, H('#a79fbe'), H('#c6bfd9'), H('#958dad'), H('#716a8a'))
        if v % 2 == 0:                               # kleines Rautenmuster in der Mitte (wie GBA-Plaetze)
            for (x, y) in ((7, 5), (6, 6), (8, 6), (5, 7), (9, 7), (6, 8), (8, 8), (7, 9)):
                px[x, y] = H('#b8b0cd')
    elif art == 'q':                                 # Platz links: kleine rosa-lavendel Platten 8x8
        platten(8, 8, H('#b3a3bf'), H('#cebfd9'), H('#9f8fad'), H('#776886'))
    elif art == 'c':                                 # Mittelweg: Schachbrett, je Feld mit Kante
        for y in range(16):
            for x in range(16):
                hell = ((x // 8) + (y // 8)) % 2 == 0
                b_, l_, s_ = ((H('#bab3cf'), H('#d4cee4'), H('#a39bb9')) if hell else
                              (H('#9c94b4'), H('#b0a9c6'), H('#8a82a2')))
                xo, yo = x % 8, y % 8
                c = s_ if (xo == 7 or yo == 7) else l_ if (xo == 0 or yo == 0) else b_
                px[x, y] = c
    elif art == 't':                                 # Terrasse: helle Platten 16x8, versetzt
        platten(16, 8, H('#c2bed2'), H('#dcd8e8'), H('#aca8be'), H('#86829a'), versatz=8)
    elif art == 'n':                                 # Rasen: das Gras von Karte 01 (assets/basis/gras_*)
        g_ = Image.open(os.path.join(ROOT, 'assets', 'basis', 'gras_%d.png' % v)).convert('RGB')
        g_ = Image.eval(g_, lambda c: int(c * 0.86))
        im.paste(g_, (0, 0))
    elif art == 'd':                                 # Sand (Sandkasten): der Sand von Karte 01
        g_ = Image.open(os.path.join(ROOT, 'assets', 'basis', 'sand_%d.png' % v)).convert('RGB')
        im.paste(Image.eval(g_, lambda c: int(c * 0.86)), (0, 0))
    elif art == 'v':                                 # Betonvorplatz: grosse helle Platten 16x16
        platten(16, 16, H('#b9bcc6'), H('#d2d4dc'), H('#a4a7b2'), H('#7f8290'))
    elif art == 'x':                                 # Sperrflaeche: Asphalt mit diagonalen weissen Streifen
        for y in range(16):
            for x in range(16):
                px[x, y] = H('#b8bcc6') if (x + y) % 8 < 2 else H('#30343f')
    elif art == 'b':                                 # Holzpromenade: Laengsplanken 4 px, versetzte Stossfugen, Naegel
        for y in range(16):
            reihe = y // 4
            for x in range(16):
                c = [H('#8a6440'), H('#916a45'), H('#86603c'), H('#8e6842')][(reihe + v) % 4]
                if y % 4 == 3:
                    c = H('#5a3e26')
                elif y % 4 == 0:
                    c = H('#b08a5e')
                stoss = (5 + reihe * 7 + v * 3) % 16
                if x == stoss and y % 4 != 3:
                    c = H('#4a3220')
                if x == (stoss + 2) % 16 and y % 4 == 1:
                    c = H('#a8865e')
                px[x, y] = c
    elif art == 'k':                                 # Kaikante: grosse graue Quader, Licht oben
        for y in range(16):
            for x in range(16):
                xo = (x + (8 if (y // 8) % 2 else 0)) % 16
                c = H('#9a9eac')
                if y % 8 == 7 or xo == 15:
                    c = H('#5c606e')
                elif y % 8 == 6 or xo == 14:
                    c = H('#7c8090')
                elif y % 8 == 0 or xo == 0:
                    c = H('#b8bcc8')
                px[x, y] = c
    elif art == 'h':                                 # Holzsteg: Planken senkrecht 4 px, Fugen, Naegel
        for y in range(16):
            for x in range(16):
                c = [H('#7a5636'), H('#84603e'), H('#70502f'), H('#7e5a38')][(x // 4 + v) % 4]
                if x % 4 == 3:
                    c = H('#4a3220')
                if y == (5 + (x // 4) * 3 + v) % 16 and x % 4 == 1:
                    c = H('#a08060')
                px[x, y] = c
    elif art == 'w':                                 # Wasser-Grund (Wellen im Bau)
        fl(H('#141a3c'))
    elif art == 'nebel':
        fl(H('#9892b0'))
    elif art == 'm':
        fl(H('#3a3a30'))
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    arten = ['s', 'g', 'p', 'q', 'c', 't', 'n', 'd', 'x', 'b', 'k', 'h', 'w', 'nebel', 'm', 'v']
    vor = Image.new('RGB', (len(arten) * 68, 64))
    for i, art in enumerate(arten):
        ks = [kachel(art, v) for v in range(5)]
        for v, kk in enumerate(ks):
            kk.save(os.path.join(OUT, '%s_%d.png' % (art, v)))
        for yy in range(4):
            for xx in range(4):
                vor.paste(ks[(xx * 3 + yy * 2) % 5], (i * 68 + xx * 16, yy * 16))
    vor.resize((vor.width * 2, vor.height * 2), Image.NEAREST).save(os.path.join(OUT, 'vorschau.png'))
    print('Kacheln ->', OUT)


if __name__ == '__main__':
    main()
