"""WDFF 컨테이너 복호/암호화 (byte ^= key[i]+cnt, key='WILL CO.,LTD.\0' 순환)."""
import struct
KEY=b'WILL CO.,LTD.\x00'
def crypt(body):
  out=bytearray(body);i=0
  for n in range(len(out)):
    k=(KEY[i]+n)&0xff
    out[n]^=k
    i=i+1 if i<len(KEY)-1 else 0
  return bytes(out)
def decode(d):
  if d[:4]!=b'WDFF':return bytes(d)
  size,flag=struct.unpack_from('<II',d,4)
  body=d[16:16+size]
  return crypt(body) if flag==1 else body
def encode(body,orig):
  if orig[:4]!=b'WDFF':return bytes(body)
  hdr=bytearray(orig[:16]);struct.pack_into('<I',hdr,4,len(body))
  flag=struct.unpack_from('<I',orig,8)[0]
  return bytes(hdr)+(crypt(body) if flag==1 else body)
def entries(b):
  n=struct.unpack_from('<I',b,0)[0]
  return [struct.unpack_from('<II',b,4+8*i) for i in range(n)]
def items(b):
  """(index, kind, data_offset_in_b, header_u32, data) 목록"""
  out=[]
  for k,(o,s) in enumerate(entries(b)):
    a=4+o;raw=b[a:a+s];h=struct.unpack_from('<I',raw,0)[0];data=raw[4:]
    if (h&0xffff)==len(data) and (h>>16)*2==len(data):kind='pal'
    elif h==len(data)*8:kind='tile'
    elif (h&0xffff)==len(data):kind='map'
    else:kind='other'
    out.append((k,kind,a,h,data))
  return out
def pal(data):
  return [((c&31)*255//31,(c>>5&31)*255//31,(c>>10&31)*255//31) for c in struct.unpack_from('<%dH'%(len(data)//2),data)]
def rebuild(b,replace):
  """replace: {item_index: 새 raw(4바이트 헤더 포함)} -> 새 body"""
  ents=entries(b);n=len(ents);raws=[]
  for k,(o,s) in enumerate(ents):
    raws.append(replace.get(k,b[4+o:4+o+s]))
  out=bytearray(struct.pack('<I',n)+b'\0'*(8*n))
  for k,r in enumerate(raws):
    while len(out)%4:out+=b'\0'
    o=len(out)-4;struct.pack_into('<II',out,4+8*k,o,len(r));out+=r
  return bytes(out)
