import hashlib,json,struct,sys
from pathlib import Path
P=Path('F:/NUEC/review-worktrees/s1-8f708e4/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/background-target-stop-20260917')
sys.path.insert(0,str(P.parents[1]/'current_build'))
from ps_contract import Elf32
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((P/'delivery-01/versions/build-result.json').read_text())
exe=Elf32(P/'delivery-01/versions/build/four_mic_endurance.elf',2)
objpath=next((P/'command-order-fix-01/before-fix/app/build').rglob('*.obj'))
obj=Elf32(objpath,1)
def data(elf,name):
 matches=[]
 for section in elf.sections:
  if section[1]!=2: continue
  strings=elf.section_data(section[6])
  for offset in range(section[4],section[4]+section[5],16):
   item=elf.unpack('<IIIBBH',offset)
   if item[5] and elf.string(strings,item[0])==name: matches.append(item)
 assert len(matches)==1,(name,len(matches))
 s=matches[0]; sec=elf.sections[s[5]]; off=s[1]-sec[3]
 return elf.section_data(s[5])[off:off+s[2]]
contracts={}
for name,field in [('continuous_contract','contract'),('scene_contract','scene')]:
 expected=struct.pack('<'+'I'*len(build['compiled'][field]),*build['compiled'][field])
 assert data(exe,name)==expected
 contracts[name]=list(struct.unpack('<'+'I'*(len(expected)//4),expected))
timer=data(exe,'now_us'); assert struct.unpack('<Q',timer[-8:])[0]==333333343
archive=exe.symbols['scene_archive']; end=exe.symbol_value('end')
assert archive[1]==0x112a80 and archive[2]==9600128 and end==0xa400c0
assert archive[1]+archive[2]<=end<=0x1000000
assert all(0x100000<=r['start']<r['end']<=end for r in exe.loads+exe.allocated)
assert sha(P/'delivery-01/versions/build/four_mic_endurance.elf')==build['compiled']['elf_sha256']
source=[]
for name,h in build['source_sha256'].items():
 assert sha(P/'delivery-01/versions/src'/name)==h
 source.append(name)
model=json.loads((P/'evidence/model_20260917_132800_1ed703b5/result.json').read_text())
for name,h in model['sha256'].items(): assert sha(P/name.replace('\\','/'))==h
result={'status':'PASS_LIMITED_ARCHIVE','contracts':contracts,'end':hex(end),'archive_start':hex(archive[1]),'archive_size':archive[2],'capture_bytes':9224000,'capacity_headroom_bytes':9600000-9224000,'timer_literal':333333343,'source_files_bound':source,'archived_model_source_hashes_match':True,'available_historical_object_sha256':sha(objpath),'post_build_object_sha256':build['compiled']['object_sha256'],'historical_object_matches_post_build':sha(objpath)==build['compiled']['object_sha256'],'object_scope':'Only before-fix object archived; report hash is not independent post-build object inspection','not_run':['ARM compile/link','full historical gate','JTAG download/readback','board']}
Path(__file__).with_name('artifact-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
