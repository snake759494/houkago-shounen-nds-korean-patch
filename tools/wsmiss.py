"""원본 .ws 데이터 영역의 일본어 문자열 중 원고(ws_unique)와 매칭되지 않는 것 찾기(빠른 버전)"""
import glob,struct,re,json,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1]
JP=re.compile(r'[\u3040-\u30ff\u4e00-\u9fff]')
def strings(d):
  ds=0x200+(struct.unpack_from('<I',d,0x24)[0]&~0xF);sz=struct.unpack_from('<I',d,0x2c)[0]
  for m in re.finditer(rb'[^\x00]+',d[ds:ds+sz]):
    s=m.group();off=m.start()
    for k in range(len(s)):
      try:t=s[k:].decode('cp932')
      except Exception:continue
      if JP.match(t) or t[:1] in '!「（…　':yield ds,off+k,t;break
if __name__=='__main__':
  a=json.load(open(W/'trans/ws_unique.json',encoding='utf8'));K={x['ja'] for x in a}
  miss={}
  for f in sorted(glob.glob(str(W/'ws/*.ws'))):
    if 'dbg' in f:continue
    for ds,o,t in strings(open(f,'rb').read()):
      if not JP.search(t) or t in K:continue
      if re.search(r'[%\[\]()_]|NSD|FLAG|チェック|初期化|data/',t):continue
      miss.setdefault(t,[]).append(Path(f).name)
  print(len(miss))
  for t,fs in miss.items():print(repr(t)[:70],fs[:2])
