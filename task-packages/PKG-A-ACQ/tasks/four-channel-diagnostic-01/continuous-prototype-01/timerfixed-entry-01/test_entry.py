"""Offline unit/negative checks; real frozen binaries, no new firmware compile."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import check_entry as c


class EntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def launch_fixture(self):
        app = self.root/'four_mic_continuous'
        config = json.loads((c.REFERENCE/'configuration/launch.json').read_text(encoding='utf-8'))
        for rel in ('build/four_mic_continuous.elf','_ide/bitstream/system_continuous_20260915.bit','_ide/psinit/ps7_init.tcl'):
            path = app/rel
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(b'path-only fixture; not hardware data')
        self.write_launch(app,config)
        return app,config

    def write_launch(self,app,config):
        (app/'_ide/launch.json').write_text(json.dumps(config),encoding='utf-8')

    def test_fixed_real_object_elf(self):
        r=c.verify_elf(c.REFERENCE/'build/main.c.obj',c.REFERENCE/'runtime/four_mic_continuous.elf')
        self.assertEqual(r['divisor'],333333343)

    def test_old_real_elf_rejected(self):
        with self.assertRaises(ValueError):
            c.verify_elf(c.REFERENCE/'build/main.c.obj',c.TASK/'board-run-20260915-01/four_mic_continuous_prefix.elf')

    def test_old_expression_rejected(self):
        path=self.root/'main_continuous.c'
        data=(c.REFERENCE/'ps/continuous/main_continuous.c').read_bytes()
        path.write_bytes(data.replace(b'/(COUNTS_PER_SECOND)',b'/COUNTS_PER_SECOND').replace(b'/ (COUNTS_PER_SECOND)',b'/ COUNTS_PER_SECOND'))
        with self.assertRaises(ValueError):
            c.pinned(path,c.POLICY['source_sha256']['continuous/main_continuous.c'])

    def test_missing_source_rejected(self):
        with self.assertRaises(Exception):
            c.pinned(self.root/'missing.c','0'*64)

    def test_mutated_compiled_base_rejected(self):
        path=self.root/'bad.o'
        data=(c.REFERENCE/'build/main.c.obj').read_bytes()
        contract=c.struct.pack('<16I',*c.CONTRACT)
        self.assertEqual(data.count(contract),1)
        values=list(c.CONTRACT);values[1]=0x01000100
        path.write_bytes(data.replace(contract,c.struct.pack('<16I',*values)))
        with self.assertRaises(ValueError):
            c.verify_elf(path,c.REFERENCE/'runtime/four_mic_continuous.elf')

    def test_changed_divisor_rejected(self):
        path=self.root/'bad.elf'
        data=(c.REFERENCE/'runtime/four_mic_continuous.elf').read_bytes()
        old=c.struct.pack('<Q',333333343)
        self.assertGreaterEqual(data.count(old),1)
        path.write_bytes(data.replace(old,c.struct.pack('<Q',666666687)))
        with self.assertRaises(ValueError):
            c.verify_elf(c.REFERENCE/'build/main.c.obj',path)

    def test_valid_load_paths(self):
        app,config=self.launch_fixture()
        self.assertEqual(Path(c.launch_paths(app,self.root)['elf']),(app/'build/four_mic_continuous.elf').resolve())

    def reject_launch(self,change):
        app,config=self.launch_fixture()
        change(config['configurations'][0])
        self.write_launch(app,config)
        with self.assertRaises(Exception):
            c.launch_paths(app,self.root)

    def test_old_elf_path_rejected(self):
        self.reject_launch(lambda x:x['targetSetup']['downloadElf'][0].update(elfFile=str(c.REFERENCE/'runtime/four_mic_continuous.elf')))

    def test_wrong_bit_path_rejected(self):
        self.reject_launch(lambda x:x['targetSetup'].update(bitstreamFile=str(c.TASK/'delivery-01/release/system_continuous.bit')))

    def test_wrong_core_rejected(self):
        self.reject_launch(lambda x:x['targetSetup']['downloadElf'][0].update(core='ps7_cortexa9_1'))

    def test_wrong_connection_rejected(self):
        self.reject_launch(lambda x:x['target'].update(targetConnectionId='other-board'))

    def test_missing_init_rejected(self):
        self.reject_launch(lambda x:x['targetSetup']['zynqInitialization']['usingPs7Init'].update(ps7InitTclFile='F:/missing/init.tcl'))

    def test_programming_disabled_rejected(self):
        self.reject_launch(lambda x:x['targetSetup'].update(programDevice=False))

    def test_duplicate_download_rejected(self):
        self.reject_launch(lambda x:x['targetSetup']['downloadElf'].append(copy.deepcopy(x['targetSetup']['downloadElf'][0])))

    def test_cpu_frequency_math(self):
        for seconds in (1,10,40):
            ticks=333333343*seconds
            self.assertEqual(ticks*1000000//(666666687//2),seconds*1000000)
            self.assertNotEqual(ticks*1000000//666666687//2,seconds*1000000)

    def test_compiler_config_difference_detected(self):
        original=c.POLICY['compile_command']
        norm=lambda s:c.normalize_command(s,Path(c.POLICY['reference_app']),Path(c.POLICY['reference_bsp']))
        for changed in (original.replace('-O2','-O0'),original+' -DCOUNTS_PER_SECOND=1',original.replace('-std=c11','-std=c99')):
            self.assertNotEqual(norm(original),norm(changed))

    def test_all_compiled_contract_fields_rejected_when_changed(self):
        data=(c.REFERENCE/'build/main.c.obj').read_bytes()
        contract=c.struct.pack('<16I',*c.CONTRACT)
        for index in range(16):
            with self.subTest(field=index):
                values=list(c.CONTRACT);values[index]^=1
                path=self.root/f'contract_{index}.o'
                path.write_bytes(data.replace(contract,c.struct.pack('<16I',*values)))
                with self.assertRaises(ValueError):
                    c.verify_elf(path,c.REFERENCE/'runtime/four_mic_continuous.elf')

    def test_changed_arithmetic_with_same_divisor_rejected(self):
        path=self.root/'arithmetic.elf'
        elf=c.Elf32(c.REFERENCE/'runtime/four_mic_continuous.elf',2)
        address,data=c.symbol(elf,'now_us')
        offset=elf.data.find(data)
        self.assertGreaterEqual(offset,0)
        changed=bytearray(elf.data);changed[offset+24]^=1
        path.write_bytes(changed)
        with self.assertRaises(ValueError):
            c.verify_elf(c.REFERENCE/'build/main.c.obj',path)


if __name__=='__main__':
    unittest.main()
