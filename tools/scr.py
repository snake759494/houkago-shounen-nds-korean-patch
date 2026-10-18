"""스냅샷(레지스터·OAM·VRAM)에서 화면 픽셀별 타일 소유 정보를 계산한다.
  python scr.py SNAP            -> snaps/SNAP/objA.png, objB.png (객체 번호 표시), bgA*.png
"""
import sys,struct
from pathlib import Path
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parents[1]
SIZES={0:[(8,8),(16,16),(32,32),(64,64)],1:[(16,8),(32,8),(32,16),(64,32)],2:[(8,16),(8,32),(16,32),(32,64)]}
def self_transparent(t,vram):
  o,a,nib=t;v=vram[a]
  return ((v>>4 if nib else v&15) if nib is not None else v)==0
class Snap:
  def __init__(s,name):
    s.d=W/'snaps'/name
    s.f={n:open(s.d/(n+'.bin'),'rb').read() for n in ['ioA','ioB','oam','pal','objA','objB','bgA','bgB']}
  def pal(s,eng,objpal):
    base=(0x200 if objpal else 0)+(0x400 if eng=='B' else 0)
    raw=s.f['pal'][base:base+0x200]
    return [((c&31)*8,(c>>5&31)*8,(c>>10&31)*8) for c in struct.unpack('<256H',raw)]
  def objs(s,eng):
    io=s.f['io'+eng];disp=struct.unpack_from('<I',io,0)[0]
    one_d=disp>>4&1;bound=32<<((disp>>20)&3) if one_d else 32
    oam=s.f['oam'][(0x400 if eng=='B' else 0):][:0x400];out=[]
    for i in range(128):
      a0,a1,a2=struct.unpack_from('<3H',oam,i*8)
      aff=a0>>8&1
      if not aff and a0>>9&1:continue
      shape=a0>>14;size=a1>>14
      if shape==3:continue
      w,h=SIZES[shape][size];y=a0&0xff;x=a1&0x1ff
      if y>=192:y-=256
      if x>=256:x-=512
      c256=a0>>13&1
      out.append(dict(i=i,x=x,y=y,w=w,h=h,tile=a2&0x3ff,pal=a2>>12,prio=a2>>10&3,hf=(a1>>12&1) and not aff,vf=(a1>>13&1) and not aff,c256=c256,one_d=one_d,bound=bound,mode=a0>>10&3))
    return out
  def obj_pixel_addr(s,o,px,py):
    """객체 안 좌표 -> (VRAM 바이트 오프셋, 니블 여부)"""
    if o['hf']:px=o['w']-1-px
    if o['vf']:py=o['h']-1-py
    tx,ty,ix,iy=px//8,py//8,px%8,py%8
    bpp=8 if o['c256'] else 4;tb=bpp*8
    if o['one_d']:
      t=o['tile']*o['bound']+(ty*(o['w']//8)+tx)*tb
    else:
      t=o['tile']*32+(ty*32+tx*(2 if bpp==8 else 1))*32
    if bpp==4:return t+iy*4+ix//2,ix&1
    return t+iy*8+ix,None
  def own_map(s,eng,only=None):
    """화면 픽셀 -> (obj, addr, nib) 맨 위 불투명 객체"""
    vram=s.f['obj'+eng];own={}
    objs=sorted([o for o in s.objs(eng) if only is None or o['i'] in only],key=lambda o:(o['prio'],o['i']))
    for o in reversed(objs):
      if o['mode']==2:continue
      for py in range(o['h']):
        for px in range(o['w']):
          X,Y=o['x']+px,o['y']+py
          if not(0<=X<256 and 0<=Y<192):continue
          a,nib=s.obj_pixel_addr(o,px,py)
          if a>=len(vram):continue
          v=vram[a]
          c=(v>>4 if nib else v&15) if nib is not None else v
          if c or (X,Y) not in own or self_transparent(own[(X,Y)],vram):own[(X,Y)]=(o,a,nib)
    return own
  def render_objs(s,eng,scale=3):
    P=s.pal(eng,True);vram=s.f['obj'+eng]
    im=Image.new('RGB',(256,192),(255,0,255))
    own=s.own_map(eng)
    for (X,Y),(o,a,nib) in own.items():
      v=vram[a];c=(v>>4 if nib else v&15) if nib is not None else v
      im.putpixel((X,Y),P[o['pal']*16+c] if nib is not None else P[c])
    im=im.resize((256*scale,192*scale),Image.NEAREST);dr=ImageDraw.Draw(im)
    for o in s.objs(eng):
      if o['mode']==2:continue
      dr.rectangle([o['x']*scale,o['y']*scale,(o['x']+o['w'])*scale-1,(o['y']+o['h'])*scale-1],outline=(0,255,0))
      dr.text((o['x']*scale+1,o['y']*scale+1),str(o['i']),fill=(255,255,0))
    im.save(s.d/f'obj{eng}.png')
  # ---- BG(텍스트 모드, 스크롤 0 가정)
  def bgs(s,eng):
    io=s.f['io'+eng];disp=struct.unpack_from('<I',io,0)[0];out=[]
    for n in range(4):
      if not disp>>(8+n)&1:continue
      cnt=struct.unpack_from('<H',io,8+2*n)[0]
      cb=(cnt>>2&15)*0x4000;sb=(cnt>>8&31)*0x800
      if eng=='A':cb+=(disp>>24&7)*0x10000;sb+=(disp>>27&7)*0x10000
      out.append(dict(n=n,prio=cnt&3,cb=cb,sb=sb,c256=cnt>>7&1,size=cnt>>14))
    return out
  def bg_pixel(s,eng,b,X,Y):
    vram=s.f['bg'+eng];mw=64 if b['size'] in(1,3) else 32
    tx,ty=X//8,Y//8;blk=(ty//32)*(2 if mw==64 else 1)+(tx//32)
    e=struct.unpack_from('<H',vram,b['sb']+blk*0x800+((ty%32)*32+tx%32)*2)[0]
    t=e&0x3ff;hf=e>>10&1;vf=e>>11&1;pn=e>>12;ix,iy=X%8,Y%8
    if hf:ix=7-ix
    if vf:iy=7-iy
    if b['c256']:return b['cb']+t*64+iy*8+ix,None,pn,e
    return b['cb']+t*32+iy*4+ix//2,ix&1,pn,e
  def render_bg(s,eng,b):
    P=s.pal(eng,False);vram=s.f['bg'+eng];im=Image.new('RGB',(256,192))
    for Y in range(192):
      for X in range(256):
        a,nib,pn,_=s.bg_pixel(s and eng,b,X,Y) if False else s.bg_pixel(eng,b,X,Y)
        if a>=len(vram):continue
        v=vram[a];c=(v>>4 if nib else v&15) if nib is not None else v
        im.putpixel((X,Y),P[pn*16+c] if nib is not None else P[c])
    im.save(s.d/f'bg{eng}{b["n"]}.png')
if __name__=='__main__':
  s=Snap(sys.argv[1])
  for e in 'AB':
    s.render_objs(e)
    for b in s.bgs(e):s.render_bg(e,b)
  print({e:[(b['n'],b['prio']) for b in s.bgs(e)] for e in 'AB'})
