"""Karte 37 - Hypnos Rooftop (A03 Nr. 4), Gelaende + Objekte + Animation (4 Bilder).

  python3 tools/karte37_layout.py && python3 tools/karte37_bauen.py && python3 tools/karte37_objekte.py && python3 tools/karte37_bauen.py

Das Dach des Hypnos-Hochhauses liegt hoch ueber Shinjuku (Nutzer): Im Ring der aeusseren 3 Kacheln sieht man tief unten
die Stadt von Karte 35 (Shinjuku Digital Fog) - verkleinert (weit unten), mit Hoehendunst, aus deren eigener Animation
gerendert (Nebel, Laternen, Teleporter bewegen sich mit). Das Dach wirft einen Schatten nach rechts unten auf die Stadt;
die Dachkante hat eine Bruestung, im Sueden faellt die Fassade sichtbar ab. Dachflaeche: helle Ziegelwege (Karte 18 'k')
und die tiefer liegende dunkle Flaeche mit Kante. Der Ring ist nicht begehbar (leere.npy).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageFilter
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte18_bauen as k18

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte37')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte37')
T = 16
N_FRAMES = 4                     # Regel: hoechstens 4 Animationsbilder
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
kb.N_FRAMES = N_FRAMES
k6.N_FRAMES = N_FRAMES
H = k4.H
gross, kontur, dunkeln = k18.gross, k18.kontur, k18.dunkeln
MASSSTAB = 2                     # die Stadt unten erscheint halb so gross (weit unten)
DUNST = np.array((150, 162, 188), np.float32)


def stadt_unten(frame, W, Hh):
    """Karte 35 aus ihrer eigenen Animation, verkleinert und mit Hoehendunst, mittig unter dem Dach (zwischengespeichert)."""
    import karte35_bauen as k35
    ordner = os.path.join(KARTE, 'blick')
    os.makedirs(ordner, exist_ok=True)
    n = N_FRAMES
    pfad = os.path.join(ordner, 'k35_%d_%s.png' % (n, 'st' if frame is None else frame))
    if not os.path.exists(pfad):
        if frame is None:
            q = Image.open(os.path.join(ROOT, 'maps', 'karte35', 'terrain.png')).convert('RGB')
        else:
            k35.N_FRAMES = n
            q = k35.bauen(frame=frame, speichern=False).convert('RGB')
        k = q.resize((q.width // MASSSTAB, q.height // MASSSTAB), Image.BOX)
        ox, oy = (k.width - W) // 2, (k.height - Hh) // 2
        k = k.crop((ox, oy, ox + W, oy + Hh))
        a = np.array(k).astype(np.float32)
        grau = a.mean(-1, keepdims=True)
        a = a * 0.75 + grau * 0.25                                     # Ferne: etwas entsaettigt
        a = a * 0.62 + DUNST * 0.38                                    # Hoehendunst
        Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(pfad)
    return np.array(Image.open(pfad).convert('RGB'))


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    kl = np.array([list(r) for r in lay['klassen']])
    dach = gross(kl != 'z')
    a = stadt_unten(frame, Wp, Hp).copy()                              # Blick hinunter
    ziegel = k18.textur('k', cols, rows)
    deck_k = kl == 'u'
    deck = gross(deck_k)
    flaeche = np.clip(k18.textur('g', cols, rows).astype(np.float32) * np.array((0.6, 0.7, 0.82)), 0, 255).astype(np.uint8)
    a[dach] = ziegel[dach]
    a[deck] = flaeche[deck]
    k18.bordsteine(a, deck, dach & ~deck)                              # Kante der tiefer liegenden Dachflaeche
    # Schatten des Daches auf die Stadt (Licht oben links -> nach rechts unten), weich
    sch = np.zeros_like(dach)
    sch[14:, 10:] = dach[:-14, :-10]
    sch &= ~dach
    s = np.array(Image.fromarray((sch * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32) / 255
    s[dach] = 0
    a[:] = np.clip(a * (1 - 0.45 * s[..., None]), 0, 255).astype(np.uint8)
    # Fassade faellt im Sueden ab (unter der Dachkante, auch unter der Plattform)
    unten = dach & ~np.vstack([dach[1:], np.zeros((1, Wp), bool)])
    for d in range(1, 15):
        f = np.vstack([np.zeros((d, Wp), bool), unten[:-d]]) & ~dach
        c = np.array(H('#8a919c'), np.float32) * (1 - d * 0.035)
        a[f] = c.astype(np.uint8)
        if d in (5, 10):
            a[f] = (c * 0.8).astype(np.uint8)                          # Geschossfuge
    # Bruestung: 1 px dunkle Aussenkontur, 2 px helle Abdeckung mit Lichtkante
    rand = kontur(dach)
    rand2 = kontur(dach & ~rand)
    a[rand2] = H('#d8dce2')
    a[rand] = H('#3a404c')
    lvl = np.ones((Hp, Wp), np.uint8)
    leere = ~dach
    if speichern and frame is None:
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(np.zeros((Hp, Wp), bool)))
        np.save(os.path.join(KARTE, 'leere.npy'), np.packbits(leere))
    img = Image.fromarray(a).convert('RGBA')
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.astype(np.int16)
            ebenen[deck] = 0                                               # tiefere Flaeche: Schatten bleiben auf ihrer Ebene
            k4.objekte_zeichnen(img, objs, cache, dach, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
            k6.animieren_k6(img, objs, cache, frame or 0)
    a = np.array(img.convert('RGB'))
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 37 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
