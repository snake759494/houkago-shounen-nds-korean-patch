"""mes 원문을 파일 순서대로 추출. 앞선 파일에서 나온 동일 문자열은 제외(공유 사전)."""
import re,glob,json,os
from pathlib import Path
W=Path(__file__).resolve().parents[1]
files=sorted(glob.glob(str(W/'mes/*.mes')))
# 스토리 순서: S_op, S_0000.. , 기타
def key(f):
  n=Path(f).stem
  pr={'S_op':0}.get(n,1 if n.startswith('S_0') else 2)
  return (pr,n)
files.sort(key=key)
seen=set();order=[];total=0
for f in files:
  items=[]
  for l in open(f,encoding='cp932').read().splitlines():
    m=re.match(r'^(\d+):"(.*)"$',l)
    if not m or not m[2]:continue
    s=m[2]
    if re.fullmatch(r'![^!]+!',s):continue  # 화자 라벨: 사전으로 처리
    if not re.search(r'[\u3040-\u30ff\u4e00-\u9fff\uff01-\uff5e]',re.sub(r'!(co|wa|sp|na)\d+!?','',s)):continue
    if s in seen:continue
    seen.add(s);items.append(s);total+=len(s)
  if items:
    json.dump(items,open(W/'trans/src'/(Path(f).stem+'.json'),'w',encoding='utf8'),ensure_ascii=False,indent=0)
    order.append((Path(f).stem,len(items),sum(map(len,items))))
json.dump(order,open(W/'trans/order.json','w'),indent=0)
print(len(seen),total)
for o in order:print(o)
