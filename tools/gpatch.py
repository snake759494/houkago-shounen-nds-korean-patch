"""그래픽 글자 교체: trans/gfx_spec.json -> trans/gfx_patches.json
spec 항목: {"snap":"name","eng":"B","layer":"obj"|"bg1".., "rect":[x,y,w,h], "text":"이름", "font":11|9,
            "fg":색인(선택), "bg":색인(선택), "outline":색인(선택), "align":"c"|"l", "dy":0}
원본 그래픽 빌드에서 만든 스냅샷을 사용한다(VRAM 원본 타일 -> 원본 파일 위치 매칭)."""
import sys,json,glob,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from scr import Snap,W
import wdff
from PIL import Image
def bdf(path):
  g={};cur=None;lines=open(path,encoding='utf8').read().splitlines();i=0
  while i<len(lines):
    l=lines[i]
    if l.startswith('ENCODING'):cur=int(l.split()[1])
    elif l.startswith('BBX'):bbx=list(map(int,l.split()[1:]))
    elif l.startswith('DWIDTH'):dw=int(l.split()[1])
    elif l=='BITMAP':
      rows=[];i+=1
      while lines[i]!='ENDCHAR':rows.append(lines[i]);i+=1
      g[cur]=(bbx,dw,rows)
    i+=1
  return g
FONTS={11:(bdf(W/'fonts/Galmuri11.bdf'),11),9:(bdf(W/'fonts/Galmuri9.bdf'),9)}
def text_mask(text,size):
  g,asc=FONTS[size];pts=[];x=0
  for ch in text:
    if ch==' ':x+=size//2;continue
    (w,h,xo,yo),dw,rows=g[ord(ch)]
    top=asc-h-yo
    for r,row in enumerate(rows):
      v=int(row,16);nb=len(row)*4
      for c in range(w):
        if v>>(nb-1-c)&1:pts.append((x+xo+c,top+r))
    x+=dw
  W_=max([p[0] for p in pts]+[0])+1;H=max([p[1] for p in pts]+[0])+1
  return pts,W_,H
_files=None
def files():
  global _files
  if _files is None:_files={Path(f).name:open(f,'rb').read() for f in glob.glob(str(W/'gfx/*.dec'))}
  return _files
def locate(block):
  hits=[(n,d.find(block)) for n,d in files().items() if d.find(block)>=0]
  return hits
def apply_spec(spec):
  patches={}  # (file,off)->bytes
  snaps={}
  for sp in spec:
    s=snaps.setdefault(sp['snap'],Snap(sp['snap']));eng=sp['eng']
    layer=sp.get('layer','obj')
    vname=('obj' if layer=='obj' else 'bg')+eng
    vram=bytearray(s.f[vname]);orig=bytes(vram)
    x0,y0,w,h=sp['rect']
    # 픽셀 소유
    own={}
    if layer=='obj':
      om=s.own_map(eng,only=sp.get('objs'))
      for y in range(y0,y0+h):
        for x in range(x0,x0+w):
          if (x,y) in om:o,a,nib=om[(x,y)];own[(x,y)]=(a,nib,o)
    else:
      b=[b for b in s.bgs(eng) if b['n']==int(layer[2:])][0]
      for y in range(y0,y0+h):
        for x in range(x0,x0+w):
          a,nib,pn,e=s.bg_pixel(eng,b,x,y);own[(x,y)]=(a,nib,None)
    def get(a,nib):
      v=vram[a];return (v>>4 if nib else v&15) if nib is not None else v
    def put(a,nib,c):
      if nib is None:vram[a]=c
      elif nib:vram[a]=(vram[a]&0x0f)|(c<<4)
      else:vram[a]=(vram[a]&0xf0)|c
    cnt=collections.Counter(get(a,n) for (a,n,o) in own.values())
    bgc=sp.get('bg',cnt.most_common(1)[0][0])
    rest=[c for c,_ in cnt.most_common() if c!=bgc]
    P=s.pal(eng,layer=='obj')
    pc=collections.Counter(v[2]['pal'] for v in own.values() if v[2] is not None)
    pn=pc.most_common(1)[0][0] if pc else 0
    def lum(c):
      r,g,b=P[pn*16+c] if c<16 else P[c];return r*3+g*6+b
    fgc=sp.get('fg',(min(rest,key=lum) if sp.get('fgdark') else max(rest,key=lambda c:abs(lum(c)-lum(bgc)))) if rest else 1)
    if sp.get('style')=='outline':
      nz=list(range(1,16))
      bgc=0;fgc=sp.get('fg',min(nz,key=lum));sp=dict(sp);sp.setdefault('outline',max(nz,key=lum))
    def pick(o,mode):
      q=o['pal'] if o else pn
      L=lambda c:(lambda r,g,b:r*3+g*6+b)(*P[q*16+c])
      return (min if mode=='dark' else max)(range(1,16),key=L)
    for (a,n,o) in own.values():put(a,n,bgc)
    if layer=='obj' and sp.get('objs'):
      for o in s.objs(eng):
        if o['i'] not in sp['objs']:continue
        for py in range(o['h']):
          for px in range(o['w']):
            X,Y=o['x']+px,o['y']+py
            if x0<=X<x0+w and y0<=Y<y0+h:
              a,nib=s.obj_pixel_addr(o,px,py);put(a,nib,0)
    pts,tw,th=text_mask(sp['text'],sp.get('font',11))
    ox=x0+((w-tw)//2 if sp.get('align','c')=='c' else 0)+sp.get('dx',0);oy=y0+(h-th)//2+sp.get('dy',0)
    ol=sp.get('outline')
    if ol is not None:
      S=set(pts)
      for (px,py) in pts:
        for dx in(-1,0,1):
          for dy in(-1,0,1):
            q=(px+dx,py+dy)
            if q not in S and (ox+q[0],oy+q[1]) in own:a,n,o=own[(ox+q[0],oy+q[1])];put(a,n,pick(o,'light') if sp.get('style')=='outline' else ol)
    miss=0
    for (px,py) in pts:
      k=(ox+px,oy+py)
      if k in own:a,n,o=own[k];put(a,n,pick(o,'dark') if sp.get('style')=='outline' else fgc)
      else:miss+=1
    if miss:print('경고: 영역 밖 픽셀',miss,sp['text'])
    # 바뀐 타일 -> 파일 위치
    tb=32
    changed=sorted({(a//tb)*tb for (a,n,o) in own.values() if vram[(a//tb)*tb:(a//tb)*tb+tb]!=orig[(a//tb)*tb:(a//tb)*tb+tb]})
    # 객체/BG 전체 블록으로 위치 결정
    objbase={}
    if layer=='obj':
      for (a,n,o) in own.values():
        if o is None:continue
        bpp=8 if o['c256'] else 4
        st=o['tile']*o['bound'];ln=o['w']*o['h']*bpp//8
        objbase[(st,ln)]=1
    blockmap={}
    for (st,ln) in objbase:
      blk=orig[st:st+ln];hits=locate(blk) if blk.strip(b'\0') else []
      if not hits and blk.strip(b'\0'):
        lead=len(blk)-len(blk.lstrip(b'\0'));core=blk.strip(b'\0')
        hh=locate(core)
        if hh:hits=[(n,i-lead) for n,i in hh]
      if hits:
        for t in range(st,st+ln,tb):blockmap[t]=(hits[0][0],hits[0][1]+(t-st))
    for t in changed:
      if t in blockmap:
        n,off=blockmap[t];patches[(n,off)]=bytes(vram[t:t+tb])
        continue
      blk=orig[t:t+tb];hits=locate(blk)
      # 주변 블록으로 모호성 해소
      span=tb
      while len(hits)>1 and span<4096:
        span*=2;lo=max(0,t-span//2);big=orig[lo:t+span//2]
        hh=[(n,i+(t-lo)) for n,i in locate(big)] if big.strip(b'\0') else []
        if hh:hits=hh
        else:break
      if not hits:print('위치 못 찾음',sp['text'],hex(t));continue
      n,off=hits[0]
      patches[(n,off)]=bytes(vram[t:t+tb])
    s.f[vname]=bytes(vram)
  for name,sn in snaps.items():
    for e in 'AB':
      sn.render_objs(e,scale=2)
      (sn.d/f'obj{e}.png').rename(sn.d/f'prev{e}.png') if not (sn.d/f'prev{e}.png').exists() else ((sn.d/f'prev{e}.png').unlink(),(sn.d/f'obj{e}.png').rename(sn.d/f'prev{e}.png'))
  return patches
if __name__=='__main__':
  spec=json.load(open(W/'trans/gfx_spec.json',encoding='utf8'))
  old={}
  q=W/'trans/gfx_patches_v100.json'
  if q.exists():old={(n,o):bytes.fromhex(h) for n,o,h in json.load(open(q))}
  avail=[sp for sp in spec if (W/'snaps'/sp['snap']/'ioA.bin').exists()]
  print('스냅샷 있는 사양',len(avail),'/',len(spec))
  P=old;P.update(apply_spec(avail))
  import wdff
  bases={}
  for n in {n for n,o in P}:
    it=wdff.items(files()[n]);bases[n]=[(a+4,a+4+len(d)) for k,kind,a,h,d in it if kind=='tile']
  bad=[(n,o) for (n,o) in P if not any(s0<=o<e0 and (o-s0)%32==0 for s0,e0 in bases[n])]
  for k in bad:P.pop(k)
  print('정렬 어긋난 패치 제거',len(bad),bad[:5])
  json.dump([[n,o,b.hex()] for (n,o),b in sorted(P.items())],open(W/'trans/gfx_patches.json','w'),indent=0)
  print('패치 타일',len(P))
