"""모델 텍스처 픽셀 편집: load/save (8bpp 색인)."""
import sys,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import wdff
W=Path(__file__).resolve().parents[1]
def textures(b):
  out=[]
  for k,kind,a,h,d in wdff.items(b):
    if kind!='other':continue
    pos=0
    while True:
      i=d.find(b'IMGO',pos)
      if i<0:break
      pos=i+4
      try:
       fmt,w,hh=struct.unpack_from('<IHH',d,i+0x20)
       iend=i+8+struct.unpack_from('<I',d,i+4)[0];bpp={4:8,3:4,2:2}.get(fmt,8)
       ioff=iend-w*hh*bpp//8
       p=d.find(b'PLTO',i);pend=p+8+struct.unpack_from('<I',d,p+4)[0];psz=struct.unpack_from('<I',d,p+0x20)[0];poff=pend-psz
       P=[((c&31)*8,(c>>5&31)*8,(c>>10&31)*8) for c in struct.unpack_from('<%dH'%(psz//2),d,poff)]
       out.append(dict(abs=a+4+ioff,w=w,h=hh,bpp=bpp,P=P,fmt=fmt))
      except Exception:pass
  return out
