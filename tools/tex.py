"""HBDF/MDLF 모델 텍스처(IMGO/PLTO) 읽기·쓰기. 형식: A3I5 8bpp 추정."""
import sys,struct,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import wdff
from PIL import Image
W=Path(__file__).resolve().parents[1]
def find(d):
  i=d.find(b'IMGO');p=d.find(b'PLTO')
  fmt,w,h=struct.unpack_from('<IHH',d,i+0x20)
  iend=i+8+struct.unpack_from('<I',d,i+4)[0]
  bpp={4:8,3:4,2:2,1:8,6:8}.get(fmt,8);imgsz=w*h*bpp//8
  ioff=iend-imgsz
  pend=p+8+struct.unpack_from('<I',d,p+4)[0]
  psz=struct.unpack_from('<I',d,p+0x20)[0];poff=pend-psz
  return dict(fmt=fmt,w=w,h=h,ioff=ioff,isz=imgsz,poff=poff,psz=psz)
def pal(d,t):return [((c&31)*255//31,(c>>5&31)*255//31,(c>>10&31)*255//31) for c in struct.unpack_from('<%dH'%(t['psz']//2),d,t['poff'])]
def render(name,out):
  b=open(W/'gfx'/name,'rb').read();it=wdff.items(b);d=it[0][4];t=find(d);P=pal(d,t)
  im=Image.new('RGB',(t['w'],t['h']),(255,0,255))
  for y in range(t['h']):
    for x in range(t['w']):
      v=d[t['ioff']+y*t['w']+x]
      if v<len(P):im.putpixel((x,y),P[v])
  im.save(out);return t
if __name__=='__main__':
  print(render(sys.argv[1],W/'shots'/'tex.png'))
