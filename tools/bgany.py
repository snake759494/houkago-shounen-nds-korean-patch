"""임의 맵/팔레트/타일 항목 조합 렌더·편집"""
import sys,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import wdff
def load(b,km,kp,kt):
  it=wdff.items(b);_,_,_,h,m=it[km];P=wdff.pal(it[kp][4]);T=it[kt][4]
  mw=(h>>16)&0xff;mh=h>>24;px=[[(0,0)]*(mw*8) for _ in range(mh*8)]
  for my in range(mh):
    for mx in range(mw):
      e=struct.unpack_from('<H',m,(my*mw+mx)*2)[0];ti=e&0x3ff;hf=e>>10&1;vf=e>>11&1;pn=e>>12
      for y in range(8):
        for x in range(8):
          sy=7-y if vf else y;sx=7-x if hf else x;o=ti*32+sy*4+sx//2
          v=T[o] if o<len(T) else 0;px[my*8+y][mx*8+x]=(pn,(v>>4) if sx&1 else v&15)
  return px,mw,mh,P
def image(px,P):
  from PIL import Image
  im=Image.new('RGB',(len(px[0]),len(px)),(255,0,255))
  for y,row in enumerate(px):
    for x,(p,c) in enumerate(row):
      if c and p*16+c<len(P):im.putpixel((x,y),P[p*16+c])
  return im
