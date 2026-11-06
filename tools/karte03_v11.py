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
    # Meer auch oben und rechts bis zum Kartenrand (Sandwaende oben/rechts entfallen), mit Buchten;
    # die Arena behaelt einen Sandstrand, der Teleporter rechts eine Landzunge
    kueste = [
        {'art': 'meer', 'r': [6, 0, 111, 2]}, {'art': 'meer', 'e': [20, 2.5, 7, 2.6]},
        {'art': 'meer', 'e': [76, 3, 6, 2.4]}, {'art': 'meer', 'e': [36, 2, 4, 2]},
        {'art': 'meer', 'r': [107, 0, 111, 79]}, {'art': 'meer', 'e': [105.5, 32, 3, 6]},
        {'art': 'meer', 'e': [106, 51, 2.6, 5]}, {'art': 'meer', 'e': [106, 75, 2.5, 4]},
        {'art': 'sand', 'e': [52.5, 13.5, 15, 14.2]},              # Arena mit Strand davor
        {'art': 'sand', 'e': [106.5, 65.5, 6.5, 4.6]},             # Landzunge zum Teleporter rechts
    ]
    boden = boden[:1] + kueste + boden[1:]
    neu['boden'] = boden
    neu['sandwand'].pop('oben', None)
    neu['sandwand'].pop('rechts', None)
    neu['sandwand']['unten']['x'] = [0, 111]              # Vordergrund-Duene ueber die ganze Breite
    # Holzsteg von der Insel nach Sueden (x0, x1, y0, y1 in Kacheln)
    neu['inselsteg'] = [94, 97, 17, 25]
    neu['_v11'] = 'Regeln v1.1 (tools/karte03_v11.py), Original: v1.0/layout_v1.0.json'
    json.dump(neu, open(os.path.join(KARTE, 'layout.json'), 'w'), indent=1)
    print('Karte 03 v1.1 Layout geschrieben')


if __name__ == '__main__':
    main()
