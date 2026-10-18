"""달력 텍스처(event_106a/b) 요일·월 한글화 -> trans/gfx_tex.json"""
import sys,json,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import texedit
from PIL import Image,ImageDraw,ImageFont
W=texedit.W
F=ImageFont.truetype(str(W.parent/'NanumSquareNeo-eHv.ttf'),17)
F2=ImageFont.truetype(str(W.parent/'NanumSquareNeo-eHv.ttf'),12)
def near(P,rgb):return min(range(len(P)),key=lambda i:sum((a-b)**2 for a,b in zip(P[i],rgb)))
out=[]
for name in ('event_106a_data_LZ.dec','event_106b_data_LZ.dec'):
  b=bytearray(open(W/'gfx'/name,'rb').read());t=texedit.textures(bytes(b))[0];w,h=t['w'],t['h'];P=t['P']
  def get(x,y):return b[t['abs']+(h-1-y)*w+x]
  def put(x,y,v):b[t['abs']+(h-1-y)*w+x]=v
  def draw(x0,y0,x1,y1,ch,font,rgb=(24,24,24)):
    cnt=collections.Counter(get(x,y) for y in range(y0,y1) for x in range(x0,x1))
    bgc=cnt.most_common(1)[0][0]
    ink=near(P,rgb)
    for y in range(y0,y1):
      for x in range(x0,x1):put(x,y,bgc)
    m=Image.new('L',(x1-x0,y1-y0));d=ImageDraw.Draw(m)
    bb=d.textbbox((0,0),ch,font=font);d.text(((x1-x0-(bb[2]-bb[0]))//2-bb[0],(y1-y0-(bb[3]-bb[1]))//2-bb[1]),ch,255,font=font)
    for y in range(m.height):
      for x in range(m.width):
        if m.getpixel((x,y))>110:put(x0+x,y0+y,ink)
  xs=[30,58,86,114,142,170,198,226]
  for i,ch in enumerate('일월화수목금토'):draw(xs[i]+2,90,xs[i+1]-2,111,ch,F,(200,40,48) if i==0 else (40,140,224) if i==6 else (24,24,24))
  draw(137,71,150,85,'월',F2)
  s=t['abs'];e=s+w*h;out.append([name,s,bytes(b[s:e]).hex()])
  im=Image.new('RGB',(w,h))
  for y in range(h):
    for x in range(w):im.putpixel((x,y),P[get(x,y)])
  im.save(W/'shots'/(name[:10]+'.png'))
json.dump(out,open(W/'trans/gfx_tex.json','w'))
print('ok')
