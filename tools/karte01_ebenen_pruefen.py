"""Prueft die Spiel-Ebenen von Karte 01: Felsspitzen ueber begehbarem Boden, Objekte auf Felsen,
Sperre breiter Objekte, Fuesse auf Wasser/Klippen.  python3 tools/karte01_ebenen_pruefen.py"""
import json, os, sys
import numpy as np
from PIL import Image
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
T=16
k=json.load(open('maps/karte01/ebenen/kollision.json'))['raster']
fels=json.load(open('maps/karte01/felsen.json'))
objs=json.load(open('assets/objekte/karte01/platzierung.json'))
g=json.load(open('maps/karte01/terrain_grid.json'))['grid']
print('Felsen:', len(fels), 'davon herausragend', sum(1 for f in fels if f[5]))
# 1 Spitzen ueber begehbaren Kacheln, die NICHT als verdeckt (3) markiert sind
H_,W_=len(k)*T,len(k[0])*T
sp=np.unpackbits(np.load('maps/karte01/felsspitzen.npy'))[:H_*W_].reshape(H_,W_)
n1=[]
for ty in range(len(k)):
    for tx in range(len(k[0])):
        if k[ty][tx]=='1' and sp[ty*T:(ty+1)*T,tx*T:(tx+1)*T].sum()>=12: n1.append((tx,ty))
print('1) Felsspitzen ueber begehbaren, nicht verdeckten Kacheln:', n1)
# 2 Objekte ueber Felsen
n2=[]
for o in objs:
    w,h=Image.open('assets/objekte/karte01/'+o['datei']).size
    for (x0,y0,x1,y1,wl,raus) in fels:
        if o['x']<x1 and o['x']+w>x0 and o['y']<y1 and o['y']+h>y0:
            n2.append((o['basis'],o['kachel'])); break
print('2) Objekte ueber Felsen:', len(n2), n2[:12])
# 3 breite Objekte mit duenner Sperre
n3=[]
for o in objs:
    a=np.array(Image.open('assets/objekte/karte01/'+o['datei']).getchannel('A'))>=128
    z=np.nonzero(a.any(1))[0]; zu=z.max()
    bw=a[max(0,zu-3):zu+1].any(0).sum()
    if bw>40 and o.get('ebene',1)==1: n3.append((o['basis'],o['kachel'],int(bw)))
print('3) breite Objekte (Fussbreite>40px):', n3)
for (b,(tx,ty),bw) in n3:
    print('   Sperre um', b, [k[ty-dy][tx-1:tx+2] for dy in range(0,3)])
# 4 Fuesse auf Wasser/Klippe
n4=[]
for o in objs:
    if o.get('ebene',1)==0: continue
    tx,ty=o['kachel']
    if g[ty][tx] in 'WDhC' : n4.append((o['basis'],o['kachel'],g[ty][tx]))
print('4) Fuss auf Wasser/Klippe:', n4[:20], len(n4))
