"""Strict ARM now_us verifier: accept only the two observed 8-byte pool layouts.

This is not a general disassembler. Exact arithmetic instructions remain pinned.
Object R_ARM_CALL relocations and linked ELF branch destinations are checked.
"""
import struct
import check_entry as base

CALLS={3:'XTime_GetTime',24:'__aeabi_uldivmod'}


def entry(elf,name):
    matches=[]
    for section in elf.sections:
        if section[1]!=2:continue
        base.need(section[9]==16 and section[5]%16==0,'Unsupported symbol table')
        strings=elf.section_data(section[6])
        for offset in range(section[4],section[4]+section[5],16):
            item=elf.unpack('<IIIBBH',offset)
            if item[5] and elf.string(strings,item[0])==name:matches.append(item)
    base.need(len(matches)==1,'Missing/ambiguous timer symbol')
    return matches[0]


def object_calls(elf,sym):
    section_index=sym[5]
    start=sym[1]-elf.sections[section_index][3]
    found={}
    for rel in elf.sections:
        if rel[1] not in (4,9) or rel[7]!=section_index:continue
        base.need(rel[1]==9 and rel[9]==8 and rel[5]%8==0,'Unsupported ARM relocation table')
        base.need(0<=rel[6]<len(elf.sections),'Invalid relocation symbol table')
        table=elf.sections[rel[6]]
        base.need(table[1]==2 and table[9]==16,'Relocations not bound to symbols')
        strings=elf.section_data(table[6])
        for offset in range(rel[4],rel[4]+rel[5],8):
            location,info=elf.unpack('<II',offset)
            if not start<=location<start+sym[2]:continue
            index=info>>8;kind=info&255
            base.need(index*16+16<=table[5],'Relocation symbol index outside table')
            target=elf.unpack('<IIIBBH',table[4]+index*16)
            name=elf.string(strings,target[0]);relative=location-start
            base.need(relative not in found,'Duplicate timer relocation')
            found[relative]=(kind,name)
    expected={i*4:(28,name) for i,name in CALLS.items()} # R_ARM_CALL = 28
    base.need(found==expected,'Timer object relocations must call XTime_GetTime and __aeabi_uldivmod only')
    return found


def inspect(elf,kind):
    sym=entry(elf,'now_us')
    address,data=base.symbol(elf,'now_us')
    base.need(address%4==0 and len(data)%4==0,'Unsupported ARM timer alignment')
    words=list(struct.unpack('<'+'I'*(len(data)//4),data))
    # 27 actual instructions end with pop pc. Only pool alignment may add a NOP.
    pool_offset=((address+27*4+7)&~7)-address
    base.need(pool_offset in (108,112) and len(data)==pool_offset+8,'Unsupported timer pool/function extent')
    base.need(words[23]==0xe1c320d0 and words[26]==0xe49df004,'Timer load/return changed')
    immediate=pool_offset-(22*4+8) # ARM PC value = instruction address + 8.
    base.need(immediate in (12,16) and words[22]==0xe28f3000+immediate,'Timer literal does not address its aligned divisor')
    if pool_offset==112:base.need(words[27]==0xe320f000,'Invalid timer alignment padding')
    divisor=struct.unpack_from('<Q',data,pool_offset)[0]
    base.need(divisor==333333343,'Wrong actual timer divisor')
    canonical=words[:27]
    canonical[22]=0xe28f3000 # only the proven pool-offset operand is normalized.
    calls={}
    if kind==1:
        relocations=object_calls(elf,sym)
        for i,name in CALLS.items():
            base.need(words[i]==0xebfffffe,'Unsupported object call addend/opcode')
            calls[name]={'relocation_type':relocations[i*4][0],'symbol':name}
    elif kind==2:
        for i,name in CALLS.items():
            word=words[i];opcode=word>>24
            base.need(opcode in (0xeb,0xfa,0xfb),'Unsupported linked timer call opcode')
            delta=(word&0xffffff)<<2
            if delta&(1<<25):delta-=1<<26
            target=address+4*i+8+delta
            thumb=opcode in (0xfa,0xfb)
            if thumb:target+=(word>>23)&2
            destination=elf.symbol_value(name)
            base.need((target&~1)==(destination&~1) and thumb==bool(destination&1),
                      'Timer linked call target/mode mismatch: '+name)
            calls[name]={'target':hex(target),'thumb':thumb}
    else:raise ValueError('Unsupported timer ELF kind')
    for i in CALLS:canonical[i]=0xeb000000 # targets/addends validated above, not ignored.
    return canonical,dict(address=hex(address),pool_offset=pool_offset,literal_immediate=immediate,
                          padding_nop=pool_offset==112,divisor=divisor,calls=calls)


def verify(obj_path,elf_path):
    obj,exe=base.Elf32(obj_path,1),base.Elf32(elf_path,2)
    expected=struct.pack('<16I',*base.CONTRACT)
    base.need(base.symbol(obj,'continuous_contract')[1]==base.symbol(exe,'continuous_contract')[1]==expected,
              'Object/ELF buffer, packet, DDR, duration contract mismatch')
    ref_obj=base.Elf32(base.pinned(base.REFERENCE/'build/main.c.obj',
        '8a376d38a7188af5884ce0e6c7eff868a0878d222634ec360cb35961c7cd11ff'),1)
    ref_exe=base.Elf32(base.pinned(base.REFERENCE/'runtime/four_mic_continuous.elf',base.POLICY['archive_elf_sha256']),2)
    original,old_obj=inspect(ref_obj,1)
    linked,old_exe=inspect(ref_exe,2)
    actual_obj,obj_report=inspect(obj,1)
    actual_exe,exe_report=inspect(exe,2)
    base.need(original==linked==actual_obj==actual_exe,'Timer arithmetic changed beyond verified call relocation/pool alignment')
    end=exe.symbol_value('end');ranges=exe.loads+exe.allocated
    base.need(end<=base.CONTRACT[1] and all(base.CONTRACT[10]<=r['start']<r['end']<=base.CONTRACT[1] for r in ranges),
              'Program/stack/heap outside program DDR or overlapping RX')
    return dict(divisor=exe_report['divisor'],contract=list(base.CONTRACT),program_end=end,ranges=ranges,
                elf_sha256=base.digest(elf_path),object_sha256=base.digest(obj_path),
                timer_layout=dict(object=obj_report,elf=exe_report,reference_object=old_obj,reference_elf=old_exe))
