from PIL import Image
from collections import Counter
import json
im=Image.open('assets/vorlagen/karte01_original.png').convert('RGB')
pal={ # code: (name, reference colors, preview color)
 'G':('gras',[(70,148,56),(106,186,72),(154,210,58)],(90,170,60)),
 'F':('wald',[(44,104,40),(26,56,26),(10,44,24),(24,98,38),(60,104,22)],(30,90,35)),
 'R':('weg_dunkel',[(135,88,50),(132,80,40),(122,72,40),(84,46,24),(76,42,24)],(140,90,50)),
 'P':('weg_hell',[(210,174,122)],(215,180,125)),
 'C':('klippe',[(106,112,128),(152,158,170)],(110,115,130)),
 'W':('fluss_teich',[(24,66,134),(118,206,240)],(30,80,170)),
 'B':('bruecke',[(174,122,64)],(180,120,60)),
 'p':('teichsand',[(234,214,158)],(235,215,160)),
 'S':('strand',[(255,240,202)],(250,238,205)),
 's':('nasser_sand',[(210,186,126)],(200,175,120)),
 'h':('flachwasser',[(58,186,168)],(60,190,170)),
 'D':('meer',[(34,44,110),(10,10,18),(24,24,38),(14,14,26)],(30,40,110)),
}
def near(c):
    best=None
    for k,(n,refs,_) in pal.items():
        for r in refs:
            d=sum((a-b)**2 for a,b in zip(c,r))
            if best is None or d<best[0]: best=(d,k)
    return best[1]
W,H=im.size; cols,rows=W//16,H//16
grid=[]
for ty in range(rows):
    row=''
    for tx in range(cols):
        cell=im.crop((tx*16,ty*16,tx*16+16,ty*16+16))
        cnt=Counter(cell.getdata())
        # ignore object pixels: take most common colour that maps well
        row+=near(cnt.most_common(1)[0][0])
    grid.append(row)
open('terrain_grid.txt','w').write('\n'.join(grid))
json.dump({'tile_size':16,'cols':cols,'rows':rows,'legend':{k:v[0] for k,v in pal.items()},'grid':grid},open('terrain_grid.json','w'),indent=1)
prev=Image.new('RGB',(cols,rows))
for y,r in enumerate(grid):
    for x,ch in enumerate(r): prev.putpixel((x,y),pal[ch][2])
prev.resize((cols*8,rows*8),Image.NEAREST).save('terrain_preview.png')
print(Counter(''.join(grid)))
# Cleanup: einzelne Fehlklassifizierungen (Baumschatten als Wasser usw.) entfernen
g=[list(r) for r in grid]
for _ in range(2):
    new=[r[:] for r in g]
    for y in range(rows):
        for x in range(cols):
            ch=g[y][x]
            if ch not in 'WRBC': continue
            nb=[g[y+dy][x+dx] for dx,dy in((1,0),(-1,0),(0,1),(0,-1)) if 0<=x+dx<cols and 0<=y+dy<rows]
            if sum(n==ch for n in nb)<1 or (ch=='W' and sum(n in 'WB' for n in nb)<2 and 'B' not in nb and y>2):
                new[y][x]=Counter(n for n in nb if n!=ch).most_common(1)[0][0]
    g=new
# Grosse Baeume haben dunkle Umrisse -> wurden als Meer erkannt: oberhalb der Kueste zu Gras
for y in range(min(85,rows)):
    for x in range(cols):
        if g[y][x]=='D': g[y][x]='G'
for y in range(min(85,rows)):
    for x in range(cols):
        if g[y][x] in 'WR':
            nb=[g[y+dy][x+dx] for dx,dy in((1,0),(-1,0),(0,1),(0,-1)) if 0<=x+dx<cols and 0<=y+dy<rows]
            if sum(n in 'WB' for n in nb)==0 and g[y][x]=='W': g[y][x]='G'
            if g[y][x]=='R' and sum(n in 'RB' for n in nb)==0: g[y][x]='G'
grid=[''.join(r) for r in g]
open('terrain_grid.txt','w').write('\n'.join(grid))
json.dump({'tile_size':16,'cols':cols,'rows':rows,'legend':{k:v[0] for k,v in pal.items()},'grid':grid},open('terrain_grid.json','w'),indent=1)
prev=Image.new('RGB',(cols,rows))
for y,r in enumerate(grid):
    for x,ch in enumerate(r): prev.putpixel((x,y),pal[ch][2])
prev.resize((cols*8,rows*8),Image.NEAREST).save('terrain_preview.png')
