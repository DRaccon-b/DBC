"""Form des Boss-Felds auf Karte 14 (Spiral Mountain: Summit) - pixelgenau, von Layout und Bau-Skript genutzt.

Formen: quadrat, achteck, rund (Manege), raute (Harlekin-Karo), pik (Spielkarten-Pik, Spitze zum Schloss, Stiel zur
Treppe), bastion (Quadrat mit runden Eckbastionen). Jede Form hat unten einen geraden Absatz fuer die Treppe.
"""
import numpy as np

T = 16
CX, CY = 40.5 * T, 18.0 * T          # Mitte des Boss-Felds (Spirale)
HX, HY = 11.5 * T, 11.0 * T          # halbe Breite/Hoehe des Rahmens (Spalten 29-51, Reihen 7-28)


def maske(form, xx, yy):
    """xx, yy: Pixelkoordinaten (Kachel-Mitten oder Pixel). Liefert die Boss-Feld-Maske."""
    dx, dy = (xx - CX), (yy - CY)
    ax, ay = np.abs(dx), np.abs(dy)
    box = (ax <= HX) & (ay <= HY)
    if form == 'achteck':                                                     # hinten gerade ueber die ganze Front,
        m = box & ((dy <= 0) | (ax / HX + ay / HY <= 1.5))                    # nur vorne abgeschraegt
    elif form == 'rund':
        m = (dx / HX) ** 2 + (dy / HY) ** 2 <= 1.0
    elif form == 'raute':
        m = box & (ax / HX + ay / HY <= 1.18)
    elif form == 'pik':
        lx, ly, lr = 0.47 * HX, 0.18 * HY, 0.56 * HX                         # zwei runde Lappen unten
        lappen = ((ax - lx) ** 2 + (dy - ly) ** 2 <= lr ** 2)
        spitze = (dy <= ly) & (dy >= -HY) & (ax <= (dy + HY) / (HY + ly) * (lx + lr * 0.98))
        stiel = (dy >= 0.35 * HY) & (dy <= HY) & (ax <= 0.2 * HX + (dy - 0.35 * HY) / (0.65 * HY) * 0.25 * HX)
        m = lappen | spitze | stiel
    elif form == 'bastion':
        k, r = 0.78, 0.3 * HY
        kern = (ax <= k * HX) & (ay <= k * HY)
        ecken = ((ax - k * HX) ** 2 + (ay - k * HY) ** 2 <= r ** 2)
        m = kern | ecken
    else:                                                                     # quadrat
        m = box
    absatz = (ax <= 3.0 * T) & (dy >= HY - 2.2 * T) & (dy <= HY)             # gerader Absatz fuer die Treppe
    return m | absatz
