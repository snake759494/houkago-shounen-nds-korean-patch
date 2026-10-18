"""VRAM 덤프의 타일(32바이트)을 그래픽 파일에서 찾는다."""
import glob,sys,collections
from pathlib import Path
W=Path(__file__).resolve().parents[1]
files={Path(f).name:open(f,'rb').read() for f in glob.glob(str(W/'gfx/*.dec'))}
def find(dump,step=32,minnz=12):
  d=open(W/dump,'rb').read();hits=collections.Counter();where={}
  for i in range(0,len(d),step):
    t=d[i:i+step]
    if sum(1 for b in t if b)<minnz or len(set(t))<4:continue
    for n,fd in files.items():
      j=fd.find(t)
      if j>=0:hits[n]+=1;where.setdefault(n,[]).append((i,j))
  return hits,where
if __name__=='__main__':
  for dmp in sys.argv[1:]:
    h,w=find(dmp)
    print(dmp,h.most_common(8))
