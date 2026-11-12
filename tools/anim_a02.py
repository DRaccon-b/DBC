"""Zusatz-Animationen der A02-Karten (Nutzer: "Animiere alles") -> Felder in platzierung.json

  python3 tools/anim_a02.py [karteNN ...]       (ohne Argument: alle A02-Karten)

Die Animationen selbst stehen in karte04_bauen (TEILANIM: bildschirm, leds, blasen, maschine, teil_drehen, wimpel,
blitze, brunnen_strahl, lampions). Hier steht je Objekt (basis), welche Animation es bekommt und welche Pixelboxen
bewegt werden duerfen (Boxen im ungespiegelten Sprite; fuer *_m-Varianten wird gespiegelt).
'teil' statt 'anim': Zusatz zu einer bestehenden Licht-Animation (z. B. Lampe leuchtet UND Blitze knistern).
Wird von regeln_a02.objekte_pruefen am Ende jedes A02-Objektskripts aufgerufen.
"""
import json, math, os, sys
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
A02 = ['karte20', 'karte21', 'karte23', 'karte24', 'karte25', 'karte26', 'karte27', 'karte28', 'karte07', 'karte29',
       'karte30', 'karte31', 'karte32', 'karte33']

ANIM = {
    'karte21': {   # Fernseher flimmern, Zirkuszelt-Wimpel wehen
        'tv/00': {'anim': 'bildschirm', 'schirm': [[4, 9, 20, 22]]},
        'tv/01': {'anim': 'bildschirm', 'schirm': [[4, 5, 20, 19]]},
        'tv/02': {'anim': 'bildschirm', 'schirm': [[9, 9, 24, 22]], 'kaputt': True},
        'tv/03': {'anim': 'bildschirm', 'schirm': [[5, 5, 22, 18]]},
        'tv/04': {'anim': 'bildschirm', 'schirm': [[4, 8, 21, 24]]},
        'tv_gross/00': {'anim': 'bildschirm', 'schirm': [[8, 11, 34, 29]]},
        'k04/zirkuszelt': {'anim': 'wimpel', 'wimpel': [[44, 0, 57, 9, 1], [81, 0, 93, 9, 1], [43, 26, 56, 36], [81, 26, 94, 37]]},
    },
    'karte24': {   # Pumpe nickt, Computer laeuft, Fahne der Bergstation weht
        'mine/08': {'anim': 'teil_drehen', 'dreh': [{'box': [0, 0, 56, 27], 'ohne_box': [17, 18, 32, 27],
                                                      'punkt': [24, 16], 'amp': 4, 'stange': [0, 27, 5, 50],
                                                      'stangen': [[37, 25, 44, 35]]}]},   # Treibstange rechts folgt
        'schrein/02': {'anim': 'maschine', 'schirm': [[8, 4, 19, 15], [29, 4, 40, 15]], 'leds': True,
                       'led_box': [[2, 17, 46, 28]]},
        'bergstation/00': {'anim': 'wimpel', 'wimpel': [[85, 0, 99, 11]], 'wimpel_frei': True},
    },
    'karte26': {   # Labor und Thronraum: Maschinen laufen, Tesla-Saeulen knistern (Nutzer)
        'digifeuer/13': {'teil': 'blitze', 'lampe_box': [24, 0, 36, 44], 'licht_farbe': [150, 255, 210]},
        'digifeuer/00': {'teil': 'flammen_boxen', 'flammen_box': [[6, 0, 36, 21]], 'flammen_alle': True, 'flammen_amp': 2.6,
                         'lampe_box': [6, 0, 36, 21], 'licht_farbe': [150, 230, 255]},   # Digi-Flammen zuengeln
        'thron_gross/01': {'anim': 'maschine', 'schirm': [[11, 3, 26, 17], [31, 1, 63, 16], [67, 4, 83, 18]],
                           'leds': True, 'led_box': [[6, 28, 88, 46]]},
        'thron/00': {'anim': 'bildschirm', 'schirm': [[9, 10, 57, 36]]},          # Holotisch flimmert
        'tank3/00': {'anim': 'maschine', 'fluessig': [[16, 16, 58, 66, 'cyan']], 'leds': True, 'led_box': [[18, 72, 58, 86]]},
        'kapsel2/02': {'anim': 'maschine', 'fluessig': [[12, 16, 30, 50, 'gruen']], 'leds': True, 'led_box': [[8, 2, 32, 14]]},
        'kapsel2/11': {'anim': 'maschine', 'fluessig': [[4, 4, 58, 50, 'rot']], 'leds': True,
                       'led_box': [[22, 46, 42, 60], [48, 34, 62, 48]]},
        'kapsel2/04': {'teil': 'leds', 'led_box': [[8, 36, 52, 55]]},
        'labor/09': {'anim': 'maschine', 'leds': True, 'led_max': 4},
        'labor/01': {'anim': 'maschine', 'schirm': [[7, 2, 28, 13]]},            # Reagenzglaeser leuchten nicht
        'halle/02': {'anim': 'teil_drehen', 'dreh': [{'bis_y': 35, 'punkt': [13, 35], 'amp': 3}]},
    },
    'karte20': {
        'k06/tv_treppe': {'schirm_box': [16, 36, 57, 67]},                    # Wirbel nur im Bildschirm
    },
    'karte29': {
        'k07_portal': {'anim': 'portal_box', 'wirbel': [24, 27, 19]},          # grauer Wirbel dreht sich
    },
    'karte25': {
        'leuchtturm/00': {'lampe_box': [14, 22, 31, 39]},                       # nur die Laterne leuchtet
    },
    'karte27': {
        'schrein/00': {'kristall_box': [22, 0, 56, 78]},                      # Schrein-Kristall schimmert
    },
    'karte07': {   # Steinlaterne leuchtet, Raeucherkessel dampft; Befunde der Animationspruefung
        'mittel/00': {'anim': 'lampe'},
        'azul/04': {'anim': 'rauch', 'rauch_box': [22, 0, 38, 16]},
        'mittel/12_sw': {'anim': 'portal_box', 'wirbel': [25, 28, 17]},       # grauer Wirbel dreht sich, Ring fest
        'azul/01': {'anim': 'standarte'},                                     # nur das Tuch weht, Stange fest
        'frucht/tomate': {'anim': 'laub_wehen'},                              # Pfahl fest
        'frucht/trauben': {'anim': 'laub_wehen', 'laub_bis': 0.8, 'amp': 1.0},   # Spalier fest
        'mittel/03': {'glitzer': 'cyan'},                                     # Kristall glitzert, nicht der Busch
        'azul/00': {'licht': [23, 10], 'licht_box': [6, 0, 40, 22]},          # Schein auf der Kugel
    },
    'karte31': {   # Spielplatz schaukelt/wippt, Papierlaternen an Ramen-Laden und Izakaya glimmen
        'karte10/spielplatz/01': {'anim': 'teil_drehen', 'dreh': [
            {'box': [12, 6, 29, 39], 'punkt': [19, 5], 'amp': 7},
            {'box': [32, 6, 49, 39], 'punkt': [41, 5], 'amp': 7, 'phase': 1.9}]},
        'karte10/spielplatz/02': {'anim': 'teil_drehen', 'dreh': [   # Brett kippt um den Bolzen, Bock bleibt fest
            {'box': [0, 0, 62, 30], 'ohne_boxen': [[27, 15, 42, 30], [21, 21, 42, 30]], 'punkt': [31, 15], 'amp': 6}]},
        'gebaeude/laden_1': {'anim': 'lampions', 'lampions': [[0, 77, 10, 92]]},
        'gebaeude/laden_4': {'anim': 'lampions', 'lampions': [[4, 77, 11, 87], [24, 77, 31, 87], [64, 77, 72, 87],
                                                              [84, 77, 91, 87]]},
    },
    'karte32': {   # kaputte Kronleuchter: Kerzen flackern; Friedhofsbrunnen fliessen
        'karte32/leuchter/00': {'anim': None},          # Kerzen am Boden sind erloschen (keine Flammen im Sprite)
        'karte32/leuchter/01': {'anim': None},
        'karte09/moebel/01': {'anim': 'kerzen', 'flammen_box': [[11, 0, 15, 4], [1, 4, 5, 10], [21, 6, 25, 11]]},
        'karte09/k8/klein/05': {'anim': None},          # Steinhaufen bewegen sich nicht
        'karte09/k8/klein/07': {'anim': None},          # liegender Ast bewegt sich nicht
        'karte09/turm/09': {'anim': 'brunnen_strahl', 'becken': [8, 38, 44, 48], 'strahl_box': [6, 18, 46, 46],
                            'strahl_min': 95},
    },
}


def _spiegeln(werte, breite):
    """Box [x0, y0, x1, y1] bzw. Punkt [x, y] an der senkrechten Sprite-Achse spiegeln."""
    if len(werte) == 2:
        return [breite - 1 - werte[0], werte[1]]
    x0, y0, x1, y1 = werte[:4]
    return [breite - x1, y0, breite - x0, y1] + list(werte[4:])


def felder(o, cfg, breite):
    neu = json.loads(json.dumps(cfg))
    if '_m.' in o['datei'] or o.get('spiegeln'):
        for k in ('schirm', 'led_box', 'fluessig', 'wimpel', 'lampions'):
            if k in neu:
                neu[k] = [_spiegeln(b, breite) for b in neu[k]]
        for k in ('flammen_box',):
            if k in neu:
                neu[k] = [_spiegeln(b, breite) for b in neu[k]]
        for k in ('becken', 'rauch_box', 'licht_box', 'strahl_box', 'glitzer_box', 'licht', 'lampe_box', 'schirm_box', 'kristall_box'):
            if k in neu:
                neu[k] = _spiegeln(neu[k], breite)
        if 'wirbel' in neu:
            neu['wirbel'] = [breite - 1 - neu['wirbel'][0]] + neu['wirbel'][1:]
        for d in neu.get('dreh', []):
            for k in ('box', 'ohne_box', 'stange'):
                if k in d:
                    d[k] = _spiegeln(d[k], breite)
            d['punkt'] = _spiegeln(d['punkt'], breite)
            d['amp'] = -d.get('amp', 4)
        if 'wimpel' in neu:
            neu['wimpel_links'] = True
    return neu


def anwenden(karte):
    cfg = ANIM.get(karte)
    if not cfg:
        return 0
    pf = os.path.join(ROOT, 'assets', 'objekte', karte, 'platzierung.json')
    objs = json.load(open(pf))
    n = 0
    for o in objs:
        c = cfg.get(o['basis'])
        if not c:
            continue
        breite = Image.open(os.path.join(os.path.dirname(pf), o['datei'])).width
        o.update(felder(o, c, breite))
        n += 1
    json.dump(objs, open(pf, 'w'), indent=0)
    print('%s: %d Objekte mit Zusatz-Animation' % (karte, n))
    return n


if __name__ == '__main__':
    for k in (sys.argv[1:] or A02):
        anwenden(k)
