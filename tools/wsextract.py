import sys,json,re,glob
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from wsparse import parse,W
DEBUG=re.compile(r'%|\[|\]|\(|\)|NSD|FLAG|_')
tot=0;chars=0;inplace=0
seen={}
for f in sorted(glob.glob(str(W/'ws/*.ws'))):
  d=open(f,'rb').read();ds,sz,strs=parse(d);out=[]
  for o,t,r in strs:
    if DEBUG.search(re.sub(r'!(co|wa|sp|na)[0-9]+','',t)) or o==0:continue
    if re.search(r'[A-Za-z]',re.sub(r'!(co|wa|sp|na)[0-9]+','',t)):continue
    nb=len(t.encode('cp932'))
    # 뒤따르는 NUL 패딩까지 제자리 용량
    e=ds+o+nb
    while e<len(d) and d[e]==0 and e<ds+sz:e+=1
    cap=None if len(r)==1 else (e-(ds+o)-1)//2
    out.append({'off':o,'ja':t,'max':cap})
    tot+=1;chars+=len(t);inplace+=cap is not None
  if out:json.dump(out,open(W/'trans/ws_src'/(Path(f).stem+'.json'),'w',encoding='utf8'),ensure_ascii=False,indent=0)
print(tot,chars,inplace)
