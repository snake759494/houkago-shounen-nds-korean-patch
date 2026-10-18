import struct,re,glob,collections
from pathlib import Path
W=Path(__file__).resolve().parents[1]
JP=re.compile(r'[\u3040-\u30ff\u4e00-\u9fff\uff01-\uff5e]')
def parse(d):
  h24,h28,h2c,h30=struct.unpack_from('<4I',d,0x24)
  ds=0x200+(h24&~0xF);end=ds+h2c
  code=d[0x200:ds]
  strs=[]
  i=ds
  for m in re.finditer(rb'[^\x00]+',d[ds:end]):
    s=m.group();off=m.start();t=None
    for k in range(0,len(s)):
      try:
        tt=s[k:].decode('cp932')
      except Exception:continue
      if k and not JP.match(tt):continue
      # 앞쪽 잡음 문자 제거(반각 가나·기호·제2수준 한자·ASCII)
      j=0
      while j<len(tt):
        c=tt[j];b=c.encode('cp932')
        bad=len(b)==1 or (('一'<=c<='鿿') and int.from_bytes(b,'big')>0x9872) or c in '°±´¨'
        if not bad or tt[j:j+1]=='!':break
        j+=1
      if k and j:off+=len(tt[:j].encode('cp932'));tt=tt[j:]
      t=tt;off+=k;break
    if t is None:continue
    if JP.search(t) and not t.startswith('data/'):
      refs=[k for k in range(0x200,ds-2) if d[k] in (0xb8,0xb9,0xba,0xbb,0xbe,0xbf,0x68) and struct.unpack_from('<H',d,k+1)[0]==off]
      strs.append((off,t,refs))
  return ds,h2c,strs
if __name__=='__main__':
  tot=0;nref=collections.Counter();chars=0
  for f in sorted(glob.glob(str(W/'ws/*.ws'))):
    d=open(f,'rb').read();ds,sz,strs=parse(d)
    tot+=len(strs);chars+=sum(len(t) for _,t,_ in strs)
    for o,t,r in strs:nref[len(r)]+=1
  print(tot,chars,nref)
