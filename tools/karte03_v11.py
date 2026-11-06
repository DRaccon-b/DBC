"""Karte 03 (Server Desert) v1.1 - Regeln aus CLAUDE.md, Meer wie Karte 01, Oase als Insel.

  python3 tools/karte03_v11.py      # liest maps/karte03/v1.0/layout_v1.0.json, schreibt layout.json

- Meer links: breiter (6 Kacheln) und als terrassiertes Meer wie Karte 01 (Flachwasser, Schaum, zwei Stufen,
  Tiefsee, Felsen, Algen) - Klasse 'meer' (karte03_bauen: wasser_details.meer_terrassen).
- Oase oben rechts: Insel im Meer (Gras + Sandstrand ringsum), Holzsteg nach Sueden zum Weg.
- Sandwaende oben/unten beginnen erst hinter dem breiteren Meer.
"""
import copy, json, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte03')


def main():
    lay = json.load(open(os.path.join(KARTE, 'v1.0', 'layout_v1.0.json')))
    neu = copy.deepcopy(lay)
    boden = []
    for z in lay['boden']:
        if z['art'] == 'wasser' and z.get('r') == [0, 0, 3, 79]:
            boden.append({'art': 'meer', 'r': [0, 0, 5, 79]})
        elif z['art'] == 'sand' and z.get('r') == [0, 54, 4, 61]:
            boden.append({'art': 'sand', 'r': [0, 54, 6, 61]})
        elif z['art'] == 'weg' and z.get('r') == [0, 56, 5, 60]:
            boden.append({'art': 'weg', 'r': [0, 56, 7, 60]})
        elif z['art'] == 'gras' and z.get('e') == [95.5, 13, 6.2, 6.8]:
            # Insel: Meer, Sandstrand ringsum, Gras in der Mitte
            boden.append({'art': 'meer', 'e': [94, 14.5, 12.5, 10.5]})
            boden.append({'art': 'sand', 'e': [95, 12, 7.2, 5.4]})
            boden.append({'art': 'gras', 'e': [95.5, 11.5, 5.2, 3.8]})
        elif z['art'] == 'weg' and z.get('r') == [94, 18, 97, 30]:
            boden.append({'art': 'weg', 'r': [94, 26, 97, 30]})
            boden.append({'art': 'weg', 'r': [94, 14, 97, 17]})
        else:
            boden.append(z)
    # Grenzen nach Nutzer-Skizze: links Meer (bis zum unteren Rand), oben Sandwand bis vor die Lagune,
    # oben rechts Meer um die Insel bis zum Kartenrand, rechts unterhalb der Lagune wieder Sandwand
    kueste = [
        {'art': 'meer', 'r': [0, 0, 7, 79]},
        # natuerliche Kueste links: Buchten ins Land, Landzungen ins Meer (Haeuser, Steg, Teleporter ausgespart)
        {'art': 'meer', 'e': [8.4, 12, 1.4, 2.6]}, {'art': 'meer', 'e': [8.6, 27, 1.7, 4.5]},
        {'art': 'meer', 'e': [8.3, 45, 1.4, 3]}, {'art': 'meer', 'e': [8.5, 70, 1.6, 4]},
        {'art': 'sand', 'e': [6.5, 20, 1.8, 3.5]}, {'art': 'sand', 'e': [6.2, 37, 2.0, 4]},
        {'art': 'sand', 'e': [6.6, 65.5, 1.6, 2.5]}, {'art': 'sand', 'e': [6.8, 76, 1.5, 3]},
        {'art': 'sand', 'r': [0, 54, 8, 61]},                       # Landzunge zum Teleporter links
        {'art': 'meer', 'r': [83, 0, 111, 21]}, {'art': 'meer', 'e': [104, 21, 7, 3.2]},
        {'art': 'meer', 'e': [82.4, 10.5, 1.3, 2.2]}, {'art': 'sand', 'e': [84.2, 16, 1.4, 2.4]},
    ]
    for z in boden:                                                 # Pflasterflaechen am Zeltlager nicht ins Meer
        if z['art'] == 'kies' and z.get('r', [None])[0] == 6:
            z['r'] = [8] + z['r'][1:]
    boden = boden[:1] + kueste + [z for z in boden[1:] if not (z['art'] == 'meer' and z.get('r') == [0, 0, 5, 79])
                                   and not (z['art'] == 'sand' and z.get('r') == [0, 54, 6, 61])]
    neu['boden'] = boden
    neu['sandwand']['oben']['x'] = [9, 81]
    neu['sandwand']['oben']['ende_rechts_meer'] = True
    neu['sandwand']['oben']['enden_am_strand'] = True
    neu['sandwand']['unten']['x'] = [8, 111]
    neu['sandwand']['rechts'] = [{'x': [106, 111], 'y': [22, 63], 'front_unten': 20}, {'x': [106, 111], 'y': [69, 79]}]
    neu['steg'] = {'x': 2, 'y': 50, 'laenge': 6, 'breite': 3}
    # Holzsteg von der Insel nach Sueden (x0, x1, y0, y1 in Kacheln)
    neu['inselsteg'] = [94, 97, 17, 25]
    neu['_v11'] = 'Regeln v1.1 (tools/karte03_v11.py), Original: v1.0/layout_v1.0.json'
    json.dump(neu, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=1)
    print('Karte 03 v1.1 Layout geschrieben')


if __name__ == '__main__':
    main()
