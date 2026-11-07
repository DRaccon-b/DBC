"""Objekte fuer Karte 17 (Our War Game!) - Anspielungen auf die Virus-Linie nur ueber Farben und Motive.

  python3 tools/karte17_bauen.py && python3 tools/karte17_objekte.py && python3 tools/karte17_bauen.py

Linke Insel (fruehe Stufen): gefleckte Virus-Eier, Eier-Haufen (Vervielfachen), Kabel-Kokons, Kugelsonde, Pixel-Schutt.
Rechte Insel (spaete Stufen): Kabel-Spinnennetz, Knochenstacheln, Riesenhorn, befallener Server, Tentakel, Kristall,
Virus-Knospe, umrankter Pylon. Aufstellplaetze, Teleporter und Spawn-Ring bleiben frei; keine Reihen.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from karte16_objekte import platzieren

T = 16
L, RX, OBEN = 3, 35, 3          # linke Kante der Inseln, obere Kante (Kacheln)
G = 'glut'
EINTRAEGE = [(n, (x0 + cx) * T, OBEN + r, 'virusglut', False) for (n, x0, cx, r) in [
    ('gross/01', L, 14.5, 6),                              # grosse Objekte zuerst: Kabel-Kokon mit Kern (links)
    ('gross/03', RX, 19.5, 17), ('gross/00', RX, 5.5, 10),   # Hoernerkrater, Knochenkristall (rechts)
    ('virus/00', L, 3.5, 4), ('virus/02', L, 9.5, 2), ('virus/01', L, 22.5, 5), ('virus/11', L, 24.5, 18),
    ('virus/15', L, 6.5, 12), ('virus/08', L, 17.5, 20), ('virus/09', L, 20.5, 8),
    ('virus/04', RX, 3.5, 4), ('virus/03', RX, 11.5, 3), ('virus/06', RX, 20.5, 5), ('virus/05', RX, 25.5, 3),
    ('virus/10', RX, 14.5, 11), ('virus/13', RX, 9.5, 13), ('virus/07', RX, 17.5, 20),
    ('virus/04', RX, 25.5, 20),
]]

if __name__ == '__main__':
    platzieren('karte17', EINTRAEGE, 0)
