"""Karte 51 - Zhuqiaomon's Sanctuary (A03 Nr. 17), Gelaende nach maps/karte51/layout.json.

Arena des Zhuqiaomon (Suzaku Gate): erhoehter Ziegelplatz mit Rautenmuster-Arena, Treppe nach Sueden, Felsrand,
Brandflecken (Nutzer: etwas verbrannt). Aufbau wie Karte 50 (Heiligtum auf Terrassen (Nutzer: echte Terrassen, steigt nach Norden an): Felsboden, Pflasterwege und -plaetze, Wiesen,
drei Terrassenkanten mit Felsfront (45-Grad-Raster), Steintreppen unter den Torii als einziger Uebergang, abgesenkter Hof
oben links (Nutzer) mit Steinplattenboden und eingeschnittener Treppe von Sueden, erhoehter Felsrand ringsum (gesperrt).

  python3 tools/karte51_layout.py && python3 tools/karte51_bauen.py
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import karte_bauen as kb
import karte04_bauen as k4
import karte06_bauen as k6
import karte20_bauen as k20
import karte48_bauen as k48

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
KARTE = os.path.join(ROOT, 'maps', 'karte51')
OBJ = os.path.join(ROOT, 'assets', 'objekte', 'karte51')
T = 16
N_FRAMES = 4
BILDDAUER = 250
k4.N_FRAMES = N_FRAMES
kb.N_FRAMES = N_FRAMES
H = k4.H
weich, zell_maske, flaeche = k4.weich, k4.zell_maske, k20.flaeche
k4.SCHATTEN = {'farbe': (22, 28, 44), 'dx': 0.3, 'dy': 0.15, 'kern': 100, 'wurf': (66, 52)}
k4.RASTER45 = True
k4.FELS['berg47'] = ['#262b38', '#353d4e', '#465064', '#59657a', '#6e7b90', '#8693a8', '#a3afc2']   # graublauer Fels
LIPPE = ['#4e5868', '#5e6878', '#6e7888', '#7e8898', '#8e98a8', '#a0aab8']
FRONT = 24                               # Terrassen und Felsrand
SEITE = 6
faerben = k48.faerben


def texturen(cols, rows):
    basis = os.path.join(ROOT, 'assets', 'basis')
    sand = os.path.join(basis, 'sand_%d.png')
    gras = os.path.join(basis, 'gras_%d.png')
    kies = os.path.join(ROOT, 'assets', 'karte03', 'basis', 'kies_%d.png')
    return {
        'g': flaeche(k6.kacheln(sand, 5, faerben((96, 112, 132), (138, 152, 168), 0.3, 0.5)), cols, rows),   # Felsboden
        'w': flaeche(k6.kacheln(kies, 5, faerben((118, 124, 132), (172, 176, 182), 0.25, 0.6)), cols, rows),  # Pflaster
        'k': flaeche(k6.kacheln(kies, 5, faerben((96, 100, 104), (142, 146, 148), 0.25, 0.6)), cols, rows),   # dunkles Pflaster
        'n': flaeche(k6.kacheln(gras, 5, faerben((62, 112, 46), (108, 158, 72), 0.3, 0.5)), cols, rows),     # Wiese
        'h': flaeche(k6.kacheln(kies, 5, faerben((120, 134, 150), (172, 184, 198), 0.25, 0.6)), cols, rows),  # Felsrand (rau)
        'd': k48.platten(cols, rows, basis=(84, 92, 110), fuge=(52, 58, 72), seed=50),
        'z': k48.platten(cols, rows, basis=(128, 132, 134), fuge=(84, 88, 92), seed=51),                     # Ziegelplatz
    }


def verkohlen(a, lay, cols, rows, frame, wand=None):
    """Nutzer: verkohlter Bereich (Feuervogel) - Boden, Wiese, Pflaster und Felsfronten geschwaerzt (Russ, Asche),
    unregelmaessig ausfransender Rand, einzelne Glutpunkte glimmen (animiert)."""
    if 'brand' not in lay:
        return
    Hp, Wp = rows * T, cols * T
    km = np.kron(np.array([[c == '1' for c in z] for z in lay['brand']]), np.ones((T, T))).astype(np.float32)
    m = weich(km, 5.0, 0.0, 77, 0.5)
    if os.environ.get('K50_RANDFREI', '1') == '1':                   # Nutzer: flache Bergkante (Felsrand) bleibt unverbrannt
        rp = np.kron(np.array([[c == 'h' for c in z] for z in lay['klassen']]), np.ones((T, T), bool))
        rand_frei = rp.copy()
        for d in range(1, 30):                                       # Fronten im Fels gehoeren zum Rand
            rand_frei[d:] |= rp[:-d] & (wand[d:] if wand is not None else False)
        m &= ~rand_frei
    weit = weich(km, 12.0, 0.0, 78, 0.25) & ~m                        # Uebergang: gesprenkelt
    if os.environ.get('K50_RANDFREI', '1') == '1':
        weit &= ~rand_frei
    rs = np.random.RandomState(5077)
    rausch = rs.rand(Hp, Wp)
    rand_ = weit & (rausch < 0.35)
    af = a.astype(np.float32)
    kohle = np.array([38, 34, 36], np.float32)
    l_ = af.mean(axis=2, keepdims=True) / 255.0
    neu = kohle + (np.array([96, 90, 92], np.float32) - kohle) * np.clip(l_ * 1.3 - 0.15, 0, 1)
    from PIL import ImageFilter as _IF2
    fl_ = Image.fromarray((rs.rand(Hp // 4, Wp // 4) * 255).astype(np.uint8)).resize((Wp, Hp), Image.BICUBIC).filter(_IF2.GaussianBlur(6))
    flecken = np.array(fl_) < 120                                    # weiche Russflecken (kein Kachelraster)
    boden = m & ~(wand if wand is not None else np.zeros_like(m))
    tief = np.where(flecken, 0.36, 0.5)[..., None]                    # Russflecken: Textur bleibt sichtbar
    af[boden] = (af * tief + kohle * (1 - tief) * 0.55)[boden]
    # Kern (Nutzer: erste Version) - ganz verkohlt; das verrusste Band (zweite Version) bleibt als Uebergang ringsum
    from PIL import ImageFilter as _IF
    kern_k = np.array(Image.fromarray((km[::T, ::T] * 255).astype(np.uint8)).filter(_IF.MinFilter(5))) > 0   # 2 Kacheln
    kern = weich(np.kron(kern_k, np.ones((T, T))).astype(np.float32), 6.0, 0.0, 80, 0.5) & m
    kb_ = kern & boden
    af[kb_] = neu[kb_]
    m_weit = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(_IF2.MaxFilter(9))) > 0
    gras_ = m_weit & ~(wand if wand is not None else np.zeros_like(m)) & ~kern & (af[..., 1] > af[..., 0] + 6)   # Wiese ganz
    lg_ = af[gras_].mean(axis=1, keepdims=True)
    af[gras_] = lg_ * np.array([1.05, 0.88, 0.72]) * 0.9
    if wand is not None:                                             # Felsfronten nur verrusst (Relief bleibt)
        wm_ = m & wand
        af[wm_] = af[wm_] * np.where(kern[wm_], 0.48, 0.62)[:, None]
    af[rand_] = af[rand_] * 0.7 + (af[rand_] * 0.45 + kohle * 0.25) * 0.3
    asche = m & (rausch > 0.985)                                     # Ascheflocken
    af[asche] = np.array([140, 136, 134])
    a[:] = np.clip(af, 0, 255).astype(np.uint8)
    glut = m & (rausch < 0.0016)                                     # Glutpunkte glimmen (4er-Schleife)
    ys, xs = np.nonzero(glut)
    f = frame or 0
    for i, (y, x) in enumerate(zip(ys, xs)):
        stufe = (f + i) % 4
        c = [(255, 170, 60), (255, 120, 40), (200, 70, 30), (255, 140, 50)][stufe]
        a[y, x] = c
        if stufe in (0, 3):
            for dy, dx in ((0, 1), (1, 0)):
                if y + dy < Hp and x + dx < Wp and m[y + dy, x + dx]:
                    a[y + dy, x + dx] = (150, 60, 30)


def bodenstruktur(a, cls, cols, rows):
    """Nutzer: mehr Bodentextur wie in der Vorlage - flache Grasbueschel (PixelLab, Karte 45), Kiesel und Zweige direkt in
    den Felsboden und die Wiesen gestempelt (kein Objekt, kein Schatten, begehbar); locker in kleinen Gruppen, nicht auf
    Pflaster/Hof, nicht unter Objekten, nicht an Terrassenkanten."""
    Hp, Wp = rows * T, cols * T
    O = os.path.join(ROOT, 'assets', 'objekte')
    def lade(p_, ton=None):
        sp = np.array(Image.open(os.path.join(O, p_)).convert('RGBA')).astype(float)
        bb = Image.fromarray(sp.astype(np.uint8)).getbbox()
        sp = sp[bb[1]:bb[3], bb[0]:bb[2]]
        if ton is not None:
            sp[..., :3] *= np.array(ton)
        return sp
    gras = [lade('karte45/halme/%s.png' % n_, (0.92, 0.95, 0.9)) for n_ in ('00', '02', '03', '06')]
    verbrannt = [lade('karte50/brand_klein/%02d.png' % n_) for n_ in (0, 2, 15, 0, 6)]
    lay_ = json.load(open(os.path.join(KARTE, 'layout.json')))
    brand_k = np.array([[c == '1' for c in z] for z in lay_.get('brand', ['0' * cols] * rows)])
    klein = [lade('karte50/klein/03.png'), lade('karte04/klein/09.png', (0.85, 0.85, 0.9)), lade('karte04/klein/02.png')]
    kl = np.array([list(z) for z in cls])
    hpk = np.array([[int(c) for c in z] for z in json.load(open(os.path.join(KARTE, 'layout.json')))['hoehe']])
    innen = np.isin(kl, ['g', 'n'])
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            p_ = np.pad(np.isin(kl, ['g', 'n']) & (hpk == np.pad(hpk, 1, mode='edge')[1 + dy:1 + dy + rows, 1 + dx:1 + dx + cols]),
                        1, mode='edge')
            innen &= p_[1 + dy:1 + dy + rows, 1 + dx:1 + dx + cols]
    kante = np.zeros((rows, cols), bool)                             # 2 Reihen unter jeder Hoehenkante frei (Front)
    kante[1:] |= hpk[:-1] > hpk[1:]
    kante[2:] |= hpk[:-2] > hpk[2:]
    innen &= ~kante
    belegt = np.zeros((Hp, Wp), bool)
    pf_ = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf_):
        for o in json.load(open(pf_)):
            if os.path.exists(os.path.join(OBJ, o['datei'])):
                bb_ = Image.open(os.path.join(OBJ, o['datei'])).getbbox()
                if bb_:
                    belegt[max(0, o['y'] + bb_[3] - 40):o['y'] + bb_[3] + 8, max(0, o['x'] + bb_[0] - 6):o['x'] + bb_[2] + 6] = True
    for t in json.load(open(os.path.join(KARTE, 'layout.json')))['teleporter']:
        belegt[max(0, (t['y'] - 2) * T):(t['y'] + t['h'] + 2) * T, max(0, (t['x'] - 2) * T):(t['x'] + t['b'] + 2) * T] = True
    rs = np.random.RandomState(5050)
    zentren = [(y, x) for y in range(rows) for x in range(cols) if innen[y, x] and rs.rand() < (0.03 if kl[y, x] == 'w' else 0.13)]
    for (cy, cx) in zentren:
        for _ in range(rs.randint(1, 4)):
            yy, xx = cy + rs.randint(-1, 2), cx + rs.randint(-1, 2)
            if not (0 <= yy < rows and 0 <= xx < cols and innen[yy, xx]):
                continue
            sp = gras[rs.randint(0, 4)] if rs.rand() < 0.75 else klein[rs.randint(0, 3)]
            if brand_k[yy, xx]:
                sp = verbrannt[rs.randint(0, len(verbrannt))]
            if rs.rand() < 0.5:
                sp = sp[:, ::-1]
            h_, w_ = sp.shape[:2]
            py, px = yy * T + rs.randint(0, max(1, T - min(h_, T))), xx * T + rs.randint(0, max(1, T - min(w_, T)))
            if py + h_ > Hp or px + w_ > Wp or belegt[py:py + h_, px:px + w_].any():
                continue
            belegt[py - 3:py + h_ + 3, px - 3:px + w_ + 3] = True
            al = sp[..., 3:4] / 255.0
            a[py:py + h_, px:px + w_] = (a[py:py + h_, px:px + w_] * (1 - al) + sp[..., :3] * al).astype(np.uint8)


def bauen(frame=None, speichern=True):
    lay = json.load(open(os.path.join(KARTE, 'layout.json')))
    cls = lay['klassen']
    cols, rows = lay['groesse']
    Wp, Hp = cols * T, rows * T
    hp = np.kron(np.array([[int(c) for c in z] for z in lay['hoehe']]), np.ones((T, T), int))
    tex = texturen(cols, rows)
    a0 = tex['g'].copy()
    for art, sd in (('z', 2), ('w', 3), ('n', 7), ('h', 11)):
        m = weich(zell_maske(cls, art + ('tT' if art == 'z' else ''), cols, rows), 5.0, 0, sd)
        if art in 'wn':
            saum = weich(zell_maske(cls, art, cols, rows), 5.0, 0, sd, 0.36) & ~m
            a0[saum] = (a0[saum] * 0.93).astype(np.uint8)
        a0[m] = tex[art][m]
    bodenstruktur(a0, cls, cols, rows)
    if lay.get('arena'):                                             # Rautenmuster: durchgehendes 45-Grad-Ziegelband auf der Mitte
        ax0, ay0, ax1, ay1 = lay['arena']
        cxp, cyp = (ax0 + ax1 + 1) * T / 2.0, (ay0 + ay1 + 1) * T / 2.0
        yy, xx = np.mgrid[0:Hp, 0:Wp]
        d_ = np.abs(xx + 0.5 - cxp) + np.abs(yy + 0.5 - cyp)
        band = (d_ >= 6.0 * T) & (d_ < 7.0 * T)
        a0[band] = tex['z'][band]
        kante_ = band & ((d_ < 6.0 * T + 1) | (d_ >= 7.0 * T - 1))
        a0[kante_] = (a0[kante_] * 0.72).astype(np.uint8)
    a = a0.copy()
    frei = np.zeros((Hp, Wp), bool)
    for (x0, x1, ry, r_) in lay['treppen']:
        if r_ == 's':
            frei[ry * T - 4:ry * T + FRONT + 10, x0 * T:(x1 + 1) * T] = True
    wand = np.zeros((Hp, Wp), bool)
    for L in (1, 2):                                           # Terrassen von unten nach oben, je mit Front
        m = weich((hp >= L).astype(np.float32), 5, 0.0, 7 + L, 0.5)
        a[m] = a0[m]
        wand &= ~m
        wand |= k4.hoehenkanten(a, m, 'berg47', FRONT, SEITE, LIPPE, frei if L < 2 else np.zeros((Hp, Wp), bool), 50 + L,
                                berg=False)
    # Hohe Felswand: liegt das Gelaende vor einer Front mehr als eine Stufe tiefer, waechst die Wand je Stufe um FRONT
    hpx = hp.copy()
    for x in range(Wp):
        y = 1
        col = wand[:, x]
        while y < Hp:
            if col[y] and not col[y - 1]:
                y0 = y
                while y < Hp and col[y]:
                    y += 1
                if y < Hp and y0 > 0:
                    d = int(hpx[max(0, y0 - 2), x]) - int(hpx[min(Hp - 1, y + 2), x])
                    lauf = y - y0
                    if d >= 2 and FRONT - 6 <= lauf <= FRONT + 6:            # nur Fronten, keine Seitenwaende
                        for yy in range(y, min(Hp, y0 + lauf * d)):
                            a[yy, x] = a[y0 + (yy - y0) % lauf, x] if (yy - y0) % lauf > 2 else a[y0 + 4, x]
                            wand[yy, x] = True
                        ye = min(Hp - 1, y0 + lauf * d)
                        for k_, f_ in ((0, 0.7), (1, 0.85)):
                            if ye + k_ < Hp:
                                a[ye + k_, x] = (a[ye + k_, x] * f_).astype(np.uint8)
                        y = y0 + lauf * d
            y += 1
    if lay.get('rand') == 'flanke':                                   # eigener Bergzug: dunklere Felstextur auf dem Rand
        rm = weich(zell_maske(cls, 'h', cols, rows), 5.0, 0, 11) & ~wand
        a[rm] = (a[rm].astype(float) * np.array([0.78, 0.8, 0.86])).astype(np.uint8)
    treppe_m = np.zeros((Hp, Wp), bool)
    for (x0, x1, ry, r_) in lay['treppen']:
        if r_ == 's':
            k4.treppe(a, x0 * T, (x1 + 1) * T, ry * T - 1, 's', FRONT, 'berg47', tex['z'])
            treppe_m[ry * T:(ry + 1) * T + 8, x0 * T:(x1 + 1) * T] = True
        else:                                                        # Hof: Treppe fuehrt vom Suedrand in den Hof hinunter
            k4.treppe(a, x0 * T, (x1 + 1) * T, ry * T - 8, 'n', FRONT, 'berg47', tex['w'])
            treppe_m[ry * T - 10:(ry + 1) * T + 8, x0 * T:(x1 + 1) * T] = True
    verkohlen(a, lay, cols, rows, frame, wand)
    F_ = [np.array(H(c)) for c in k4.FELS['berg47']]
    for (x0, x1, ry, r_) in lay['treppen']:                          # breite Treppe: Licht/Schatten-Naht weich verteilen
        if r_ == 's':
            seg = a[ry * T:ry * T + FRONT + 4, x0 * T + 3:(x1 + 1) * T - 3]
            for (c_d, c_h) in ((F_[4], F_[5]), (F_[2], F_[3])):
                mk = np.all(seg == c_d, axis=-1)
                xx_ = np.arange(seg.shape[1])[None, :].repeat(seg.shape[0], 0)
                hell_ = mk & ((xx_ + np.arange(seg.shape[0])[:, None]) % 2 == 0) & (xx_ < seg.shape[1] * 0.85)
                seg[hell_] = c_h
    for tp in lay['teleporter']:
        k4.teleporter_zeichnen(a, tp['x'], tp['y'], tp['b'], tp['h'], frame)
    img = Image.fromarray(a).convert('RGBA')
    lvl = (hp + 1).astype(np.uint8)
    lvl[wand] = 9
    lvl[treppe_m] = 2                                                # Treppen begehbar (eigene Ebene, Uebergang)
    xm = np.zeros((Hp, Wp), bool)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain_basis.png'))
        np.save(os.path.join(KARTE, 'pixelhoehe.npy'), lvl)
        np.save(os.path.join(KARTE, 'wand.npy'), np.packbits(wand))
        np.save(os.path.join(KARTE, 'wasser.npy'), np.packbits(xm))
        np.save(os.path.join(KARTE, 'treppe.npy'), np.packbits(treppe_m))
    pf = os.path.join(OBJ, 'platzierung.json')
    if os.path.exists(pf):
        objs = sorted((o for o in json.load(open(pf)) if os.path.exists(os.path.join(OBJ, o['datei']))),
                      key=lambda o: o.get('sortier', o['y'] + o['fuss']))
        if objs:
            cache = {o['datei']: Image.open(os.path.join(OBJ, o['datei'])).convert('RGBA') for o in objs}
            ebenen = lvl.copy().astype(np.int16)
            k4.objekte_zeichnen(img, objs, cache, ~wand, frame, ebenen=ebenen)
            k4.animieren(img, objs, cache, frame or 0)
    if speichern and frame is None:
        img.save(os.path.join(KARTE, 'terrain.png'))
    print('Karte 51 %dx%d gebaut' % (cols, rows))
    return img


if __name__ == '__main__':
    bauen()
