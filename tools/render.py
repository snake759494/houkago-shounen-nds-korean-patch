"""WDFF 파일의 BG(맵 합성)와 스프라이트 타일을 PNG로 렌더링."""
import sys,struct
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent))
import wdff
W=Path(__file__).resolve().parents[1]
def tiles4(data):
  n=len(data)//32;T=[]
  for t in range(n):
    px=[]
    for y in range(8):
      row=[]
      for x in range(4):
        v=data[t*32+y*4+x];row+=[v&15,v>>4]
      px.append(row)
    T.append(px)
  return T
def render_file(name,out=None):
  b=open(W/'gfx'/name,'rb').read();it=wdff.items(b);imgs=[]
  i=0
  while i<len(it):
    k,kind,a,h,d=it[i]
    if kind=='map' and i+2<len(it) and it[i+1][1]=='pal' and it[i+2][1]=='tile':
      mw=(h>>16)&0xff;mh=h>>24;P=wdff.pal(it[i+1][4]);T=tiles4(it[i+2][4])
      im=Image.new('RGB',(mw*8,mh*8))
      for my in range(mh):
        for mx in range(mw):
          e=struct.unpack_from('<H',d,(my*mw+mx)*2)[0];ti=e&0x3ff;hf=e>>10&1;vf=e>>11&1;pn=e>>12
          if ti>=len(T):continue
          t=T[ti]
          for y in range(8):
            for x in range(8):
              c=t[7-y if vf else y][7-x if hf else x]
              ci=pn*16+c
              im.putpixel((mx*8+x,my*8+y),P[ci] if ci<len(P) and c else (40,0,40))
      imgs.append((f'{k}bg',im));i+=3;continue
    if kind=='tile':
      P=None
      for j in range(i-1,-1,-1):
        if it[j][1]=='pal':P=wdff.pal(it[j][4]);break
      T=tiles4(d);cols=16;rows=(len(T)+cols-1)//cols
      im=Image.new('RGB',(cols*8,max(rows,1)*8),(40,0,40))
      for n,t in enumerate(T):
        for y in range(8):
          for x in range(8):
            c=t[y][x]
            if c:im.putpixel(((n%cols)*8+x,(n//cols)*8+y),P[c] if P and c<len(P) else (c*16,)*3)
      imgs.append((f'{k}sp',im))
    i+=1
  if not imgs:return
  Wd=sum(im.width for _,im in imgs)+4*len(imgs);H=max(im.height for _,im in imgs)
  sheet=Image.new('RGB',(Wd,H),(255,255,255));x=0
  for _,im in imgs:sheet.paste(im,(x,0));x+=im.width+4
  sheet.save(out or W/'gfxview'/(name[:-4]+'.png'))
if __name__=='__main__':
  for n in sys.argv[1:]:render_file(n)
