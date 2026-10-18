import sys,capstone
d=open(sys.argv[1],'rb').read();s=int(sys.argv[2],16);n=int(sys.argv[3],16);base=0x02000000 if 'arm9' in sys.argv[1] else int(sys.argv[4],16)
md=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB if len(sys.argv)>5 else capstone.CS_MODE_ARM)
for i in md.disasm(d[s:s+n],base+s):print(hex(i.address),i.mnemonic,i.op_str)
