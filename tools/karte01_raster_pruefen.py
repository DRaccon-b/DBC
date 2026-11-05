import json, os, math, sys
import numpy as np
from PIL import Image
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OBJ='assets/objekte/karte01'; T=16
objs=json.load(open(os.path.join(OBJ,'platzierung.json')))
def basis_bbox(o):
    p=os.path.join(OBJ,o['basis']+'.png')
    if not os.path.exists(p): p=os.path.join(OBJ,o['datei'])
    im=Image.open(p).convert('RGBA')
    if o.get('spiegeln'): im=im.transpose(Image.FLIP_LEFT_RIGHT)
    a=np.array(im.getchannel('A'))>0
    ys,xs=np.nonzero(a)
    off=2 if o['datei'].startswith('varianten/') else 0
    return xs.min()+off, ys.min(), xs.max()+off, ys.max()
schlecht=0; beisp=[]
for o in objs:
    x0,y0,x1,y1=basis_bbox(o)
    X0,Y0,X1,Y1=o['x']+x0,o['y']+y0,o['x']+x1,o['y']+y1
    noetig=math.ceil((x1-x0+1)/T)*math.ceil((y1-y0+1)/T)
    belegt=(X1//T-X0//T+1)*(Y1//T-Y0//T+1)
    if belegt>noetig:
        schlecht+=1
        if len(beisp)<8: beisp.append((o['basis'],x1-x0+1,y1-y0+1,noetig,belegt))
print(len(objs),'Objekte,',schlecht,'belegen mehr Kacheln als noetig'); print(beisp)
