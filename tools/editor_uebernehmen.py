"""Aenderungen aus dem Editor (spiel/karte01.html) uebernehmen.

  python3 tools/editor_uebernehmen.py aenderungen.txt
  python3 tools/editor_uebernehmen.py < aenderungen.txt

Eingabe ist der Text von "Aenderungen kopieren":
  x,y=wert                      Kollision einer Kachel (1 frei, 2 gesperrt, 3 verdeckt)
  datei.png@x,y[~]=modus        Ebene eines Objekts (hinten, geteilt, vorne)
Andere Zeilen werden ignoriert.

Dauerhaft gespeichert in maps/karte01/ebenen/kollision_korrekturen.json und ebenen_korrekturen.json;
tools/karte01_ebenen.py wendet beide beim Neubauen an. Mit Ebenen-Aenderungen werden alle Ebenen neu
gebaut, sonst nur Kollisionsraster, Masken und spiel/karte01_kollision.js.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import karte01_ebenen as E

KACHEL = re.compile(r'^\s*(\d+)\s*,\s*(\d+)\s*=\s*([123])\s*$')
OBJEKT = re.compile(r'^\s*(\S+\.png@\d+,\d+~?)\s*=\s*(hinten|geteilt|vorne)\s*$')


def main():
    text = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    kacheln, objekte = {}, {}
    for z in text.splitlines():
        m = KACHEL.match(z)
        if m:
            kacheln['%s,%s' % (m.group(1), m.group(2))] = int(m.group(3))
            continue
        m = OBJEKT.match(z)
        if m:
            objekte[m.group(1)] = m.group(2)
    if not kacheln and not objekte:
        sys.exit('Keine Zeilen der Form x,y=wert oder datei.png@x,y=modus gefunden.')

    k = json.load(open(os.path.join(E.OUT, 'kollision.json')))
    rows, cols = k['rows'], k['cols']
    ausserhalb = [p for p in kacheln if not (0 <= int(p.split(',')[0]) < cols and 0 <= int(p.split(',')[1]) < rows)]
    if ausserhalb:
        sys.exit('Ausserhalb der Karte (%dx%d): %s' % (cols, rows, ', '.join(ausserhalb)))

    if objekte:
        bekannt = {E.objekt_key(o) for o in json.load(open(os.path.join(E.OBJ, 'platzierung.json')))}
        fremd = [p for p in objekte if p not in bekannt]
        if fremd:
            sys.exit('Unbekannte Objekte (platzierung.json geaendert?): %s' % ', '.join(fremd))
        alle_o = E.ebenen_korrekturen_laden()
        alle_o.update(objekte)
        json.dump({'beschreibung': 'Ebene je Objekt aus dem Editor (hinten = unter dem Spieler, geteilt = Fuss '
                                   'unten/Rest oben, vorne = ueber dem Spieler); von tools/karte01_ebenen.py angewendet.',
                   'objekte': dict(sorted(alle_o.items()))}, open(E.EBENEN_KORREKTUREN, 'w'), indent=1)

    if kacheln:
        alle_k = E.korrekturen_laden()
        alle_k.update(kacheln)
        alle_k = dict(sorted(alle_k.items(), key=lambda kv: tuple(reversed([int(v) for v in kv[0].split(',')]))))
        json.dump({'beschreibung': 'Handkorrekturen der Kollision (x,y -> 1 frei, 2 gesperrt, 3 verdeckt); '
                                   'wird von tools/karte01_ebenen.py nach der Berechnung angewendet.',
                   'kacheln': alle_k}, open(E.KORREKTUREN, 'w'), indent=1)

    if objekte:
        E.main()                                # Ebenen neu bauen (wendet auch die Kollisionskorrekturen an)
    else:
        klasse = np.array([[int(c) for c in z] for z in k['raster']])
        E.korrekturen_anwenden(klasse)
        E.kollision_schreiben(klasse)
    print('Uebernommen: %d Kacheln, %d Objekte.' % (len(kacheln), len(objekte)))


if __name__ == '__main__':
    main()
