"""WDFF 안의 BG(맵+팔레트+4bpp 타일)를 색인 픽셀로 풀고, 글자 교체 후 타일을 다시 만든다.
spec(trans/bg_spec.json): [{"file":..., "map":k, "clear":[x,y,w,h], "lines":[{"y":..,"text":..,"font":11,"x":"c"}],
  "fg":색인, "fg2":강조색인, "bgc":색인}]  강조는 텍스트 안 {...}.
결과: gfx_bg/<file> (교체된 body) — build가 사용."""
import sys,json,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import wdff
from gpatch import FONTS
W=Path(__file__).resolve().parents[1]
def load_bg(b,k):
  it=wdff.items(b);_,_,_,h,m=it[k];P=it[k+1][4];T=it[k+2][4]
  mw=(h>>16)&0xff;mh=h>>24
  px=[[(0,0)]*(mw*8) for _ in range(mh*8)]
  for my in range(mh):
    for mx in range(mw):
      e=struct.unpack_from('<H',m,(my*mw+mx)*2)[0];ti=e&0x3ff;hf=e>>10&1;vf=e>>11&1;pn=e>>12
      for y in range(8):
        for x in range(8):
          sy=7-y if vf else y;sx=7-x if hf else x
          o=ti*32+sy*4+sx//2
          v=T[o] if o<len(T) else 0;c=(v>>4) if sx&1 else v&15
          px[my*8+y][mx*8+x]=(pn,c)
  return px,mw,mh,it
def store_bg(b,k,px,mw,mh,it):
  tiles=[];index={};mp=bytearray()
  def key(t):return bytes(t)
  for my in range(mh):
    for mx in range(mw):
      pn=px[my*8][mx*8][0]
      t=bytearray(32)
      for y in range(8):
        for x in range(8):
          p,c=px[my*8+y][mx*8+x]
          t[y*4+x//2]|=(c<<4) if x&1 else c
      kk=key(t)
      found=None
      # 원본처럼 뒤집기 재사용은 하지 않음(단순화), 동일 타일만 공유
      if kk not in index:index[kk]=len(tiles);tiles.append(kk)
      mp+=struct.pack('<H',(index[kk]&0x3ff)|(pn<<12))
  assert len(tiles)<=1024,len(tiles)
  td=b''.join(tiles)
  mraw=struct.pack('<I',it[k][3])+bytes(mp)
  traw=struct.pack('<I',len(td)*8)+td
  return wdff.rebuild(b,{k:mraw,k+2:traw})
def nearest(P,pn,rgb):
  best=None
  for c in range(1,16):
    r,g,b=P[pn*16+c] if pn*16+c<len(P) else (0,0,0)
    d=(r-rgb[0])**2+(g-rgb[1])**2+(b-rgb[2])**2
    if best is None or d<best[0]:best=(d,c)
  return best
def draw(px,text,font,x,y,fg,fg2,P=None):
  g,asc=FONTS[font];cx=0;hi=False;pts=[]
  for ch in text:
    if ch=='{':hi=True;continue
    if ch=='}':hi=False;continue
    if ch==' ':cx+=font//2+1;continue
    (w,h,xo,yo),dw,rows=g[ord(ch)];top=asc-h-yo
    for r,row in enumerate(rows):
      v=int(row,16);nb=len(row)*4
      for c in range(w):
        if v>>(nb-1-c)&1:pts.append((cx+xo+c,top+r,hi))
    cx+=dw
  width=cx
  if x=='c':x=(len(px[0])-width)//2 if len(px[0])<=256 else (256-width)//2
  hitiles=set()
  for (a,bb,hi) in pts:
    X,Y=x+a,y+bb
    if hi:hitiles.add((X//8,Y//8))
  # 강조 타일은 강조색이 가장 잘 맞는 팔레트로 교체
  npal=len(P)//16
  for (tx,ty) in hitiles:
    best=min(range(npal),key=lambda q:nearest(P,q,fg2)[0]*4+nearest(P,q,(0,0,0))[0])
    for yy in range(ty*8,ty*8+8):
      for xx in range(tx*8,tx*8+8):
        p,c=px[yy][xx];rgb=P[p*16+c];px[yy][xx]=(best,nearest(P,best,rgb)[1])
  for (a,bb,hi) in pts:
    X,Y=x+a,y+bb
    p,_=px[Y][X];px[Y][X]=(p,nearest(P,p,fg2 if hi else fg)[1])
def run():
  spec=json.load(open(W/'trans/bg_spec.json',encoding='utf8'))
  out=W/'gfx_bg';out.mkdir(exist_ok=True)
  cur={}
  for sp in spec:
    f=sp['file']
    if f not in cur:
      bb=bytearray(open(W/'gfx'/f,'rb').read())
      for name in ('gfx_patches.json','gfx_direct.json','gfx_tex.json','gfx_stamp.json','gfx_chunk.json'):
        q=W/'trans'/name
        if q.exists():
          for n,o,h in json.load(open(q)):
            if n==f:bb[o:o+len(h)//2]=bytes.fromhex(h)
      cur[f]=bytes(bb)
    if 'maplabel' in sp:
      import maplabel
      for L in sp['maplabel']:
        cur[f]=maplabel.apply(cur[f],sp['map'],L['rect'],L['text'],L.get('size',12),L.get('keep'),trect=L.get('trect'),ink_rgb=tuple(L['ink']) if 'ink' in L else None,halo_on=L.get('halo',True))
      continue
    if 'logo' in sp:
      import logo
      L=sp['logo'];cur[f]=logo.apply(cur[f],sp['map'],*L['xy'],*L['cell'],L['size'],L.get('keep'),tuple(L['frame']),tuple(L['fill']),tuple(L['outline']),L['clear'],tuple(L['clear_rgb']) if 'clear_rgb' in L else None)
      continue
    b=cur[f];px,mw,mh,it=load_bg(b,sp['map'])
    x0,y0,w,h=sp['clear']
    P=wdff.pal(it[sp['map']+1][4])
    bgrgb=tuple(sp.get('bgrgb',(0,0,0)))
    th=sp.get('erase_bright')
    if 'bgsrc' in sp:
      sb=open(W/'gfx'/sp['bgsrc']['file'],'rb').read();spx,_,_,sit=load_bg(sb,sp['bgsrc']['map']);SP=wdff.pal(sit[sp['bgsrc']['map']+1][4])
      for y in range(y0,y0+h):
        for x in range(x0,x0+w):
          q,cc=spx[y][x];p=px[y][x][0];px[y][x]=(p,nearest(P,p,SP[q*16+cc])[1])
      th=-1;sp=dict(sp);sp['keep_rgb']=None
      w=0
    for y in range(y0,y0+h):
      for x in range(x0,x0+w):
        p,c=px[y][x]
        if th is not None and sum(P[p*16+c])<th:continue
        if sp.get('keep_rgb') and list(P[p*16+c]) in sp['keep_rgb']:continue
        px[y][x]=(p,nearest(P,p,bgrgb)[1])
    for ln in sp['lines']:
      draw(px,ln['text'],ln.get('font',11),ln.get('x','c'),ln['y'],tuple(sp['fg']),tuple(sp.get('fg2',sp['fg'])),P)
    cur[f]=store_bg(b,sp['map'],px,mw,mh,it)
  for f,b in cur.items():open(out/f,'wb').write(b)
  print('BG 파일',len(cur))
if __name__=='__main__':run()
