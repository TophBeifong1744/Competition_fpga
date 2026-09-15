"""B-only adaptation: archived checker, real ARM decoding instead of unavailable objdump."""
import sys,struct,hashlib
from pathlib import Path
sys.path.insert(0,'F:/NUEC/review-tools/continuous-capstone-5')
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM

def capstone_timer(elf):
    found=[]
    for sec in elf.sections:
        if sec[1]!=2: continue
        strings=elf.section_data(sec[6])
        for offset in range(sec[4],sec[4]+sec[5],16):
            s=elf.unpack('<IIIBBH',offset)
            if s[5] and elf.string(strings,s[0])=='now_us': found.append(s)
    assert len(found)==1
    s=found[0]; assert s[1]&1==0
    section=elf.sections[s[5]]
    def memory(address,size):
        offset=address-section[3]
        assert 0<=offset and offset+size<=section[5]
        return elf.section_data(s[5])[offset:offset+size]
    code=memory(s[1],s[2]); ins=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(code,s[1]))
    loads=[i for i,x in enumerate(ins) if x.mnemonic=='ldrd' and x.op_str=='r2, r3, [r3]']
    assert len(loads)==1
    index=loads[0]; add=ins[index-1]; call=ins[index+1]
    assert add.mnemonic=='add' and add.op_str.startswith('r3, pc, #')
    literal=add.address+8+int(add.op_str.split('#')[1],0)
    divisor=struct.unpack('<Q',memory(literal,8))[0]
    assert divisor==333333343
    assert call.mnemonic=='blx' and int(call.op_str.lstrip('#'),0)==elf.symbol_value('__aeabi_uldivmod')&~1
    assert any(x.mnemonic=='bl' and int(x.op_str.lstrip('#'),0)==elf.symbol_value('XTime_GetTime')&~1 for x in ins)
    lines=[f'{x.address:08x}: {x.bytes.hex()} {x.mnemonic} {x.op_str}' for x in ins if x.address<literal]
    lines.append(f'{literal:08x}: literal uint64 divisor={divisor} ({divisor:#x}); real division target={call.op_str}')
    return '\n'.join(lines)

run=Path(sys.argv[1]).resolve()
source=(run/'check_evidence.py').read_text(encoding='utf-8')
assert hashlib.sha256((run/'check_evidence.py').read_bytes()).hexdigest()==__import__('json').loads((run.parent/'publication/SHA256.json').read_bytes())['board-run-20260915-02/check_evidence.py']
source=source.replace('ROOT = Path(__file__).resolve().parent','ROOT = Path(sys.argv[1]).resolve()',1)
start=source.index('    objdump = Path(')
end=source.index('    vectors = []',start)
source=source[:start]+'    disassembly = capstone_timer(exe)\n'+source[end:]
exec(compile(source,str(run/'check_evidence.py')+' [B Capstone adaptation]','exec'),{'__name__':'__main__','__file__':str(run/'check_evidence.py'),'capstone_timer':capstone_timer})
