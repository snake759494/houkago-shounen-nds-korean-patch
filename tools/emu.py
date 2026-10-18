"""헤드리스 DeSmuME: python emu.py ROM 명령.json  (시스템 입력 사용 안 함, 끝나면 종료)
명령: [{"keys":"a","hold":2,"wait":60,"shot":"name","save":"st","load":"st","frames":n}]"""
import sys,json,os
from pathlib import Path
from desmume.emulator import DeSmuME
from desmume.controls import Keys,keymask
rom=Path(sys.argv[1]).resolve();cmds=json.loads(Path(sys.argv[2]).read_text(encoding='utf8'))
W=Path(__file__).resolve().parents[1];shots=W/'shots';st=W/'states';st.mkdir(exist_ok=True)
os.chdir(os.environ.get('EMU_TMP',str(W)))
SAV=os.environ.get('EMU_SAV')
import shutil
e=DeSmuME();e.volume_set(0);e.open(str(rom))
if SAV and Path(SAV).exists():
  assert e.backup.import_file('W:/'+Path(SAV).resolve().relative_to(W).as_posix());e.reset()
def fr(n):
  for _ in range(n):e.cycle(with_joystick=False)
for a in cmds:
  if a.get('savreset'):
    fr(60);print('export',e.backup.export_file('W:/_bk.sav'));e.reset();print('import',e.backup.import_file('W:/_bk.sav'));e.reset()
  if a.get('reset'):e.reset()
  if 'load' in a:e.savestate.load_file(str(st/(a['load']+'.dst')))
  m=0
  for k in a.get('keys','').split('+'):
    if k:m|=keymask(getattr(Keys,'KEY_'+k.upper()))
  rep=a.get('repeat',1)
  for _ in range(rep):
    if m:e.input.keypad_add_key(m)
    if 'touch' in a:e.input.touch_set_pos(*a['touch'])
    fr(a.get('hold',4 if (m or 'touch' in a) else 0))
    if m:e.input.keypad_rm_key(m)
    if 'touch' in a:e.input.touch_release()
    fr(a.get('wait',30))
  if 'shot' in a:e.screenshot().save(shots/(a['shot']+'.png'))
  if 'save' in a:e.savestate.save_file(str(st/(a['save']+'.dst')))
  if 'snap' in a:
    sd=W/'snaps'/a['snap'];sd.mkdir(parents=True,exist_ok=True)
    for nm,(st0,n) in {'ioA':(0x04000000,0x80),'ioB':(0x04001000,0x80),'oam':(0x07000000,0x800),'pal':(0x05000000,0x800),
      'objA':(0x06400000,0x40000),'objB':(0x06600000,0x20000),'bgA':(0x06000000,0x80000),'bgB':(0x06200000,0x20000)}.items():
      open(sd/(nm+'.bin'),'wb').write(bytes(e.memory.unsigned[st0:st0+n]))
    e.screenshot().save(sd/'screen.png')
  if 'dump' in a:
    s,n=a['dump'];open(W/(a.get('dumpname','dump')+'.bin'),'wb').write(bytes(e.memory.unsigned[s:s+n]))
if os.environ.get('EMU_SAVOUT'):e.backup.export_file('W:/'+Path(os.environ['EMU_SAVOUT']).resolve().relative_to(W).as_posix())
e.destroy()
print('done')
