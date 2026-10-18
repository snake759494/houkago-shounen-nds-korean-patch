"""타이틀 로고 '방과후소년' 세로 렌더(원본 격자·흰 글자·짙은 외곽선 형식)."""
import sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageFilter
W=Path(__file__).resolve().parents[1]
def render(fontfile,cell_w=38,cell_h=37,n=5,size=34,text='방과후소년'):
  font=ImageFont.truetype(str(fontfile),size)
  H=cell_h*n+2;Wd=cell_w+2
  fill=Image.new('L',(Wd,H),0);d=ImageDraw.Draw(fill)
  for i,ch in enumerate(text):
    bb=d.textbbox((0,0),ch,font=font);tw=bb[2]-bb[0];th=bb[3]-bb[1]
    d.text((1+(cell_w-tw)//2-bb[0],1+i*cell_h+(cell_h-th)//2-bb[1]),ch,255,font=font)
  fill=fill.point(lambda v:255 if v>110 else 0)
  outl=fill.filter(ImageFilter.MaxFilter(5))
  return fill,outl
if __name__=='__main__':
  out=Image.new('RGB',(200,200),(70,60,140))
  for j,f in enumerate(['SeoulHangangEB.ttf','NanumSquareNeo-eHv.ttf']):
    fi,ol=render(W.parent/f)
    for y in range(fi.height):
      for x in range(fi.width):
        if fi.getpixel((x,y)):out.putpixel((10+j*90+x,5+y),(255,255,255))
        elif ol.getpixel((x,y)):out.putpixel((10+j*90+x,5+y),(60,40,100))
  out.resize((600,600),Image.NEAREST).save(W/'shots/logo_try.png')

import json
sys.path.insert(0,str(Path(__file__).parent))
import wdff,bgedit
def apply(b,k,x0,y0,cell_w,cell_h,size,keep,frame_rgb,fill_rgb,ol_rgb,clear,clear_rgb=None):
  px,mw,mh,it=bgedit.load_bg(b,k);P=wdff.pal(it[k+1][4])
  cx0,cy0,cx1,cy1=clear
  for y in range(cy0,cy1):
    for x in range(cx0,cx1):
      if keep and keep[0]<=x<keep[2] and keep[1]<=y<keep[3]:continue
      p=px[y][x][0];px[y][x]=(p,0 if clear_rgb is None else bgedit.nearest(P,p,clear_rgb)[1])
  fi,ol=render(W.parent/'NanumSquareNeo-eHv.ttf',cell_w,cell_h,5,size)
  def setc(x,y,rgb):
    p=px[y][x][0];px[y][x]=(p,bgedit.nearest(P,p,rgb)[1])
  for i in range(5):
    top=y0+i*cell_h
    for x in range(x0,x0+cell_w+1):
      setc(x,top,frame_rgb);setc(x,top+cell_h,frame_rgb)
    for y in range(top,top+cell_h+1):
      setc(x0,y,frame_rgb);setc(x0+cell_w,y,frame_rgb)
  for y in range(fi.height):
    for x in range(fi.width):
      X,Y=x0-1+x,y0-1+y
      if not(0<=X<mw*8 and 0<=Y<mh*8):continue
      if fi.getpixel((x,y)):setc(X,Y,fill_rgb)
      elif ol.getpixel((x,y)):setc(X,Y,ol_rgb)
  return bgedit.store_bg(b,k,px,mw,mh,it)
