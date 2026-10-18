"""지도 BG의 손글씨(파랑/빨강) 픽셀 덩어리 찾기"""
import sys,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import wdff,bgedit
def ink(rgb):
  r,g,b=rgb
  return (b>r+40 and b>g+10) or (r>g+60 and r>b+30)
def comps(f,k=0,gap=6):
  b=open(Path(__file__).resolve().parents[1]/'gfx'/f,'rb').read();px,mw,mh,it=bgedit.load_bg(b,k);P=wdff.pal(it[k+1][4])
  pts={(x,y) for y in range(192) for x in range(256) if ink(P[px[y][x][0]*16+px[y][x][1]])}
  seen=set();out=[]
  for p in pts:
    if p in seen:continue
    st=[p];seen.add(p);c=[]
    while st:
      x,y=st.pop();c.append((x,y))
      for dx in range(-gap,gap+1):
        for dy in range(-gap,gap+1):
          q=(x+dx,y+dy)
          if q in pts and q not in seen:seen.add(q);st.append(q)
    if len(c)>25:
      xs=[a for a,_ in c];ys=[b for _,b in c];out.append((min(xs),min(ys),max(xs),max(ys),len(c)))
  return sorted(out)
if __name__=='__main__':
  for n in range(2,8):
    print(n,comps(f'mini_mapA{n}_data_LZ.dec'))
