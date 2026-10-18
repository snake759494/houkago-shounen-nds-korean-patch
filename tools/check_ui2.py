"""ui2 번역 검사: 바이트 용량, @줄 수·줄 길이(8자), !변수! 일치, 문자 집합."""
import json,re,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1];sys.path.insert(0,str(W/'tools'))
from check import ALLOW,NAMES
src=json.load(open(W/'trans/ui2_src.json',encoding='utf8'));dst=json.load(open(W/'trans/ui2_ko.json',encoding='utf8'))
if len(src)!=len(dst):print('길이 불일치',len(src),len(dst));sys.exit(1)
nb=lambda s:sum(1 if ord(c)<128 else 2 for c in s)
bad=0
for i,(e,d) in enumerate(zip(src,dst)):
  if d is None:continue
  er=[]
  if nb(d)>e['cap']:er.append(f"용량 {nb(d)}>{e['cap']}")
  sv=[NAMES.get(v,v) for v in re.findall(r'!([^!]+)!',e['ja'])];dv=re.findall(r'!([^!]+)!',d)
  if sv!=dv:er.append(f'변수 {sv}/{dv}')
  if '@' in e['ja']:
    sl=e['ja'].count('@')+1;dl=d.split('@')
    if len(dl)>sl+1:er.append(f'줄 수 {len(dl)}>{sl+1}')
    for ln in dl:
      L=len(re.sub(r'![^!]+!','□□□□',ln))
      if L>8:er.append(f'줄 길이 {L}: {ln}')
  core=re.sub(r'![^!]+!','',d)
  for c in core:
    if not('\uac00'<=c<='\ud7a3' or c in ALLOW or c in '@%d0123456789 ' or c in e['ja']):er.append(f'문자 {c!r}')
  if re.search(r'[\u3040-\u30fa\u4e00-\u9fff]',core):er.append('가나/한자')
  if er:bad+=1;print(i,e['bin'],e['off'],repr(e['ja']),'=>',repr(d),';'.join(er))
print('오류',bad)
