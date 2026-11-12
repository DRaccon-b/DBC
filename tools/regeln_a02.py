"""Regeln aus CLAUDE.md, die sich fuer alle A02-Karten gleich anwenden lassen (Nutzer: "wende die Regeln auf alle an").

  wege_schwingen(k, ...)       Regel 6: gerade Wegbahnen sanft verbiegen (Layout, Kachelklassen)
  objekte_pruefen(karte, ...)  "Nichts auf Wegen" + "Teleporter frei" auf platzierung.json
  python3 tools/regeln_a02.py karteNN [wegklassen]   -> nur objekte_pruefen

Regel 6b (45-Grad-Wegkanten) steckt direkt in den Bau-Skripten: Wegmaske = Kachelmaske, Gauss 5 px, Schwelle 50 %
(weich(roh, 5.0, 0, 4)) statt der ausgefransten Kante.
"""
import json, os, sys
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
T = 16


def platz(w, r=2, anteil=0.8):
    """Kacheln in breiten Wegflaechen (Lager, Hof, Platz): im (2r+1)^2-Fenster mehr als 'anteil' Weg."""
    from PIL import ImageFilter
    w = np.asarray(w)
    m = np.array(Image.fromarray((w * 255).astype(np.uint8)).filter(ImageFilter.BoxBlur(r))) / 255.0
    return w & (m > anteil)


def wege_schwingen(k, weg='w', frei='g', amp=1.25, wellen=(21.0, 17.0), seed=0, fest=None, abstand=2, platz_r=2):
    """Regel 6 (Wege nie nur gerade): die Wegflaeche wird mit einem weichen Verschiebungsfeld verbogen - waagerechte
    Bahnen schwingen auf und ab, senkrechte nach links und rechts (Amplitude amp Kacheln, Wellenlaenge ~20 Kacheln,
    Steigung < 0.5 -> Wege bleiben zusammenhaengend und gleich breit). Gerechnet wird 4-fach fein mit weicher Maske,
    danach je Kachel ueber 50 %.
    Fest bleiben: alles im Abstand 'abstand' Kacheln zu Nicht-Gras/Nicht-Weg (Treppen, Bruecken, Plaetze, Waende,
    Teleporter, Wasser ...) und die Maske 'fest' (z. B. Gebaeudeflaechen). Neue Wegkacheln nur auf 'frei' (Gras)."""
    k = np.array(k)
    R, C = k.shape
    w = np.isin(k, list(weg))
    anker = ~np.isin(k, list(weg + frei)) | platz(w, platz_r)                 # breite Flaechen sind Plaetze, keine Wege
    if fest is not None:
        anker |= fest
    cur = anker.copy()
    gew = np.zeros((R, C), np.float32)
    for d in range(abstand + 3):                                       # Gewicht 0 am Anker -> 1 ab abstand+3 Kacheln
        if d >= abstand:
            gew[~cur] += 1.0 / 3
        cur = cur | np.roll(cur, 1, 0) | np.roll(cur, -1, 0) | np.roll(cur, 1, 1) | np.roll(cur, -1, 1)
    gew = np.clip(gew, 0, 1)
    F = 4
    yy, xx = np.mgrid[0:R * F, 0:C * F].astype(np.float32) / F
    rs = np.random.RandomState(seed)
    p = rs.uniform(0, 2 * np.pi, 4)
    dy = amp * (0.75 * np.sin(2 * np.pi * xx / wellen[0] + p[0]) + 0.25 * np.sin(2 * np.pi * xx / 7.3 + p[1]))
    dx = amp * (0.75 * np.sin(2 * np.pi * yy / wellen[1] + p[2]) + 0.25 * np.sin(2 * np.pi * yy / 6.7 + p[3]))
    g = np.array(Image.fromarray((gew * 255).astype(np.uint8)).resize((C * F, R * F), Image.BILINEAR)) / 255.0
    sy = np.clip(yy - g * dy, 0, R - 1e-3)
    sx = np.clip(xx - g * dx, 0, C - 1e-3)
    neu_f = w[sy.astype(int), sx.astype(int)].astype(np.float32)
    neu = neu_f.reshape(R, F, C, F).mean((1, 3)) > 0.5
    out = k.copy()
    for y, x in zip(*np.nonzero(w & ~neu & (gew > 0))):                # frei gewordene Kachel: Boden der Nachbarn
        nb = [k[yy, xx] for yy in range(max(0, y - 1), min(R, y + 2)) for xx in range(max(0, x - 1), min(C, x + 2))
              if k[yy, xx] in frei]
        out[y, x] = max(set(nb), key=nb.count) if nb else frei[0]
    out[neu & np.isin(k, list(frei))] = weg[0]
    return out


def objekte_pruefen(karte, wegklassen='w', klein_bis=24):
    """Nichts auf Wegen: stehende Objekte (nicht liegend, nicht an der Wand, keine Gebaeude) mit dem Fuss auf einer
    Wegkachel werden auf die naechste freie Nicht-Weg-Kachel (bis 2 Kacheln) geschoben, sonst entfernt.
    Teleporter frei: kleine Streudeko (Sprite-Hoehe <= klein_bis px) im Umkreis von 2 Kacheln wird entfernt."""
    lay = json.load(open(os.path.join(ROOT, 'maps', karte, 'layout.json')))
    kl = lay['klassen']
    cols, rows = lay['groesse']
    obj_dir = os.path.join(ROOT, 'assets', 'objekte', karte)
    pf = os.path.join(obj_dir, 'platzierung.json')
    objs = json.load(open(pf))
    tps = lay.get('teleporter', [])

    wmask = np.array([[c in wegklassen for c in z] for z in kl]) if wegklassen else np.zeros((rows, cols), bool)
    plaetze = platz(wmask) if wegklassen else wmask
    pl = np.zeros_like(wmask)                                          # Platzflaeche + 1 Kachel Rand
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            pl |= np.roll(np.roll(plaetze, dy, 0), dx, 1)

    def weg(tx, ty):
        return 0 <= tx < cols and 0 <= ty < rows and wmask[ty, tx] and not pl[ty, tx]

    belegt = {tuple(o.get('kachel', [-1, -1])) for o in objs}
    neu, verschoben, entfernt = [], 0, 0
    for o in objs:
        if 'kachel' not in o:
            neu.append(o); continue
        tx, ty = o['kachel']
        fest = (o.get('liegend') or o.get('an_wand') or o.get('gebaeude') or o.get('fest_pos') or o.get('schwebend')
                or o.get('hochbahn') or o.get('vorrang'))
        try:
            h = Image.open(os.path.join(obj_dir, o['datei'])).height
        except OSError:
            h = 99
        if any(tp['x'] - 2 <= tx < tp['x'] + tp['b'] + 2 and tp['y'] - 2 <= ty < tp['y'] + tp['h'] + 2 for tp in tps) \
                and h <= klein_bis and not fest:
            entfernt += 1
            continue
        if not fest and weg(tx, ty):
            ziel = None
            for r in (1, 2):
                for dy in range(-r, r + 1):
                    for dx in range(-r, r + 1):
                        nx, ny = tx + dx, ty + dy
                        if (0 <= nx < cols and 0 <= ny < rows and kl[ny][nx] == 'g' and (nx, ny) not in belegt
                                and not any(weg(nx + ax, ny + ay) for ax in (-1, 0, 1) for ay in (0,))):
                            ziel = (dx, dy); break
                    if ziel: break
                if ziel: break
            if ziel is None:
                entfernt += 1
                continue
            o['x'] += ziel[0] * T; o['y'] += ziel[1] * T
            o['kachel'] = [tx + ziel[0], ty + ziel[1]]
            belegt.add(tuple(o['kachel']))
            verschoben += 1
        neu.append(o)
    json.dump(neu, open(pf, 'w'), indent=0)
    print('%s Regeln: %d verschoben, %d entfernt (Wege/Teleporter), %d Objekte' % (karte, verschoben, entfernt, len(neu)))


if __name__ == '__main__':
    objekte_pruefen(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'w')
