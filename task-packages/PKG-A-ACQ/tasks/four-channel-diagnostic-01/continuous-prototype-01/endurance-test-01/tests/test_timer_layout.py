"""Real archived objects/ELFs, mutated only in temporary test copies."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import check_endurance as gate
timer=gate.timer_layout
base=gate.base
NEW_OBJ=HERE/'timer-layout-fix-01/build/main.c.obj'
NEW_ELF=HERE/'timer-layout-fix-01/build/four_mic_endurance.elf'
OLD_OBJ=base.REFERENCE/'build/main.c.obj'
OLD_ELF=base.REFERENCE/'runtime/four_mic_continuous.elf'


def offset(elf):
    sym=timer.entry(elf,'now_us');section=elf.sections[sym[5]]
    return section[4]+sym[1]-section[3]


class TimerLayoutTests(unittest.TestCase):
    def mutate(self,kind,relative,value,old=False):
        obj=OLD_OBJ if old else NEW_OBJ;exe=OLD_ELF if old else NEW_ELF
        original=obj if kind==1 else exe
        parsed=base.Elf32(original,kind);raw=bytearray(parsed.data)
        struct.pack_into('<I',raw,offset(parsed)+relative,value)
        with tempfile.TemporaryDirectory(prefix='e1_timer_') as folder:
            changed=Path(folder)/'changed.elf';changed.write_bytes(raw)
            with self.assertRaises(ValueError):timer.verify(changed if kind==1 else obj,changed if kind==2 else exe)

    def test_old_padded_layout(self):
        result=timer.verify(OLD_OBJ,OLD_ELF)
        self.assertEqual(result['timer_layout']['object']['literal_immediate'],16)
    def test_new_unpadded_layout_full_contract(self):
        result=gate.compiled(NEW_OBJ,NEW_ELF)
        self.assertEqual(result['timer_layout']['object']['literal_immediate'],12)
        self.assertEqual(result['divisor'],333333343)
        self.assertEqual(result['profile'],list(gate.PROFILE))
    def test_raw_before_fix_false_rejection(self):
        with self.assertRaisesRegex(ValueError,'Object timer code differs'):
            base.verify_elf(NEW_OBJ,NEW_ELF)
    def test_divisor_both_kinds(self):
        for kind in (1,2):
            with self.subTest(kind=kind):self.mutate(kind,108,333333333)
    def test_high_divisor_not_ignored(self):
        self.mutate(1,112,1);self.mutate(2,112,1)
    def test_wrong_literal_offset(self):
        self.mutate(1,22*4,0xe28f3010);self.mutate(2,22*4,0xe28f3010)
    def test_arithmetic_not_ignored(self):
        self.mutate(1,5*4,0xe1a0320e);self.mutate(2,5*4,0xe1a0320e)
    def test_return_not_ignored(self):
        self.mutate(2,26*4,0xe320f000)
    def test_padded_layout_must_use_nop(self):
        self.mutate(1,27*4,0xe1a00000,True);self.mutate(2,27*4,0xe1a00000,True)
    def test_object_call_addend(self):
        self.mutate(1,3*4,0xebffffff)
    def test_elf_call_target(self):
        e=base.Elf32(NEW_ELF,2)
        for i in (3,24):
            with self.subTest(index=i):
                w=struct.unpack_from('<I',e.data,offset(e)+i*4)[0]
                self.mutate(2,i*4,w+1)
    def test_object_relocations_not_ignored(self):
        e=base.Elf32(NEW_OBJ,1);sym=timer.entry(e,'now_us')
        start=sym[1]-e.sections[sym[5]][3]
        locations={}
        for rel in e.sections:
            if rel[1]==9 and rel[7]==sym[5]:
                for o in range(rel[4],rel[4]+rel[5],8):
                    location,info=e.unpack('<II',o)
                    if location in (start+12,start+96):locations[location-start]=(o,info)
        self.assertEqual(set(locations),{12,96})
        first,info=locations[12];second_info=locations[96][1]
        for title,value in (('type',(info&~255)|29),('wrong_symbol',second_info)):
            with self.subTest(case=title),tempfile.TemporaryDirectory(prefix='e1_reloc_') as folder:
                raw=bytearray(e.data);struct.pack_into('<I',raw,first+4,value)
                changed=Path(folder)/'changed.o';changed.write_bytes(raw)
                with self.assertRaisesRegex(ValueError,'relocations'):timer.verify(changed,NEW_ELF)

if __name__=='__main__':unittest.main(verbosity=2)
