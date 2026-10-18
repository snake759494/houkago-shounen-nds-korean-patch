"""타일 묶음을 공유하는 여러 맵을 함께 편집해 재인코딩 -> gfx_bg 파일에 반영"""
import sys,struct,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import wdff,bgany,bgedit
W=Path(__file__).resolve().parents[1]
def run(fname,maps,pal_k,tile_k,edits):
  src=W/'gfx_bg'/fname
  b=(src if src.exists() else W/'gfx'/fname).read_bytes()
  it=wdff.items(b);P=wdff.pal(it[pal_k][4])
  pxs={m:bgany.load(b,m,pal_k,tile_k)[:3] for m in maps}
  for m,ed in edits.items():
    px,mw,mh=pxs[m]
    for e in ed:
      x0,y0,w,h=e['clear']
      for y in range(y0,y0+h):
        for x in range(x0,x0+w):p=px[y][x][0];px[y][x]=(p,bgedit.nearest(P,p,tuple(e['bg']))[1])
      for ln in e['lines']:bgedit.draw(px,ln['text'],ln.get('font',11),ln['x'],ln['y'],tuple(e['fg']),tuple(e['fg']),P)
  tiles=[];index={};raws={}
  for m in maps:
    px,mw,mh=pxs[m];mp=bytearray()
    for my in range(mh):
      for mx in range(mw):
        pn=px[my*8][mx*8][0];t=bytearray(32)
        for y in range(8):
          for x in range(8):
            c=px[my*8+y][mx*8+x][1];t[y*4+x//2]|=(c<<4) if x&1 else c
        k=bytes(t)
        if k not in index:index[k]=len(tiles);tiles.append(k)
        mp+=struct.pack('<H',(index[k]&0x3ff)|(pn<<12))
    raws[m]=struct.pack('<I',it[m][3])+bytes(mp)
  assert len(tiles)<=1024
  td=b''.join(tiles);raws[tile_k]=struct.pack('<I',len(td)*8)+td
  (W/'gfx_bg').mkdir(exist_ok=True);src.write_bytes(wdff.rebuild(b,raws))
if __name__=='__main__':
  hdr=lambda x,y,w,t:{"clear":[x-2,y-1,w+30,16],"bg":[255,255,255],"fg":[40,40,40],"lines":[{"x":x+2,"y":y+1,"text":t}]}
  run('minigame_data_LZ.dec',[22,23],25,24,{22:[hdr(18,12,70,'규칙 등'),hdr(16,90,80,'노는 요령')],23:[hdr(18,12,70,'조작 설명')]})
  print('ok')
