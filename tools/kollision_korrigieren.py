"""Kollisions-Aenderungen aus dem Editor (spiel/karte01.html) uebernehmen.

  python3 tools/kollision_korrigieren.py aenderungen.txt
  python3 tools/kollision_korrigieren.py < aenderungen.txt

Eingabe ist der Text von "Aenderungen kopieren", eine Kachel je Zeile:  x,y=wert
(1 frei, 2 gesperrt, 3 verdeckt). Andere Zeilen werden ignoriert.

Die Korrekturen landen dauerhaft in maps/karte01/ebenen/kollision_korrekturen.json und werden
auch von tools/karte01_ebenen.py angewendet, gehen beim Neubauen also nicht verloren.
Danach neu geschrieben: kollision.json/.txt, ebene2_kollision.png, vorschau.png, spiel/karte01_kollision.js.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import karte01_ebenen as E

ZEILE = re.compile(r'^\s*(\d+)\s*,\s*(\d+)\s*=\s*([123])\s*$')


def main():
    text = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    neu = {}
    for z in text.splitlines():
        m = ZEILE.match(z)
        if m:
            neu['%s,%s' % (m.group(1), m.group(2))] = int(m.group(3))
    if not neu:
        sys.exit('Keine Zeilen der Form x,y=wert gefunden.')

    k = json.load(open(os.path.join(E.OUT, 'kollision.json')))
    rows, cols = k['rows'], k['cols']
    klasse = np.array([[int(c) for c in z] for z in k['raster']])
    ausserhalb = [p for p in neu if not (0 <= int(p.split(',')[0]) < cols and 0 <= int(p.split(',')[1]) < rows)]
    if ausserhalb:
        sys.exit('Ausserhalb der Karte (%dx%d): %s' % (cols, rows, ', '.join(ausserhalb)))

    alle = E.korrekturen_laden()
    alle.update(neu)
    alle = dict(sorted(alle.items(), key=lambda kv: tuple(reversed([int(v) for v in kv[0].split(',')]))))
    json.dump({'beschreibung': 'Handkorrekturen der Kollision (x,y -> 1 frei, 2 gesperrt, 3 verdeckt); '
                               'wird von tools/karte01_ebenen.py nach der Berechnung angewendet.',
               'kacheln': alle}, open(E.KORREKTUREN, 'w'), indent=1)

    vorher = klasse.copy()
    E.korrekturen_anwenden(klasse)
    E.kollision_schreiben(klasse)
    geaendert = int((vorher != klasse).sum())
    print('%d Kacheln eingelesen, %d im Raster geaendert, %d Korrekturen insgesamt.' % (len(neu), geaendert, len(alle)))


if __name__ == '__main__':
    main()
