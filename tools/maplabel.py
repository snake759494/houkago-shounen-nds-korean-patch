"""지도 손글씨 교체: 사각형 안 잉크(파랑/빨강) 픽셀을 주변 배경색으로 메우고 같은 잉크색으로 한글을 쓴다."""
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).parent))
import wdff,bgedit,mapink
W=Path(__file__).resolve().parents[1]
FONT=W.parent/'NanumSquareNeo-dEb.ttf'
def apply(b,k,rect,text,size=12,keep=None,ink_rgb=None,lh=None,trect=None,halo_on=True):
  px,mw,mh,it=bgedit.load_bg(b,k);P=wdff.pal(it[k+1][4])
  x0,y0,x1,y1=rect
  col=lambda x,y:P[px[y][x][0]*16+px[y][x][1]]
  inside=lambda x,y:x0<=x<=x1 and y0<=y<=y1 and not(keep and keep[0]<=x<=keep[2] and keep[1]<=y<=keep[3])
  ink=[(x,y) for y in range(y0,y1+1) for x in range(x0,x1+1) if inside(x,y) and mapink.ink(col(x,y))]
  def lt(c):
    r,g,b=c
    return min(c)>226 or (min(c)>195 and max(c)-min(c)<14) or (b>r+12 and b>=g and min(c)>150) or (r>g+20 and r>b+8 and min(c)>140)
  halo=[(x,y) for y in range(y0,y1+1) for x in range(x0,x1+1) if halo_on and inside(x,y) and (lt(col(x,y)) if halo_on is True else (col(x,y)[0]>col(x,y)[1]+20 and col(x,y)[0]>col(x,y)[2]+8))]
  if ink_rgb is None:
    n=len(ink) or 1
    ink_rgb=tuple(sum(col(x,y)[i] for x,y in ink)//n for i in range(3))
  # 메우기: 바깥에서 안쪽으로 이웃 평균
  todo=set(ink)|set(halo);rgb={}
  bad=lambda c:mapink.ink(c) or lt(c)
  for y in range(max(0,y0-3),min(192,y1+4)):
    for x in range(max(0,x0-3),min(256,x1+4)):
      if (x,y) not in todo:rgb[(x,y)]=col(x,y)
  while todo:
    nxt=set()
    for (x,y) in todo:
      nb=[rgb[(x+dx,y+dy)] for dx in(-1,0,1) for dy in(-1,0,1) if (x+dx,y+dy) in rgb and not bad(rgb[(x+dx,y+dy)])]
      if nb:rgb[(x,y)]=tuple(sum(c[i] for c in nb)//len(nb) for i in range(3))
      else:nxt.add((x,y))
    if nxt==todo:
      for p in nxt:rgb[p]=(220,220,180)
      break
    todo=nxt
  tgt={}
  for (x,y) in set(ink)|set(halo):tgt[(x,y)]=rgb[(x,y)]
  # 글자
  font=ImageFont.truetype(str(FONT),size)
  lines=text.split('\n');lh=lh or size+1
  if trect:x0,y0,x1,y1=trect
  im=Image.new('L',(x1-x0+40,lh*len(lines)+8),0);d=ImageDraw.Draw(im)
  widths=[d.textbbox((0,0),ln,font=font)[2] for ln in lines]
  for i,ln in enumerate(lines):d.text((20+(x1-x0+1-widths[i])//2,2+i*lh),ln,255,font=font)
  im=im.point(lambda v:255 if v>100 else 0)
  oy=y0+((y1-y0+1)-lh*len(lines))//2-2
  for y in range(im.height):
    for x in range(im.width):
      if im.getpixel((x,y)):
        X,Y=x0-20+x,oy+y
        if 0<=X<256 and 0<=Y<192:tgt[(X,Y)]=ink_rgb
  # 타일별 최적 팔레트 재선택
  npal=len(P)//16
  for tx,ty in {(x//8,y//8) for (x,y) in tgt}:
    cols=[]
    for yy in range(ty*8,ty*8+8):
      for xx in range(tx*8,tx*8+8):
        cols.append(((xx,yy),tgt.get((xx,yy),P[px[yy][xx][0]*16+px[yy][xx][1]])))
    best=min(range(npal),key=lambda q:sum(bgedit.nearest(P,q,c)[0] for _,c in cols))
    for (xx,yy),c in cols:px[yy][xx]=(best,bgedit.nearest(P,best,c)[1])
  return bgedit.store_bg(b,k,px,mw,mh,it)
