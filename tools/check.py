import sys,json,re
from pathlib import Path
W=Path(__file__).resolve().parents[1]
NAMES={'おさむ':'오사무','あつし':'아츠시','かずゆき':'카즈유키','よしお':'요시오','ひでき':'히데키','だいすけ':'다이스케','たけし':'타케시','ともひろ':'토모히로','いく':'이쿠','たつや':'타츠야','まゆみ':'마유미','のりこ':'노리코','かおる':'카오루','はるみ':'하루미','ちかこ':'치카코','まこと':'마코토','せつこ':'세츠코','みよ':'미요','お父さん':'아빠','お母さん':'엄마','井上先生':'이노우에선생님','おばあちゃん':'할머니'}
KEEP=set('時 分 数 数２ 夢 猫 おまいり あぜ道 カズ'.split())
ALLOW=set('　！？、。…「」『』（）〜ー・：／＋－×％＆♪☆★○●◎△▲□■→←↑↓‥')|{chr(c) for c in range(0xFF10,0xFF1A)}|{chr(c) for c in range(0xFF21,0xFF3B)}|{chr(c) for c in range(0xFF41,0xFF5B)}
TAG=r'!(?:co|wa|sp|na)[0-9]+'
def tokens(s): return re.findall(TAG,s)
def strip(s):
  s=re.sub(TAG,'',s); return re.sub(r'!([^!]+)!',lambda m:'□'*4,s)
def check(src,dst):
  err=[]
  if not isinstance(dst,str): return ['문자열 아님']
  if tokens(src)!=tokens(dst): err.append(f'태그 불일치 {tokens(src)} / {tokens(dst)}')
  sv=[v for v in re.findall(r'!([^!]+)!',re.sub(TAG,'',src))]
  dv=[v for v in re.findall(r'!([^!]+)!',re.sub(TAG,'',dst))]
  exp=sorted(NAMES.get(v,v) for v in sv)
  if sorted(dv)!=exp: err.append(f'변수 불일치 {exp} / {sorted(dv)}')
  BS=chr(92)+'n'; lines=strip(dst).split(BS); sl=src.count(BS)+1
  if len(lines)>max(2,sl): err.append(f'줄 수 {len(lines)}')
  for ln in lines:
    if len(ln)>18 and len(ln)>max(len(x) for x in strip(src).split(BS)): err.append(f'줄 길이 {len(ln)}: {ln}')
  for ch in strip(dst).replace('\n',''):
    if not ('\uac00'<=ch<='\ud7a3' or ch in ALLOW or ch=='□'):
      if ch not in strip(src): err.append(f'허용 안 된 문자 {ch!r}')
  if re.search(r'[\u3040-\u30ff\u4e00-\u9fff]',strip(dst)) and strip(dst)!=strip(src): err.append('가나/한자 잔존')
  return err

def check_ws():
  src=json.load(open(W/'trans/ws_unique.json',encoding='utf8'))
  p=W/'trans/ws_unique_ko.json'
  dst=json.load(open(p,encoding='utf8'))
  bad=0
  if len(dst)!=len(src): print('길이 불일치',len(src),len(dst));return 1
  for i,(e,d) in enumerate(zip(src,dst)):
    s=e['ja'].replace(chr(10),chr(92)+'n');dd=d.replace(chr(10),chr(92)+'n')
    er=check(s,dd)
    if e['max'] is not None and len(d)>e['max']: er.append(f"최대 {e['max']}자 초과({len(d)})")
    if er: bad+=1;print(i,repr(e['ja']),'=>',repr(d),'|',';'.join(er))
  print('오류',bad);return bad

if __name__=="__main__" and sys.argv[1:]==["ws"]:
  check_ws();sys.exit()
if __name__=="__main__":
  bad=0
  for n in sys.argv[1:]:
    n=Path(n).stem;src=json.load(open(W/'trans/src'/(n+'.json'),encoding='utf8'))
    p=W/'trans/ko'/(n+'.json')
    if not p.exists(): print(n,'출력 없음');bad+=1;continue
    dst=json.load(open(p,encoding='utf8'))
    if len(src)!=len(dst): print(n,'길이 불일치',len(src),len(dst));bad+=1;continue
    for i,(s,d) in enumerate(zip(src,dst)):
      e=check(s,d)
      if e: bad+=1;print(n,i,s,'=>',d,'|',';'.join(e))
  print('오류',bad)
