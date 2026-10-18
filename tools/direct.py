"""파일 안 4bpp 타일 블록을 직접 고치는 글자 교체 -> trans/gfx_direct.json
spec(trans/direct_spec.json): [{"file","base"(타일0 오프셋),"tile"(시작 타일),"w","h"(픽셀,1D 객체 배치),
  "text","font","fg"(색인,생략시 최밝음 추정),"bg"(색인,생략시 최빈)}]"""
import json,collections,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from gpatch import text_mask,W
def run():
  spec=json.load(open(W/'trans/direct_spec.json',encoding='utf8'));out={}
  cache={}
  for sp in spec:
    f=sp['file'];d=cache.setdefault(f,bytearray(open(W/'gfx'/f,'rb').read()))
    if 'chunks' in sp:
      cw,ch=sp.get('cw',32),sp.get('ch',16);w=cw*len(sp['chunks']);h=ch;tw=cw//8
      def addr(x,y):
        o=sp['chunks'][x//cw];xx=x%cw
        t=o*(cw*ch//64)+(y//8)*tw+xx//8;return sp['base']+t*32+(y%8)*4+(xx%8)//2,(xx%8)&1
    else:
      w,h=sp['w'],sp['h'];tw=w//8
      def addr(x,y):
        t=sp['tile']+(y//8)*tw+x//8;return sp['base']+t*32+(y%8)*4+(x%8)//2,(x%8)&1
    def get(x,y):
      a,n=addr(x,y);return d[a]>>4 if n else d[a]&15
    def put(x,y,c):
      a,n=addr(x,y);d[a]=(d[a]&0x0f)|(c<<4) if n else (d[a]&0xf0)|c
    x0,y0,rw,rh=sp.get('rect',[0,0,w,h])
    cnt=collections.Counter(get(x,y) for y in range(y0,y0+rh) for x in range(x0,x0+rw))
    bg=sp.get('bg',cnt.most_common(1)[0][0]);fg=sp['fg']
    for y in range(y0,y0+rh):
      for x in range(x0,x0+rw):
        if get(x,y) in sp.get('erase',[fg]):put(x,y,bg)
    pts,tw_,th=text_mask(sp['text'],sp.get('font',11))
    ox=x0+(rw-tw_)//2+sp.get('dx',0);oy=y0+(rh-th)//2+sp.get('dy',0)
    S=set(pts)
    if 'outline' in sp:
      for (px,py) in pts:
        for dx,dy in((1,0),(0,1),(1,1)):
          q=(px+dx,py+dy)
          if q not in S and 0<=ox+q[0]<w and 0<=oy+q[1]<h:put(ox+q[0],oy+q[1],sp['outline'])
    for (px,py) in pts:
      if 0<=ox+px<w and 0<=oy+py<h:put(ox+px,oy+py,fg)
    tl=[o*(sp.get('cw',32)*sp.get('ch',16)//64)+i for o in sp['chunks'] for i in range(sp.get('cw',32)*sp.get('ch',16)//64)] if 'chunks' in sp else range(sp['tile'],sp['tile']+tw*(h//8))
    for t in tl:
      o=sp['base']+t*32;out[(f,o)]=bytes(d[o:o+32])
  json.dump([[n,o,b.hex()] for (n,o),b in sorted(out.items())],open(W/'trans/gfx_direct.json','w'),indent=0)
  print('직접 패치 타일',len(out))
if __name__=='__main__':run()
