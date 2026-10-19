"""한글 ROM 빌드: 폰트(갈무리11) + mes 대사 + ov1 이름표 + UI 문자열."""
import re,json,glob,sys,hashlib
from pathlib import Path
import ndspy.rom,ndspy.lz10
W=Path(__file__).resolve().parents[1];ROOT=W.parent
SRC=ROOT/'Houkago Shounen (Japan).nds';OUT=ROOT/'Houkago Shounen (Korean).nds'
sys.path.insert(0,str(W/'tools'))
from check import NAMES,TAG
rom=ndspy.rom.NintendoDSRom.fromFile(str(SRC))
glyphcodes=json.load(open(W/'ext/glyphcodes.json'))
# ---- 번역 사전
def load_pairs():
  pairs={}
  for p in sorted((W/'trans/src').glob('*.json')):
    q=W/'trans/ko'/p.name
    if not q.exists():continue
    s=json.load(open(p,encoding='utf8'));k=json.load(open(q,encoding='utf8'))
    if len(s)==len(k):
      for a,b in zip(s,k):pairs[a]=b
  return pairs
PAIRS=load_pairs()
WSU={}
if (W/'trans/ws_unique_ko.json').exists():
  _a=json.load(open(W/'trans/ws_unique.json',encoding='utf8'));_b=json.load(open(W/'trans/ws_unique_ko.json',encoding='utf8'))
  if len(_a)==len(_b):WSU={x['ja']:y for x,y in zip(_a,_b)}
WSU.update(json.load(open(W/'trans/ws_test.json',encoding='utf8')) if (W/'trans/ws_test.json').exists() else {})
UI={}
_us=json.load(open(W/'trans/ui_src.json',encoding='utf8'));_uk=json.load(open(W/'trans/ui_ko.json',encoding='utf8'))
for e,k in zip(_us,_uk):
  if k is None:continue
  if e['bin']=='ov1' and 0x3c898<=int(e['off'],16)<0x3ca68:continue  # 변수 키 표는 KEYS로 처리
  UI.setdefault(e['bin'],{})[e['off']]=k
if (W/'trans/ui2_ko.json').exists():
  for e,k in zip(json.load(open(W/'trans/ui2_src.json',encoding='utf8')),json.load(open(W/'trans/ui2_ko.json',encoding='utf8'))):
    if k is None or (k==e['ja'] and k):continue
    k=re.sub(r'!([^!]+)!',lambda m:'!'+m[1]+'!',k)
    UI.setdefault(e['bin'],{})[e['off']]=k
KEYS=dict(NAMES);KEYS.update({'カズ':'카즈','だいすけ ':'다이스케'})
# ---- 인코딩 테이블: 한글 음절 -> 한자 슬롯 코드
KB=json.load(open(W/'trans/keyboard.json',encoding='utf8'))
texts=list(KB.values())+['군']+list(WSU.values())+list(PAIRS.values())+list(KEYS.values())+[v for g in UI.values() for v in g.values()]
extra=json.load(open(W/'trans/extra_chars.json',encoding='utf8')) if (W/'trans/extra_chars.json').exists() else ''
syl=sorted({c for t in texts for c in t if '\uac00'<=c<='\ud7a3'}|{c for c in extra if '\uac00'<=c<='\ud7a3'})
RESERVED=set()  # 원문 그대로 남길 키(時 分 数 夢 猫 등)의 한자 코드는 피함
for k in '時分数夢猫道':RESERVED.add(int.from_bytes(k.encode('cp932'),'big'))
slots=[(i,c) for i,c in enumerate(glyphcodes) if c>=0x889F and c not in RESERVED]
assert len(syl)<=len(slots),(len(syl),len(slots))
ENC={};GIDX={}
for ch,(i,c) in zip(syl,slots):ENC[ch]=c.to_bytes(2,'big');GIDX[ch]=i
def enc(s):
  out=bytearray()
  for ch in s:
    if ch in ENC:out+=ENC[ch]
    else:out+=ch.encode('cp932')
  return bytes(out)
# ---- 폰트
def bdf(path):
  g={};cur=None
  lines=open(path,encoding='utf8').read().splitlines();i=0
  while i<len(lines):
    l=lines[i]
    if l.startswith('ENCODING'):cur=int(l.split()[1])
    elif l.startswith('BBX'):bbx=list(map(int,l.split()[1:]))
    elif l=='BITMAP':
      rows=[];i+=1
      while lines[i]!='ENDCHAR':rows.append(int(lines[i],16));i+=1
      g[cur]=(bbx,rows,len(lines[i-1]) if rows else 2)
    i+=1
  return g
G11=bdf(W/'fonts/Galmuri11.bdf')
FONT_ASC=14
def glyph_bits(ch):
  (w,h,xo,yo),rows,_=G11[ord(ch)]
  nb=((w+7)//8)*8;bits=0
  top=11-h-yo  # 기준선: 한글 11px 상자 하단=셀 11행
  for r,v in enumerate(rows):
    y=top+r
    for x in range(w):
      if v>>(nb-1-x)&1:
        X=x+xo
        if 0<=X<12 and 0<=y<12:bits|=1<<(y*12+X)
  return bits
font=bytearray(rom.files[683])
for ch,i in GIDX.items():
  font[i*18:i*18+18]=glyph_bits(ch).to_bytes(18,'little')
rom.files[683]=bytes(font)
# ---- mes
def tr_line(s,miss):
  if not s:return s
  m=re.fullmatch(r'!([^!]+)!',s)
  if m:return '!'+KEYS.get(m[1],m[1])+'!'
  if s in PAIRS:return PAIRS[s]
  if re.search(r'[\u3040-\u30ff\u4e00-\u9fff]',re.sub(TAG,'',s)):miss.append(s)
  return s
stats={'lines':0,'miss':0}
for fid in range(len(rom.files)):
  n=rom.filenames.filenameOf(fid)
  if not(n and n.endswith('.mes')):continue
  raw=rom.files[fid];comp=raw[0]==0x10 and not raw.startswith(b'0000')
  d=ndspy.lz10.decompress(raw) if comp else raw
  out=[];miss=[]
  for l in d.split(b'\r\n'):
    m=re.match(rb'^(\d+):"(.*)"$',l,re.S)
    if not m:out.append(l);continue
    s=m[2].decode('cp932');t=tr_line(s,miss);stats['lines']+=1
    # 변수 토큰 안의 원문 키(時 등)는 원래 바이트 유지
    out.append(m[1]+b':"'+enc(t)+b'"')
  stats['miss']+=len(miss)
  nd=b'\r\n'.join(out)
  rom.files[fid]=ndspy.lz10.compress(nd) if comp else nd
# ---- ws 스크립트 문자열
import struct
from wsparse import parse
wsstat={'inplace':0,'reloc':0,'fail':[]}
for fid in range(len(rom.files)):
  n=rom.filenames.filenameOf(fid)
  if not(n and n.endswith('.ws')):continue
  raw=rom.files[fid]
  try:d=bytearray(ndspy.lz10.decompress(raw));comp=True
  except Exception:d=bytearray(raw);comp=False
  ds,sz,strs=parse(bytes(d));end=ds+sz;app=bytearray()
  for o,t,refs in strs:
    if t not in WSU:
      # 앞에 잡음 바이트가 붙은 경우: 원고에 있는 가장 긴 뒷부분으로 매칭
      sub=next((t[i:] for i in range(1,len(t)) if t[i:] in WSU),None)
      if not sub:continue
      o+=len(t[:len(t)-len(sub)].encode('cp932',errors='replace'));t=sub
      refs=[q for q in range(0x200,ds-2) if d[q] in (0xb8,0xb9,0xba,0xbb,0xbe,0xbf,0x68) and struct.unpack_from('<H',d,q+1)[0]==o]
    nb=enc(WSU[t])+b'\0';ob=len(t.encode('cp932'))
    a=ds+o;cap=ob+1
    if len(refs)!=1:
      e=a+ob
      while e<end and d[e]==0:e+=1
      cap=e-a
    if len(nb)<=cap:
      d[a:a+ob+1]=b'\0'*(ob+1);d[a:a+len(nb)]=nb;wsstat['inplace']+=1
    elif len(refs)==1:
      no=sz+len(app)
      if no+len(nb)>=0x10000:wsstat['fail'].append(t);continue
      app+=nb
      struct.pack_into('<H',d,refs[0]+1,no);wsstat['reloc']+=1
    else:wsstat['fail'].append(t)
  if app:
    d=d[:end]+app;sz2=sz+len(app);struct.pack_into('<I',d,0x2c,sz2)
    tot=(len(d)+0x3f)&~0x3f;d+=b'\0'*(tot-len(d));struct.pack_into('<I',d,0x30,tot)
  rom.files[fid]=ndspy.lz10.compress(bytes(d)) if comp else bytes(d)
print('ws',wsstat['inplace'],wsstat['reloc'],len(wsstat['fail']),wsstat['fail'][:5])
# ---- 그래픽(WDFF) 글자 패치
import wdff
import os
GP=[] if os.environ.get('NOGFX') else json.load(open(W/'trans/gfx_patches.json'))+json.load(open(W/'trans/gfx_direct.json'))+(json.load(open(W/'trans/gfx_tex.json')) if (W/'trans/gfx_tex.json').exists() else [])+(json.load(open(W/'trans/gfx_stamp.json')) if (W/'trans/gfx_stamp.json').exists() else [])+(json.load(open(W/'trans/gfx_chunk.json')) if (W/'trans/gfx_chunk.json').exists() else [])
if os.environ.get('NOGFX'):OUT=W/'nogfx.nds'
byfile={}
for n,o,h in GP:byfile.setdefault(n,[]).append((o,bytes.fromhex(h)))
BGNAMES={f.name for f in (W/'gfx_bg').glob('*.dec')} if not os.environ.get('NOGFX') else set()
for n,lst in byfile.items():
  if n in BGNAMES:continue
  fid=rom.filenames.idOf('data/'+n.replace('.dec','.bin'))
  dec=ndspy.lz10.decompress(rom.files[fid]);body=bytearray(wdff.decode(dec))
  for o,b in lst:body[o:o+len(b)]=b
  rom.files[fid]=ndspy.lz10.compress(wdff.encode(bytes(body),dec))
BGF=[] if os.environ.get('NOGFX') else sorted((W/'gfx_bg').glob('*.dec'))
for f in BGF:
  n=f.name;fid=rom.filenames.idOf('data/'+n.replace('.dec','.bin'))
  dec=ndspy.lz10.decompress(rom.files[fid]);body=bytearray(f.read_bytes())
  rom.files[fid]=ndspy.lz10.compress(wdff.encode(bytes(body),dec))
print('그래픽 파일',len(byfile),'타일',len(GP),'BG재구성',len(BGF))
# ---- ov1 이름표(16바이트 슬롯)
ovs=rom.loadArm9Overlays()
def patch_slots(ov,table):
  d=bytearray(ovs[ov].data)
  for off,(ja,ko) in table.items():
    off=int(off,16);b=ja.encode('cp932');assert d[off:off+len(b)]==b,(ov,hex(off),ja)
    size=len(b)
    while off+size<len(d) and d[off+size]==0:size+=1
    nb=enc(ko);cap=int(table_caps.get((ov,hex(off)),size-1))
    assert len(nb)<=cap,(ja,ko,len(nb),cap)
    d[off:off+size]=nb+b'\0'*(size-len(nb))
  ovs[ov].data=bytes(d)
table_caps={}
d1=ovs[1].data;base=d1.find('おさむ'.encode('cp932'),0x3c800)
nt={}
for i in range(26):
  off=base+16*i;ja=d1[off:off+16].split(b'\0')[0].decode('cp932')
  if ja in KEYS:nt[hex(off)]=(ja,KEYS[ja])
for ov,tab in UI.items():
  for off,ko in tab.items():pass
patch_slots(1,nt)
import ndspy.code
arm9=ndspy.code.MainCodeFile(rom.arm9,0x02000000)
a9=bytearray(arm9.sections[0].data) if False else None
BINS={}
def getbin(name):
  return ovs[int(name[2:])].data
def setbin(name,d):
  ovs[int(name[2:])].data=bytes(d)
uistat=0
for name,tab in UI.items():
  if name=='arm9':
    raw=bytearray(open(W/'ext/arm9.bin','rb').read())
  else: raw=bytearray(getbin(name))
  for off,ko in tab.items():
    o=int(off,16);e=o
    while raw[e]!=0:e+=1
    size=e-o
    while e<len(raw) and raw[e]==0:e+=1
    cap=e-o-1;nb=enc(ko)
    assert len(nb)<=cap,(name,off,ko)
    raw[o:o+size]=b'\0'*size;raw[o:o+len(nb)]=nb;uistat+=1
  if name=='arm9':ARM9NEW=bytes(raw)
  else:setbin(name,raw)
print('UI',uistat)
d2=bytearray(ovs[2].data)
for base,txt in ((0xddac,KB['page1']),(0xde74,KB['page2']),(0xe0c8,'군')):
  for i,ch in enumerate(txt):
    o=base+4*i;assert d2[o+2]==0 and d2[o]>=0x81
    d2[o:o+2]=enc(ch)
ovs[2].data=bytes(d2)
d6=bytearray(ovs[6].data)
for base,txt in ((0x4a48,KB['dream1']),(0x4a48+150,KB['dream2'])):
  for i,ch in enumerate(txt):
    o=base+3*i;assert d6[o+2]==0 and d6[o]>=0x81,(hex(o))
    d6[o:o+2]=enc(ch)
ovs[6].data=bytes(d6)
# 오버레이 저장(압축 해제 상태로 저장, 테이블 플래그 갱신)
import ndspy.code
table=rom.arm9OverlayTable
for k,o in ovs.items():
  rom.files[o.fileID]=o.save(compress=False)
rom.arm9OverlayTable=ndspy.code.saveOverlayTable(ovs)
if 'ARM9NEW' in globals():
  m9=rom.loadArm9();sec=m9.sections[0]
  sec.data=ARM9NEW[:len(sec.data)]
  rom.arm9=m9.save(compress=False)
rom.saveToFile(str(OUT))
json.dump({ch:ENC[ch].hex() for ch in syl},open(W/'trans/encoding.json','w',encoding='utf8'),ensure_ascii=False)
print('음절',len(syl),'/',len(slots),'번역쌍',len(PAIRS),stats)
