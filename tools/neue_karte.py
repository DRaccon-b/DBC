"""Neue Karte aus einer Vorbild-Karte anlegen (Grundgeruest fuer den Skill "neue-karte").

  python3 tools/neue_karte.py 34 "Name der Karte" --vorbild karte21 --gebiet A03 --nr 1 --vorlage pfad/zur/vorlage.png
          [--beschreibung "Kurzbeschreibung"]

Legt an:
  tools/karte34_{layout,kacheln,bauen,objekte}.py   Kopie der Vorbild-Skripte (karteXX -> karte34), zum Anpassen
  assets/vorlagen/karte34_vorlage.png               die Vorlage
  assets/karte34/                                   Grundkacheln des Vorbilds (falls vorhanden)
  assets/objekte/karte34/                           Sprites des Vorbilds (Wiederverwenden zuerst, Regel 3) -
                                                    ohne platzierung.json und varianten/
  maps/karte34/karte.json                           Name, Version, Gebiet, Beschreibung (fuer Paket und Tileset)
  maps/GEBIETE.md                                   neue Zeile im Gebiet
Danach: Layout an die Vorlage anpassen (Masse, Klassen-Farben REF, Sonderflaechen), bauen, objekte, bauen,
animation_a02 (16 + 4), Pruef-Workflow (.claude/workflows/karte_pruefen.js), Fehler beheben, paket_a02.

Vorbild-Katalog (welche Karte als Grundgeruest):
  karte20 Wiese/Dorf, Wald ringsum, Bach mit Bruecken, Plateau mit Treppe
  karte21 Tal mit Fluss + Bruecken, Mauer mit Tor, Platz, Lager
  karte23 Felder, Hecken, Terrassen, Senke, Teich
  karte24 Canyon/Wueste: Klippen, Arenen, Mine, Seilbahn
  karte25 Strand + Meer (45-Grad-Kueste, Schaum), Plateau mit Leuchtturm, Stege
  karte26 Innenraum/Festung: Raeume, Waende, Maschinen
  karte27 Seen, Wasserfaelle, Moor, Wald
  karte28 dunkler Wald, Arenen auf Erhoehung
  karte07 schwebende Inseln ueber Wolkenmeer, Terrassen, Bruecke
  karte29 graues Meer in Stufen, Strand, Tempelplatz
  karte30 Stadt am Meer: Strassen, Gebaeude, Hochbahn, Pier
  karte31 Wohnsiedlung: Strassen, Park, Laeden
  karte32 Schloss/Ruine in der Sternenleere, Friedhof
  karte33 runde Plattform in der Leere, Risse in andere Karten
  karte16 / karte17 / karte19  Netz-Plattformen (Digitalwelt)
"""
import argparse, json, os, re, shutil

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
TOOLS = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('nr')
    ap.add_argument('name')
    ap.add_argument('--vorbild', required=True)
    ap.add_argument('--gebiet', default='A03')
    ap.add_argument('--nr-im-gebiet', '--nr', dest='nr_g', default='?')
    ap.add_argument('--vorlage')
    ap.add_argument('--beschreibung', default='')
    a = ap.parse_args()
    neu = 'karte%02d' % int(a.nr)
    alt = a.vorbild
    n_alt, n_neu = alt[5:], neu[5:]
    if os.path.exists(os.path.join(TOOLS, neu + '_bauen.py')):
        raise SystemExit('%s existiert schon' % neu)
    ersetzen = [(alt, neu), ('Karte %s' % n_alt, 'Karte %s' % n_neu), ('Karte %d' % int(n_alt), 'Karte %d' % int(n_neu)),
                ('k%s_' % n_alt, 'k%s_' % n_neu)]
    for teil in ('layout', 'kacheln', 'bauen', 'objekte', 'baeume', 'gebaeude'):
        q = os.path.join(TOOLS, '%s_%s.py' % (alt, teil))
        if not os.path.exists(q):
            continue
        s = open(q).read()
        for x, y in ersetzen:
            s = re.sub(r'(?<![0-9])%s(?![0-9])' % re.escape(x), y, s)
        s = ('# Grundgeruest aus %s (tools/neue_karte.py) - an die Vorlage von %s "%s" anpassen!\n' % (alt, neu, a.name)) + s
        open(os.path.join(TOOLS, '%s_%s.py' % (neu, teil)), 'w').write(s)
        print('tools/%s_%s.py' % (neu, teil))
    if os.path.isdir(os.path.join(ROOT, 'assets', alt)):
        shutil.copytree(os.path.join(ROOT, 'assets', alt), os.path.join(ROOT, 'assets', neu), dirs_exist_ok=True)
    od_alt, od_neu = os.path.join(ROOT, 'assets', 'objekte', alt), os.path.join(ROOT, 'assets', 'objekte', neu)
    if os.path.isdir(od_alt):
        shutil.copytree(od_alt, od_neu, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('platzierung.json*', 'varianten'))
    os.makedirs(os.path.join(ROOT, 'maps', neu), exist_ok=True)
    if a.vorlage:
        shutil.copy(a.vorlage, os.path.join(ROOT, 'assets', 'vorlagen', '%s_vorlage.png' % neu))
    json.dump({'name': a.name.replace(' ', '_').replace("'", ''), 'titel': a.name, 'version': 'v1.0',
               'gebiet': '%s Nr. %s' % (a.gebiet, a.nr_g), 'beschreibung': a.beschreibung, 'vorbild': alt},
              open(os.path.join(ROOT, 'maps', neu, 'karte.json'), 'w'), ensure_ascii=False, indent=1)
    g = os.path.join(ROOT, 'maps', 'GEBIETE.md')
    s = open(g).read()
    kopf = '## %s' % a.gebiet
    zeile = '| %s | Karte %s – %s | in Arbeit (Vorbild %s) |' % (a.nr_g, n_neu, a.name, alt)
    if kopf not in s:
        s = s.rstrip() + '\n\n%s *(in Arbeit)*\n| Nr. | Karte | Stand |\n|---|---|---|\n%s\n' % (kopf, zeile)
    else:
        i = s.index(kopf)
        j = s.find('\n## ', i + 1)
        j = len(s) if j < 0 else j
        s = s[:j].rstrip() + '\n' + zeile + '\n' + s[j:]
    open(g, 'w').write(s)
    print('Karte %s "%s" angelegt (Vorbild %s, %s)' % (neu, a.name, alt, a.gebiet))


if __name__ == '__main__':
    main()
