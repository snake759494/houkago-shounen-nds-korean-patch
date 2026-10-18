"""스프라이트 묶음 객체(32x16 등)의 글자 교체 -> trans/gfx_chunk.json
spec trans/chunk_spec.json: [{"file","item","chunks":[..],"cw":32,"ch":16,"rect":[x,y,w,h],"text","font","ink":"dark|light|sat","pal":n(선택)}]"""
import sys,json,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import wdff
from gpatch import text_mask,W
spec=json.load(open(W/'trans/chunk_spec.json',encoding='utf8'));cache={};out={}
for sp in spec:
  f=sp['file'];b=cache.setdefault(f,bytearray(open(W/'gfx'/f,'rb').read()))
  it=wdff.items(bytes(b));k=sp['item'];base=it[k][2]+4
  P=wdff.pal([x for x in it[:k] if x[1]=='pal'][-1][4]);pn=sp.get('pal',0)
  cw,ch=sp.get('cw',32),sp.get('ch',16);per=cw*ch//64;tw=cw//8
  def addr(x,y):
    o=sp['chunks'][x//cw];xx=x%cw;t=o*per+(y//8)*tw+xx//8;return base+t*32+(y%8)*4+(xx%8)//2,(xx%8)&1
  def get(x,y):a,n=addr(x,y);return b[a]>>4 if n else b[a]&15
  def put(x,y,c):
    a,n=addr(x,y);b[a]=(b[a]&0x0f)|(c<<4) if n else (b[a]&0xf0)|c
  x0,y0,rw,rh=sp['rect']
  cnt=collections.Counter(get(x,y) for y in range(y0,y0+rh) for x in range(x0,x0+rw))
  bg=sp.get('bg',cnt.most_common(1)[0][0])
  L=lambda c:sum(P[pn*16+c]) if pn*16+c<len(P) else 0
  cols=[c for c in cnt if c!=bg and c]
  mode=sp.get('ink','dark')
  ink=sp.get('fg',(min(cols,key=L) if mode=='dark' else max(cols,key=L)) if cols else 1)
  for y in range(y0,y0+rh):
    for x in range(x0,x0+rw):put(x,y,bg)
  pts,tw_,th=text_mask(sp['text'],sp.get('font',11))
  ox=x0+(rw-tw_)//2;oy=y0+(rh-th)//2
  for px,py in pts:
    if 0<=ox+px<cw*len(sp['chunks']) and 0<=oy+py<ch:put(ox+px,oy+py,ink)
  for o in sp['chunks']:
    for t in range(per):
      s=base+(o*per+t)*32;out[(f,s)]=bytes(b[s:s+32])
json.dump([[n,o,v.hex()] for (n,o),v in sorted(out.items())],open(W/'trans/gfx_chunk.json','w'))
print('청크 타일',len(out))
