"""WDFF 타일 항목을 지정 폭(타일 수)으로 펼쳐 보기: python sheet.py file item cols [pal_item]"""
import sys
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).parent))
import wdff
W=Path(__file__).resolve().parents[1]
f,k,cols=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
b=open(W/'gfx'/f,'rb').read();it=wdff.items(b);d=it[k][4]
pk=int(sys.argv[4]) if len(sys.argv)>4 else max(j for j in range(k) if it[j][1]=='pal')
P=wdff.pal(it[pk][4]);n=len(d)//32;rows=(n+cols-1)//cols
im=Image.new('RGB',(cols*8,rows*8),(255,0,255))
for t in range(n):
  for y in range(8):
    for x in range(8):
      v=d[t*32+y*4+x//2];c=(v>>4) if x&1 else v&15
      if c:im.putpixel(((t%cols)*8+x,(t//cols)*8+y),P[c])
im.resize((im.width*2,im.height*2),Image.NEAREST).save(W/'shots/sheet.png');print(n,'tiles',im.size)
