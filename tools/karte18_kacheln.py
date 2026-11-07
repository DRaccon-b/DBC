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

    if art == 's':                                   # Asphalt: dunkles Blaugrau, helle und dunkle Koerner
        fl(H('#30343f'))
        for _ in range(10):
            px[r.randint(0, 15), r.randint(0, 15)] = H('#3a3e4b')
        for _ in range(6):
            px[r.randint(0, 15), r.randint(0, 15)] = H('#272a33')
        if v == 2:                                   # Flicken
            x0, y0 = r.randint(1, 7), r.randint(1, 7)
            for y in range(y0, y0 + 6):
                for x in range(x0, x0 + 7):
                    px[x, y] = H('#2b2e38')
        if v == 4:                                   # feiner Riss
            x, y = r.randint(3, 12), 1
            for _ in range(10):
                if 0 <= x < 16 and 0 <= y < 16:
                    px[x, y] = H('#22242c')
                x += r.choice((-1, 0, 1)); y += 1
    elif art == 'g':                                 # Gehweg: Pflaster 8x4, versetzt, Licht oben
        grund, licht, fuge = H('#5c6676'), H('#6a7484'), H('#3e4654')
        for y in range(16):
            for x in range(16):
                xo = (x + (4 if (y // 4) % 2 else 0)) % 8
                if y % 4 == 3 or xo == 7:
                    c = fuge
                elif y % 4 == 0:
                    c = licht
                else:
                    c = grund
                px[x, y] = c
        if v in (1, 3):                              # einzelner dunklerer Stein
            sx, sy = r.choice((0, 8)), r.choice((0, 4, 8, 12))
            for y in range(sy, sy + 3):
                for x in range(sx + (4 if (sy // 4) % 2 else 0), sx + (4 if (sy // 4) % 2 else 0) + 7):
                    if 0 <= x < 16 and (y % 4) != 0:
                        px[x, y] = H('#56606f')
    elif art in 'pq':                                # Platz: lavendel, p grosse Platten, q kleine
        g = 16 if art == 'p' else 8
        basis = [H('#776f8a'), H('#7b738e'), H('#736b86'), H('#7e7691'), H('#787089')][v]
        for y in range(16):
            for x in range(16):
                c = basis
                if art == 'q' and ((x // 8) + (y // 8)) % 2:
                    c = mix(basis, H('#6c6480'), 0.5)
                if y % g == g - 1 or x % g == g - 1:
                    c = H('#5e5672')
                elif y % g == 0 or x % g == 0:
                    c = mix(basis, H('#958daa'), 0.5)
                px[x, y] = c
        if v == 3:                                   # Fleck
            x0, y0 = r.randint(2, 8), r.randint(2, 8)
            for y in range(y0, y0 + 4):
                for x in range(x0, x0 + 5):
                    if (x - x0 - 2) ** 2 + (y - y0 - 1.5) ** 2 < 6:
                        px[x, y] = mix(px[x, y], H('#5a5270'), 0.35)
    elif art == 'c':                                 # Mittelweg: Schachbrett hell/dunkel lavendel
        for y in range(16):
            for x in range(16):
                px[x, y] = H('#8e87a4') if ((x // 8) + (y // 8)) % 2 == 0 else H('#7c7592')
                if x % 8 == 0 or y % 8 == 0:
                    px[x, y] = mix(px[x, y], H('#a49dba'), 0.4)
    elif art == 't':                                 # Terrasse: helle Platten 16x16 mit Mittelfuge 8
        for y in range(16):
            for x in range(16):
                c = H('#9790ac') if ((x // 8) + (y // 8)) % 2 == 0 else H('#8f88a4')
                if y == 15 or x == 15:
                    c = H('#6e6886')
                elif y == 0 or x == 0:
                    c = H('#aea8c2')
                px[x, y] = c
    elif art == 'n':                                 # Rasen: dunkles Abendgruen, Halme
        fl(H('#2f4a36'))
        for _ in range(14):
            x, y = r.randint(0, 15), r.randint(1, 15)
            px[x, y] = H('#3a5a40'); px[x, y - 1] = H('#456848') if r.random() < 0.5 else H('#3a5a40')
        for _ in range(5):
            px[r.randint(0, 15), r.randint(0, 15)] = H('#263e2c')
    elif art == 'd':                                 # Sand (Sandkasten)
        fl(H('#a89068'))
        for _ in range(12):
            px[r.randint(0, 15), r.randint(0, 15)] = H('#b8a078') if r.random() < 0.6 else H('#94805a')
    elif art == 'x':                                 # Sperrflaeche: Asphalt mit diagonalen weissen Streifen
        for y in range(16):
            for x in range(16):
                px[x, y] = H('#b8bcc6') if (x + y) % 8 < 2 else H('#30343f')
    elif art == 'b':                                 # Gleisbett: Schotter, Holzschwellen quer (Schienen im Bau)
        fl(H('#4a4246'))
        for _ in range(26):
            px[r.randint(0, 15), r.randint(0, 15)] = r.choice((H('#58505a'), H('#3c3438'), H('#625a62')))
        for x0 in (1, 9):
            for x in range(x0, x0 + 5):
                for y in range(1, 15):
                    px[x, y] = H('#5a4434') if y not in (1, 14) else H('#3e2e24')
                px[x, 1] = H('#6e5640')
    elif art == 'k':                                 # Kaikante: grosse graue Quader, Licht oben
        for y in range(16):
            for x in range(16):
                xo = (x + (8 if (y // 8) % 2 else 0)) % 16
                c = H('#8a8e9c')
                if y % 8 == 7 or xo == 15:
                    c = H('#5c606e')
                elif y % 8 == 0:
                    c = H('#a2a6b2')
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
    arten = ['s', 'g', 'p', 'q', 'c', 't', 'n', 'd', 'x', 'b', 'k', 'h', 'w', 'nebel', 'm']
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
