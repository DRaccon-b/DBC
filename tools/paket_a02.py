"""Abgabepaket je Karte (A01 + A02): Kollision, Tilesets, README, Standbild, Discord-GIFs (4 und 16 Bilder) -> ZIP

  python3 tools/paket_a02.py karteNN [...]      (ohne Argument: alle 17 Karten)

Ablauf je Karte: tools/kollision.py -> maps/karteNN/ebenen/, tools/tileset_export.py --kein-zip -> maps/karteNN/tileset/,
dann maps/karteNN/<version>/ mit README.md, <Name>_<version>.png, _discord.gif (4 Bilder, Tileset-Takt),
_discord_16.gif (16 Bilder, 110 ms) und dem ZIP <Name>_<version>.zip (inkl. kollision/ und tileset/).
"""
import os, shutil, subprocess, sys, zipfile
import json
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
T = 16
KARTEN = {   # karte: (Name, Version, Gebiet, Beschreibung)
    'karte16': ('The_Network', 'v1.1', 'A01 Nr. 1', 'Ankunft im Netz: schmaler Steg zur runden Plattform mit Firewall-Tor und '
                'Computer "Dungeon Records"; Leere mit blauen Datenstraengen und schwebenden Fragmenten.'),
    'karte17': ('Our_War_Game', 'v1.1', 'A01 Nr. 2', 'Zwei schwebende Raeume im Netz, verbunden ueber die Leere; '
                'Aufstellfelder, Marker und Teleporter im Stil von Karte 16.'),
    'karte19': ('Revenge', 'v1.1', 'A01 Nr. 3', 'Zwei Raeume: links mit drei Druckplatten (spiegelsymmetrisch), rechts '
                'ein Hafen mit Wasserbecken und Pollern; Ausgang ueber goldene Pfeile.'),
    'karte20': ('Startdorf', 'v1.1', 'A02 Nr. 1', 'Startdorf mit Fernseher-Portal auf der Treppe, Strohhaeusern, Feldern, '
                'Windmuehle, Bach mit Bruecken und Wald ringsum.'),
    'karte21': ('Digi_Egg_Valley', 'v1.0', 'A02 Nr. 2', 'Tal der Digi-Eier: Schreinhof hinter der Mauer, Fluss mit drei '
                'Holzbruecken, Lager mit Zirkuszelt, flimmernde Fernseher, Wald ringsum.'),
    'karte23': ('Harvest_Hills', 'v1.0', 'A02 Nr. 3', 'Bauernland: Felder, Hecken, Scheune und Silo, Muehlenplateau, '
                'Teich mit Bach, terrassierte Senke mit Treppen.'),
    'karte24': ('The_Kaisers_Canyon', 'v1.0', 'A02 Nr. 4', 'Roter Canyon: Schrein-Arena mit Bannern, Mine mit Loren und '
                'Oelpumpe, Seilbahn mit wippenden Gondeln, Lager und Bergstation.'),
    'karte25': ('Sunset_Bay', 'v1.0', 'A02 Nr. 5', 'Strand mit Huetten, Palmen und Stegen, Plateau mit Leuchtturm, '
                'terrassiertes Meer mit Schaum am 45-Grad-Raster und das Kaiser-Flaggschiff.'),
    'karte26': ('The_Kaisers_Fortress', 'v1.0', 'A02 Nr. 6', 'Festung des Kaisers: Thronraum mit Konsolen, Digi-Feuern und '
                'Tesla-Saeulen, Labore mit Tanks und Kapseln, Zellentrakt, Halle mit Wandschildern.'),
    'karte27': ('Destiny_Lake', 'v1.0', 'A02 Nr. 7', 'Seenlandschaft mit Wasserfaellen, Kristallschrein, Moor, Stegen, '
                'bluehenden Baeumen und gestrandetem Schiff.'),
    'karte28': ('Tower_Forest', 'v1.1', 'A02 Nr. 8', 'Dunkler Wald mit Schlamm-Arena, Spinnen-Arena, schwarzen Obelisken, '
                'Wiesen mit Lagerfeuer und geschwungenen Feldwegen.'),
    'karte07': ('The_Holy_Peaks', 'v1.0', 'A02 Nr. 9', 'Schwebende Bergkuppen ueber dem Wolkenmeer: Pagode, Azul-Hof mit '
                'Raeucherkessel, Beete, Kristalle, Drachenbruecke, Schnee und Steinlaternen.'),
    'karte29': ('The_Sea_of_Darkness', 'v1.1', 'A02 Nr. 10', 'Graues Meer der Dunkelheit: Strand mit Wracks und Felsnadeln, '
                'Tempelplatz mit Kraken-Mosaik, Leuchtturm, Stufenmeer am 45-Grad-Raster.'),
    'karte30': ('Odaiba', 'v1.0', 'A02 Nr. 11', 'Stadtteil Odaiba: Fernsehgebaeude, Bueros, Bahnhof und Hochbahn, '
                'Riesenrad, Statue, Strand und Meer mit Pier.'),
    'karte31': ('Highton_View_Terrace', 'v1.0', 'A02 Nr. 12', 'Wohnsiedlung: Wohnbloecke, Ladenzeile, Bahnhof, Park mit '
                'Spielplatz und Uhr, Strassen und Fussgaengerbruecke.'),
    'karte32': ('Dream_Ruins', 'v1.0', 'A02 Nr. 13', 'Traumruinen eines Schlosses in der Sternenleere: Turmportal, '
                'zerbrochene Saeulen und Kronleuchter, Friedhof mit Brunnen, schwebende Traumobjekte.'),
    'karte33': ('The_World_of_Dreams', 'v1.0', 'A02 Nr. 14', 'Runde Traumplattform mit Ringmauer und drei Runen, vier '
                'Raum-Zeit-Risse in andere Karten, surreale schwebende Objekte.'),
}

README = """# {titel} ({gebiet}) {version}

{cols} x {rows} Kacheln zu 16 px ({w} x {h} px).

## Inhalt
{beschreibung}

Alle Bodenkanten liegen am 16er-Raster mit 45-Grad-Schraegen; Objekte stehen am Raster, hohe Objekte blockieren nur
am Sockel. Kontrolliert nach allen Regeln (CLAUDE.md) inkl. Agenten-Gesamtpruefung.

## Animation
- `{name}_{version}_discord_16.gif` - 16 Bilder, 110 ms (fluessige Fassung)
- `{name}_{version}_discord.gif` - 4 Bilder (Takt der Tilesets)
Bewegt sich nur, was sich wirklich bewegt (Wasser, Feuer, Licht, Pflanzen im Wind, Stoff, Maschinen); Steine,
Stangen und Mauern bleiben ruhig.

## Dateien
- `{name}_{version}.png` - Standbild
- `kollision/` - `kollision.json`, `kollision.txt` (1 begehbar, 2 gesperrt, 3 begehbar + verdeckt),
  `ebene2_kollision.png`, `kollision_overlay.png`
- `tileset/` - Boden- und Objekt-Tilesets am 16x16-Raster, animierte Teile am exakt selben Platz, Tiled-Karte (`.tmx`)

Erzeugt mit `tools/{karte}_*.py`, `tools/kollision.py`, `tools/tileset_export.py`, `tools/paket_a02.py`.
"""


def paket(karte, ohne_tileset=False):
    name, version, gebiet, text = KARTEN[karte]
    K = os.path.join(ROOT, 'maps', karte)
    tools = os.path.dirname(os.path.abspath(__file__))
    subprocess.run([sys.executable, os.path.join(tools, 'kollision.py'), karte], check=True)
    if not ohne_tileset:
        subprocess.run([sys.executable, os.path.join(tools, 'tileset_export.py'), karte, '--kein-zip'], check=True)
    vdir = os.path.join(K, version)
    os.makedirs(vdir, exist_ok=True)
    for d in os.listdir(vdir):                                       # alte ZIPs dieser Version ersetzen
        if d.endswith('.zip'):
            os.remove(os.path.join(vdir, d))
    stand = Image.open(os.path.join(K, 'terrain.png'))
    w, h = stand.size
    stand.save(os.path.join(vdir, '%s_%s.png' % (name, version)))
    shutil.copy(os.path.join(K, 'animation', '%s_discord.gif' % karte), os.path.join(vdir, '%s_%s_discord.gif' % (name, version)))
    shutil.copy(os.path.join(K, 'animation', '%s_discord_16.gif' % karte),
                os.path.join(vdir, '%s_%s_discord_16.gif' % (name, version)))
    readme = README.format(titel=name.replace('_', ' '), gebiet=gebiet, version=version, cols=w // T, rows=h // T, w=w, h=h,
                           beschreibung=text, name=name, karte=karte)
    open(os.path.join(vdir, 'README.md'), 'w').write(readme)
    ziel = os.path.join(vdir, '%s_%s.zip' % (name, version))
    with zipfile.ZipFile(ziel, 'w', zipfile.ZIP_DEFLATED) as z:
        for d in ('README.md', '%s_%s.png' % (name, version), '%s_%s_discord.gif' % (name, version),
                  '%s_%s_discord_16.gif' % (name, version)):
            z.write(os.path.join(vdir, d), d)
        for ordner, ziel_ordner in ((os.path.join(K, 'ebenen'), 'kollision'), (os.path.join(K, 'tileset'), 'tileset')):
            if not os.path.isdir(ordner):
                continue
            for wurzel, _, dateien in os.walk(ordner):
                for d in sorted(dateien):
                    if ordner.endswith('ebenen') and not d.startswith(('kollision', 'ebene2')):
                        continue
                    p = os.path.join(wurzel, d)
                    z.write(p, os.path.join(ziel_ordner, os.path.relpath(p, ordner)))
    print('%s: %s (%.1f MB)' % (karte, os.path.relpath(ziel, ROOT), os.path.getsize(ziel) / 1e6), flush=True)


if __name__ == '__main__':
    for k in (sys.argv[1:] or list(KARTEN)):
        paket(k)
