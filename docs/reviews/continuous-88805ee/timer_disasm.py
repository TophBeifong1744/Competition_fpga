import sys,struct,json
from pathlib import Path
sys.path.insert(0,'F:/NUEC/review-tools/continuous-capstone-5')
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_MODE_THUMB
task=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(task.parent/'current_build'))
from ps_contract import Elf32
elf=Elf32(task/'board-run-20260915-02/runtime/four_mic_continuous.elf',2)
local=[]
for sec in elf.sections:
    if sec[1]!=2: continue
    strings=elf.section_data(sec[6])
    for offset in range(sec[4],sec[4]+sec[5],16):
        item=elf.unpack('<IIIBBH',offset)
        if item[5] and elf.string(strings,item[0])=='now_us': local.append(item)
assert len(local)==1
s=local[0]; section=elf.sections[s[5]]; address=s[1]&~1
data=elf.section_data(s[5])[address-section[3]:address-section[3]+s[2]]
decoder=Cs(CS_ARCH_ARM,CS_MODE_THUMB if s[1]&1 else CS_MODE_ARM)
for ins in decoder.disasm(data,address): print(f'{ins.address:08x}: {ins.bytes.hex()} {ins.mnemonic} {ins.op_str}')
print('division symbol',hex(elf.symbol_value('__aeabi_uldivmod')))
print('timer function size',s[2])
