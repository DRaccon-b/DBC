"""Zufallskarte im Stil von Karte 01 aus vorgefertigten Kartenstuecken (tools/zufall_stuecke.py).

  python3 tools/zufall_karte.py 7            (Startwert 7, 5x4 Felder)
  python3 tools/zufall_karte.py 7 6 5        (Startwert 7, 6x5 Felder)

Ablauf (wie bei Kachel-Dungeons a la Path of Exile):
  1. Grundriss auf einem groben Feldraster: Bossarena (2x2 Felder) und Startlager moeglichst weit
     auseinander, dazwischen ein verschlungener Hauptweg, davon Abzweigungen in Sackgassen, selten eine
     Schleife. Unbenutzte Felder werden dichter Wald.
  2. Stuecke einsetzen: Fuer jedes Feld wird zufaellig ein Stueck (in einer seiner 8 Lagen) gewaehlt,
     dessen Kanten genau zum Grundriss passen (zu = Wald, offen = Waldweg oder Wiese) und zu den schon
     gesetzten Nachbarn passen (gleicher Kantentyp). Klappt es nicht, wird zurueckgegangen (Backtracking).
  3. Bauen mit der Karte-01-Technik: karte_bauen.py (Boden, Uebergaenge, Teiche, Waldboden),
     objekte_setzen.py (Wald, Waldrand, Wiese, Laternen, feste Objekte der Stuecke), karte01_raster.py
     (Regel 1/1b), karte01_v11_begleiter.py (Regel 5, Regel 7), karte01_v11_aufraeumen.py
     (keine Ueberlappungen, richtiger Untergrund). Die Karte-01-Dateien bleiben unberuehrt: alle Skripte
     schreiben in maps/zufall/_bau/<startwert>/.

Ausgabe: maps/zufall/karte_<startwert>.png und maps/zufall/grundriss_<startwert>.png (Felder mit Stueckname).
"""
import json, os, random, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import zufall_stuecke as zs

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OBJ01 = os.path.join(ROOT, 'assets', 'objekte', 'karte01')
ZIEL = os.path.join(ROOT, 'maps', 'zufall')
N = zs.N
GEGEN = {'N': 'S', 'S': 'N', 'O': 'W', 'W': 'O'}
RICHT = {'N': (0, -1), 'S': (0, 1), 'O': (1, 0), 'W': (-1, 0)}


# ---------------------------------------------------------------- 1. Grundriss
def grundriss(rnd, gw, gh):
    """Liefert boss (x, y oben links), start, Menge der Wegfelder und Verbindungen {(a, b)}."""
    for _ in range(500):
        bx, by = rnd.randrange(gw - 1), rnd.randrange(gh - 1)
        boss = {(bx + dx, by + dy) for dx in (0, 1) for dy in (0, 1)}
        frei = [(x, y) for x in range(gw) for y in range(gh) if (x, y) not in boss]
        dist = lambda c: min(abs(c[0] - b[0]) + abs(c[1] - b[1]) for b in boss)
        weit = max(dist(c) for c in frei)
        start = rnd.choice([c for c in frei if dist(c) >= weit - 1])
        ziel_laenge = int(len(frei) * 0.45)
        bester = None
        for _ in range(3000):                              # zufaellige, selbstvermeidende Wege
            pfad = [start]
            while True:
                x, y = pfad[-1]
                nb = [(x + dx, y + dy) for dx, dy in RICHT.values()]
                nb = [c for c in nb if 0 <= c[0] < gw and 0 <= c[1] < gh and c not in boss and c not in pfad]
                am_boss = [b for b in boss if b[0] == x and abs(b[1] - y) == 1]   # Arena nur von Nord/Sued
                if am_boss and len(pfad) >= ziel_laenge:
                    break
                if not nb:
                    pfad = None
                    break
                pfad.append(rnd.choice(nb))
            if pfad and (bester is None or abs(len(pfad) - ziel_laenge) < abs(len(bester) - ziel_laenge)):
                bester = pfad
                if len(pfad) == ziel_laenge:
                    break
        if bester is None or len(bester) < 3:
            continue
        pfad = bester
        x, y = pfad[-1]
        eingang = rnd.choice([b for b in boss if b[0] == x and abs(b[1] - y) == 1])
        verb = {frozenset((pfad[i], pfad[i + 1])) for i in range(len(pfad) - 1)}
        verb.add(frozenset((pfad[-1], eingang)))
        belegt = set(pfad)
        # Abzweigungen in Sackgassen (nie am Startlager)
        ziel_belegt = int(len(frei) * 0.8)
        versuche = 0
        while len(belegt) < ziel_belegt and versuche < 400:
            versuche += 1
            a = rnd.choice([c for c in belegt if c != start])
            laenge = rnd.choice((1, 1, 2, 2, 3))
            ast = [a]
            for _ in range(laenge):
                x, y = ast[-1]
                nb = [(x + dx, y + dy) for dx, dy in RICHT.values()]
                nb = [c for c in nb if 0 <= c[0] < gw and 0 <= c[1] < gh and c not in boss and c not in belegt
                      and c not in ast]
                if not nb:
                    break
                ast.append(rnd.choice(nb))
            if len(ast) < 2:
                continue
            for i in range(len(ast) - 1):
                verb.add(frozenset((ast[i], ast[i + 1])))
            belegt |= set(ast)
        # selten eine Schleife: zwei benachbarte Wegfelder zusaetzlich verbinden
        kand = [frozenset((a, (a[0] + dx, a[1] + dy))) for a in belegt for dx, dy in ((1, 0), (0, 1))
                if (a[0] + dx, a[1] + dy) in belegt and start not in (a, (a[0] + dx, a[1] + dy))]
        kand = [k for k in kand if k not in verb]
        if kand and rnd.random() < 0.6:
            verb.add(rnd.choice(kand))
        return (bx, by), start, belegt, verb, pfad
    raise RuntimeError('kein Grundriss gefunden')


# ---------------------------------------------------------------- 2. Stuecke einsetzen
def einsetzen(rnd, gw, gh, boss_xy, start, belegt, verb):
    lagen = zs.alle_lagen()
    anzahl_lagen = {}
    for l in lagen:
        anzahl_lagen[l['name']] = anzahl_lagen.get(l['name'], 0) + 1
    bx, by = boss_xy
    boss = {(bx + dx, by + dy) for dx in (0, 1) for dy in (0, 1)}
    einheiten = [('boss', (bx, by), 2)] + [('start' if c == start else 'normal', c, 1) for c in sorted(belegt)] + \
                [('wald', (x, y), 1) for x in range(gw) for y in range(gh) if (x, y) not in belegt and (x, y) not in boss]
    # Reihenfolge: Start zuerst, dann in Wegrichtung (Breitensuche), dann Wald
    def nachbarn(c):
        return [d for d in belegt | boss if frozenset((c, d)) in verb]
    reihe, gesehen, q = [], {start}, [start]
    while q:
        c = q.pop(0)
        reihe.append(c)
        for d in nachbarn(c):
            if d not in gesehen and d not in boss:
                gesehen.add(d); q.append(d)
    pos = {c: i for i, c in enumerate(reihe)}
    einheiten.sort(key=lambda e: (e[0] == 'wald', e[0] == 'boss', pos.get(e[1], 999)))

    kante = {}                           # (feld, seite) -> typ (gesetzt)
    wahl = {}
    benutzt = {}

    def soll(feld, seite):
        nb = (feld[0] + RICHT[seite][0], feld[1] + RICHT[seite][1])
        offen = frozenset((feld, nb)) in verb
        return offen, kante.get((nb, GEGEN[seite]))

    def kandidaten(e):
        art, (ex, ey), gr = e
        out = []
        for l in lagen:
            if l['typ'] != art or l['felder'] != (gr, gr):
                continue
            ok = True
            for (fx, fy, s), t in l['kanten'].items():
                offen, nachbar = soll((ex + fx, ey + fy), s)
                if (t != 'Z') != offen or (nachbar is not None and nachbar != t):
                    ok = False
                    break
            if ok:
                gew = l['gewicht'] / anzahl_lagen[l['name']] / (1 + 3 * benutzt.get(l['name'], 0)) ** 2
                out.append((gew, l))
        # gewichtet mischen
        out = [(rnd.random() ** (1.0 / g), l) for g, l in out]
        return [l for _, l in sorted(out, key=lambda t: -t[0])]

    def setzen(i):
        if i == len(einheiten):
            return True
        e = einheiten[i]
        for l in kandidaten(e):
            ex, ey = e[1]
            neu = [((ex + fx, ey + fy), s) for (fx, fy, s) in l['kanten']]
            for (fx, fy, s), t in l['kanten'].items():
                kante[((ex + fx, ey + fy), s)] = t
            wahl[e[1]] = l
            benutzt[l['name']] = benutzt.get(l['name'], 0) + 1
            if setzen(i + 1):
                return True
            benutzt[l['name']] -= 1
            for k in neu:
                del kante[k]
            del wahl[e[1]]
        return False

    if not setzen(0):
        raise RuntimeError('Stuecke passen nicht zum Grundriss')
    return wahl


# ---------------------------------------------------------------- 3. Bauen
def zusammensetzen(gw, gh, wahl):
    raster = [['F'] * (gw * N) for _ in range(gh * N)]
    fest, symmetrie = [], []
    for (fx, fy), l in wahl.items():
        for y, z in enumerate(l['raster']):
            for x, c in enumerate(z):
                raster[fy * N + y][fx * N + x] = c
        eigene = [(name, fx * N + ox, fy * N + oy) for name, ox, oy in l.get('objekte', [])]
        fest += eigene
        symmetrie += [tuple(eigene[i] for i in s) for s in l.get('symmetrie', [])]
    return [''.join(z) for z in raster], fest, symmetrie


def symmetrisch(obj, symmetrie):
    """Regel 'Symmetrische Plaetze': Paare stehen exakt spiegelgleich zur Achse (geht vor Regel 1b)."""
    pf = os.path.join(obj, 'platzierung.json')
    objs = json.load(open(pf))

    def finde(f):
        name, ax, ay = f
        k = [o for o in objs if o.get('basis') == name and 'kachel' in o]
        return min(k, key=lambda o: abs(o['kachel'][0] - ax) + abs(o['kachel'][1] - ay)) if k else None

    def mitte(o):
        return (o['block'][0] + o['block'][2] / 2.0) * 16
    for achse, a, b in symmetrie:
        oa, o1, o2 = finde(achse), finde(a), finde(b)
        if not (oa and o1 and o2):
            print('  Symmetrie: Objekt fehlt', achse, a, b)
            continue
        m = mitte(oa)
        links, rechts = sorted((o1, o2), key=mitte)
        d = round((m - mitte(links) + mitte(rechts) - m) / 2.0)
        links['x'] += int(round(m - d - mitte(links)))
        rechts['x'] += int(round(m + d - mitte(rechts)))
        print('  Symmetrie: %s / %s im Abstand %d px zu %s' % (a[0], b[0], d, achse[0]))
    json.dump(objs, open(pf, 'w'), indent=0)


def bauordner(startwert):
    bau = os.path.join(ZIEL, '_bau', str(startwert))
    obj = os.path.join(bau, 'obj')
    if os.path.exists(bau):
        shutil.rmtree(bau)
    os.makedirs(obj)
    for d in ('baeume', 'deko', 'gross', 'dschungel', 'k7gras', 'zelt_strand', 'zufall_portal', 'zufall_brunnen'):
        os.symlink(os.path.join(OBJ01, d), os.path.join(obj, d))
    shutil.copytree(os.path.join(OBJ01, 'varianten'), os.path.join(obj, 'varianten'))   # eigene Kopie: neue Varianten
    return bau, obj


def bauen(raster, fest, symmetrie, bau, obj):
    rows, cols = len(raster), len(raster[0])
    json.dump({'tile_size': 16, 'cols': cols, 'rows': rows,
               'legend': {'G': 'gras', 'F': 'wald', 'P': 'weg_hell', 'W': 'fluss_teich'}, 'grid': raster},
              open(os.path.join(bau, 'terrain_grid.json'), 'w'), indent=0)
    json.dump({'segmente': [], 'treppen': [], 'wasserfaelle': [], 'bruecken': [], 'stege': []},
              open(os.path.join(bau, 'hoehenplan.json'), 'w'))
    import karte_bauen, objekte_setzen, karte01_raster, karte01_v11_begleiter, karte01_v11_aufraeumen
    for m in (karte_bauen, objekte_setzen, karte01_raster, karte01_v11_begleiter, karte01_v11_aufraeumen):
        if hasattr(m, 'KARTE'):
            m.KARTE = bau
        m.OBJ = obj
    objekte_setzen.FEST = fest
    objekte_setzen.TEICH_AB_ZEILE = 0
    for n in ('zufall_portal/01', 'zufall_brunnen/00'):     # Einbettung: Bodenfuss + Kontaktschatten wie Steine
        objekte_setzen.FUSS_ART[n] = 'stein'
    objekte_setzen.SCHATTEN = tuple(objekte_setzen.SCHATTEN) + ('zufall_portal/', 'zufall_brunnen/')
    objekte_setzen.DSCHUNGEL_SPERRE = (5, 7, 2)        # Waldrand ueber der Arena bleibt bewachsen
    karte_bauen.bauen(objekte=False)                     # Boden -> terrain_basis.png, tilemap.json
    objekte_setzen.main()                                # Wald, Deko, feste Objekte -> platzierung.json
    karte01_raster.main()                                # Regel 1/1b: minimaler Kachelblock, mittig
    symmetrisch(obj, symmetrie)                          # Paare spiegelgleich zur Achse
    karte01_v11_begleiter.main()                         # Regel 5 + Regel 7
    karte_bauen.bauen()
    karte01_v11_aufraeumen.main()                        # Ueberlappungen / Untergrund
    img = karte_bauen.bauen()
    rest = karte01_v11_aufraeumen.pruefen(json.load(open(os.path.join(obj, 'platzierung.json'))), {})
    print('Endkontrolle: %d Objekte mit Ueberlappung oder falschem Untergrund (Regel-5-Begleiter erlaubt)' % len(rest))
    return img


def grundriss_bild(gw, gh, wahl, boss_xy, start, verb, pfad):
    px = 4
    im = Image.new('RGB', (gw * N * px, gh * N * px))
    for (fx, fy), l in wahl.items():
        im.paste(zs.bild(l['raster'], px), (fx * N * px, fy * N * px))
    d = ImageDraw.Draw(im)
    for (fx, fy), l in wahl.items():
        w, h = l['felder']
        d.rectangle((fx * N * px, fy * N * px, (fx + w) * N * px - 1, (fy + h) * N * px - 1), outline=(20, 20, 20))
        d.text((fx * N * px + 3, fy * N * px + 2), '%s %s' % (l['name'], l['lage']), fill=(255, 255, 255))
    return im


def main():
    startwert = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    gw = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    gh = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    rnd = random.Random(startwert)
    for _ in range(50):
        boss_xy, start, belegt, verb, pfad = grundriss(rnd, gw, gh)
        try:
            wahl = einsetzen(rnd, gw, gh, boss_xy, start, belegt, verb)
            break
        except RuntimeError:
            continue
    raster, fest, symmetrie = zusammensetzen(gw, gh, wahl)
    os.makedirs(ZIEL, exist_ok=True)
    grundriss_bild(gw, gh, wahl, boss_xy, start, verb, pfad).save(os.path.join(ZIEL, 'grundriss_%d.png' % startwert))
    for (fx, fy), l in sorted(wahl.items(), key=lambda t: (t[0][1], t[0][0])):
        print('  Feld %d,%d: %s (%s)' % (fx, fy, l['name'], l['lage']))
    bau, obj = bauordner(startwert)
    img = bauen(raster, fest, symmetrie, bau, obj)
    img.convert('RGB').save(os.path.join(ZIEL, 'karte_%d.png' % startwert))
    json.dump({'startwert': startwert, 'felder': [gw, gh],
               'stuecke': {'%d,%d' % k: {'name': l['name'], 'lage': l['lage']} for k, l in wahl.items()}},
              open(os.path.join(ZIEL, 'karte_%d.json' % startwert), 'w'), indent=1)
    print('fertig: maps/zufall/karte_%d.png (%dx%d Kacheln)' % (startwert, gw * N, gh * N))


if __name__ == '__main__':
    main()
