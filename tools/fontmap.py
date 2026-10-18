import numpy as np
from PIL import Image,ImageDraw,ImageFont
d=open('ext/font12.char','rb').read()
def g(i):
  b=int.from_bytes(d[i*18:i*18+18],'little')
  return np.array([[b>>(y*12+x)&1 for x in range(12)] for y in range(12)],float)
F=[g(i) for i in range(3563)]
codes=[]
for hi in list(range(0x81,0x99)):
  for lo in list(range(0x40,0x7F))+list(range(0x80,0xFD)):
    c=hi<<8|lo
    if c>0x9872:continue
    try: ch=bytes([hi,lo]).decode('cp932')
    except: continue
    codes.append((c,ch))
font=ImageFont.truetype('C:/Windows/Fonts/msgothic.ttc',12)
def r(ch):
  im=Image.new('L',(12,12));ImageDraw.Draw(im).text((0,0),ch,255,font=font);return np.array(im)/255
R=[r(ch) for c,ch in codes]
def sim(a,b):
  best=0
  for dy in (-2,-1,0,1,2):
    for dx in (-1,0,1):
      bb=np.roll(np.roll(b,dy,0),dx,1)
      best=max(best,(a*bb).sum()/np.sqrt((a*a).sum()*(bb*bb).sum()+1e-9))
  return best
def _old(a,b):
  return (a*b).sum()/np.sqrt((a*a).sum()*(b*b).sum()+1e-9)

n,m=len(F),len(R);K=m-n
S=np.full((n,K+1),-1.0)
for i in range(n):
  for k in range(K+1): S[i,k]=sim(F[i],R[i+k])
D=np.full((n,K+1),-1e9);B=np.zeros((n,K+1),int)
D[0]=S[0]
for i in range(1,n):
  for k in range(K+1):
    pk=int(np.argmax(D[i-1,:k+1]));D[i,k]=D[i-1,pk]+S[i,k];B[i,k]=pk
k=int(np.argmax(D[-1]));path=[0]*n
for i in range(n-1,-1,-1): path[i]=k;k=B[i,k]
prev=0
for i in range(n):
  if path[i]!=prev: print('skip at',i,[hex(codes[i+j][0])+codes[i+j][1] for j in range(prev,path[i])]);prev=path[i]
print('final',path[-1],'avg',D[-1].max()/n)
import json;json.dump([codes[i+path[i]][0] for i in range(n)],open('ext/glyphcodes.json','w'))
low=[(i,hex(codes[i+path[i]][0]),codes[i+path[i]][1],round(S[i,path[i]],2)) for i in range(n) if S[i,path[i]]<0.5]
print(len(low),low[:40])
