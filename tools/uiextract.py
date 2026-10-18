"""ARM9·오버레이에서 표시용 SJIS 문자열 후보 추출."""
import re,json
from pathlib import Path
W=Path(__file__).resolve().parents[1]
JP=re.compile(r'[぀-ヿ一-鿿]')
PUNCT=set('○◎◇◆□■△▲▽▼☆★♪→←↑↓※〒×÷＝＋－～',)|set('　、。！？「」（）・…～ー〜＋－：／％『』？')
def okchar(c):
  if '぀'<=c<='ヿ' or c in PUNCT or 0xff10<=ord(c)<=0xff5a or c in ' \n%d0123456789@':return True
  if '一'<=c<='鿿':
    return 0x889f<=int.from_bytes(c.encode('cp932'),'big')<=0x9872
  return False
res={}
for name in ['arm9','ov1','ov2','ov3','ov4','ov5','ov6']:
  d=open(W/'ext'/(name+'.bin'),'rb').read()
  out=[]
  for m in re.finditer(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\x20-\x7e]|\x0a)+\x00',d):
    b=m.group()[:-1]
    try:t=b.decode('cp932')
    except Exception:continue
    if len(JP.findall(t))<1 or not all(okchar(c) for c in t):continue
    if len(t)<2:continue
    out.append((hex(m.start()),t))
  res[name]=out
  print(name,len(out))
json.dump(res,open(W/'trans/ui_raw.json','w',encoding='utf8'),ensure_ascii=False,indent=0)
