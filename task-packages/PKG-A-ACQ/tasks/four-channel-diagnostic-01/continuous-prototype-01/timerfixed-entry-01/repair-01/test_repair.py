"""Actual archive/parser and NTFS lock tests. No compiler or board."""
from contextlib import ExitStack
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ENTRY=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ENTRY))
import check_entry as gate
import artifact_guard as guard
from command_contract import normalize_command, command_argv

class RepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.obj=ENTRY/'user-build-20260916-01/app/build/CMakeFiles/four_mic_continuous.elf.dir/main.c.obj'
        self.elf=ENTRY/'user-build-20260916-01/app/build/four_mic_continuous.elf'
    def tearDown(self):
        self.tmp.cleanup()
    def mutate(self,offset,value,fmt='<I'):
        data=bytearray(self.elf.read_bytes())
        struct.pack_into(fmt,data,offset,value)
        p=self.root/'bad.elf';p.write_bytes(data)
        return p
    def reject(self,p):
        with self.assertRaises(Exception):
            gate.verify_elf(self.obj,p)
    def test_real_archived_startup_pass(self):
        r=gate.verify_elf(self.obj,self.elf)
        self.assertEqual(r['startup']['entry'],0x100000)
    def test_invalid_entries(self):
        for value in (0,0x01000000,0x100001,0x100004,0x1000cc,0x0010c000,0xffffffff):
            with self.subTest(entry=hex(value)):
                self.reject(self.mutate(24,value))
    def test_nonexecutable_load_rejected(self):
        phoff=self.load_header()
        self.reject(self.mutate(phoff+24,6))
    def test_entry_not_file_backed_rejected(self):
        phoff=self.load_header()
        self.reject(self.mutate(phoff+16,0))
        self.reject(self.mutate(phoff+16,4))
    def load_header(self):
        elf=gate.Elf32(self.elf,2)
        h=elf.unpack('<HHIIIIIHHHHHH',16)
        return next(h[4]+32*i for i in range(h[9]) if elf.unpack('<I',h[4]+32*i)[0]==1)
    def test_vector_symbol_mismatch(self):
        elf=gate.Elf32(self.elf,2)
        for section in elf.sections:
            if section[1]!=2:continue
            strings=elf.section_data(section[6])
            for off in range(section[4],section[4]+section[5],16):
                sym=elf.unpack('<IIIBBH',off)
                if elf.string(strings,sym[0])=='_vector_table':
                    self.reject(self.mutate(off+4,0x100004));return
        self.fail('symbol missing')
    def norm(self,s):
        return normalize_command(s,Path(gate.POLICY['reference_app']),Path(gate.POLICY['reference_bsp']))
    def test_gcc_semantic_case_preserved(self):
        cmd=gate.POLICY['compile_command']
        for before,after in (('-DSDT','-Dsdt'),('-U__clang__','-u__clang__'),('-O2','-o2')):
            with self.subTest(after=after):
                self.assertNotEqual(self.norm(cmd),self.norm(cmd.replace(before,after)))
        self.assertNotEqual(self.norm('gcc -DNAME=Value'),self.norm('gcc -DNAME=value'))
    def test_quotes_and_macro_path_values(self):
        self.assertNotEqual(self.norm('gcc "-DMSG=Hello World"'),self.norm('gcc -DMSG=Hello World'))
        self.assertNotEqual(self.norm('gcc -DSTR=F:/AbC'),self.norm('gcc -DSTR=f:/abc'))
        args=['gcc','-DSTR="Hello World"','-I','F:/Has Space/include']
        self.assertEqual(command_argv(subprocess.list2cmdline(args)),args)
    def test_only_recognized_paths_casefold(self):
        self.assertEqual(self.norm('F:/Tool/GCC.exe -IF:/SDK/Include -DSDT'),
                         self.norm('f:/tool/gcc.EXE -If:/sdk/include -DSDT'))
        self.assertNotEqual(self.norm('gcc -IF:/sdk -DSDT'),self.norm('gcc -if:/sdk -DSDT'))
    def test_expanded_link_contract(self):
        output=json.loads((ENTRY/'user-build-20260916-01/verification-01/ninja-commands.json').read_text())['stdout']
        app=Path(gate.POLICY['reference_app']);bsp=Path(gate.POLICY['reference_bsp'])
        gate.verify_link_output(output,app,bsp)
        for addition in (' -Wl,-e,0',' -Wl,--entry=0x01000000',' -u__clang__'):
            with self.subTest(addition=addition):
                bad=output.replace(' -Wl,-Map=memory.map,--cref',' -Wl,-Map=memory.map,--cref'+addition)
                with self.assertRaises(ValueError):gate.verify_link_output(bad,app,bsp)
    def test_mandatory_lock_blocks_write_replace_delete(self):
        p=self.root/'file';p.write_bytes(b'original')
        q=self.root/'replacement';q.write_bytes(b'other')
        with guard.locked_files([p]):
            self.assertEqual(p.read_bytes(),b'original')
            for op in (lambda:p.write_bytes(b'bad'),lambda:os.replace(q,p),lambda:p.unlink()):
                with self.assertRaises(OSError):op()
        p.write_bytes(b'released')
    def test_preexisting_writer_rejected(self):
        p=self.root/'file';p.write_bytes(b'original')
        with p.open('r+b'):
            with self.assertRaises(OSError):
                with guard.locked_files([p]):pass
    def test_directory_rename_rejected(self):
        d=self.root/'set';d.mkdir();p=d/'file';p.write_bytes(b'original')
        with guard.locked_files([p]):
            with self.assertRaises(OSError):d.rename(self.root/'replaced')
    def test_seal_retains_three_artifacts_during_active_rebuild(self):
        files={}
        for key in ('elf','bit','init'):
            files[key]=self.root/key;files[key].write_bytes(key.encode())
        expected={k:guard.sha(v) for k,v in files.items()}
        with ExitStack() as stack:
            with guard.locked_files(files.values()):
                snap=stack.enter_context(guard.sealed_snapshot(files,expected,self.root/'sealed'))
            for key in files:
                files[key].write_bytes(b'rebuilt')
                self.assertEqual(guard.sha(snap[key]),expected[key])
                with self.assertRaises(OSError):snap[key].write_bytes(b'replace')
        snap['elf'].write_bytes(b'after-release')
    def test_seal_wrong_hash_rejected(self):
        files={}
        for key in ('elf','bit','init'):
            files[key]=self.root/key;files[key].write_bytes(key.encode())
        with self.assertRaises(ValueError):
            with guard.sealed_snapshot(files,{k:'0'*64 for k in files},self.root/'sealed'):pass

if __name__=='__main__':
    unittest.main()
