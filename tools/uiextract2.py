"""설명문(@ 줄바꿈, !변수!) 포함 UI 문자열 추가 추출 -> trans/ui2_src.json (ui_src.json에 없는 것)"""
import re,json,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1];sys.path.insert(0,str(W/'tools'))
import uiextract
JP=re.compile(r'[\u3040-\u30ff\u4e00-\u9fff\uff10-\uff5a、。！？「」]')
def ok(c):return uiextract.okchar(c) or (' '<=c<='~') or ('一'<=c<='鿿')
old=json.load(open(W/'trans/ui_src.json',encoding='utf8'))
have={(e['bin'],int(e['off'],16)) for e in old}
new=[]
for name in ['arm9','ov1','ov2','ov3','ov4','ov5','ov6']:
  d=open(W/'ext'/(name+'.bin'),'rb').read()
  for m in re.finditer(rb'(?<=\x00)(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\x20-\x7e]|\x0a)+\x00',d):
    s=m.start();b=m.group()[:-1]
    if (name,s) in have:continue
    try:t=b.decode('cp932')
    except:continue
    if not all(ok(c) for c in t):continue
    core=re.sub(r'![^!]*!','',t).replace('@','')
    j=len(JP.findall(core));a=len(re.findall(r'[ -~]',core))
    if j<2 or a>j//2:continue
    e=s+len(b)
    while e<len(d) and d[e]==0:e+=1
    new.append({'bin':name,'off':hex(s),'ja':t,'cap':e-s-1})
json.dump(new,open(W/'trans/ui2_src.json','w',encoding='utf8'),ensure_ascii=False,indent=0)
print(len(new),sum(len(x['ja']) for x in new))
