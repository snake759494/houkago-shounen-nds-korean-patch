"""UI 번역 검사: 바이트 용량(한글·전각=2바이트, ASCII=1바이트), 문자 집합, 변환 형식."""
import json,re,sys
from pathlib import Path
W=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(W/'tools'))
from check import ALLOW
src=json.load(open(W/'trans/ui_src.json',encoding='utf8'))
dst=json.load(open(W/'trans/ui_ko.json',encoding='utf8'))
bad=0
if len(src)!=len(dst):print('길이 불일치',len(src),len(dst));sys.exit(1)
def nbytes(s):return sum(1 if ord(c)<128 else 2 for c in s)
for i,(e,d) in enumerate(zip(src,dst)):
  if d is None:continue
  er=[]
  if nbytes(d)>e['cap']:er.append(f"용량 초과 {nbytes(d)}>{e['cap']}바이트")
  for c in d:
    if not('\uac00'<=c<='\ud7a3' or c in ALLOW or c in '\n%d0123456789 ' or c in e['ja']):er.append(f'문자 {c!r}')
  if re.search(r'[\u3040-\u30fa\u4e00-\u9fff]',d):er.append('가나/한자')
  if re.findall(r'%\d*[a-z]',e['ja'])!=re.findall(r'%\d*[a-z]',d):er.append('서식 지정자')
  if er:bad+=1;print(i,e['bin'],e['off'],repr(e['ja']),'=>',repr(d),';'.join(er))
print('오류',bad)
