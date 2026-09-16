import importlib.util
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import check_endurance as gate

class GateTests(unittest.TestCase):
    def test_legal_bytes(self):
        gate.check_contract_bytes(struct.pack('<10I',*gate.PROFILE),struct.pack('<22I',*gate.SCHEDULE))
    def test_each_profile_field_rejected(self):
        for index in range(10):
            with self.subTest(index=index):
                values=list(gate.PROFILE);values[index]^=1
                with self.assertRaises(ValueError):gate.check_contract_bytes(struct.pack('<10I',*values),struct.pack('<22I',*gate.SCHEDULE))
    def test_each_schedule_field_rejected(self):
        for index in range(22):
            with self.subTest(index=index):
                values=list(gate.SCHEDULE);values[index]^=1
                with self.assertRaises(ValueError):gate.check_contract_bytes(struct.pack('<10I',*gate.PROFILE),struct.pack('<22I',*values))
    def test_old_two_segment_profile_rejected(self):
        with self.assertRaises(ValueError):gate.check_contract_bytes(struct.pack('<16I',*gate.base.CONTRACT),b'')
    def test_real_fixed_old_elf_not_new_profile(self):
        r=gate.base.REFERENCE
        with self.assertRaisesRegex(ValueError,'endurance_contract'):
            gate.compiled(r/'build/main.c.obj',r/'runtime/four_mic_continuous.elf')
    def test_source_and_config_binding(self):
        with tempfile.TemporaryDirectory(prefix='e1_gate_') as folder:
            src=Path(folder)
            for name in gate.POLICY['source_text_sha256']:
                original=HERE/'proposed-src'/name
                if not original.exists():original=gate.base.REFERENCE/'ps'/name
                target=src/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original,target)
            cmake=src/'CMakeLists.txt';cmake.write_text(gate.expected_cmake(),encoding='utf-8')
            gate.source_check(src)
            config=src/'UserConfig.cmake';saved=config.read_bytes()
            config.write_text(config.read_text().replace('"main.c"','"continuous/continuous_core.c"\n"main.c"'))
            with self.assertRaisesRegex(ValueError,'UserConfig'):gate.source_check(src)
            config.write_bytes(saved)
            code=src/'continuous/main_continuous.c';saved=code.read_bytes()
            code.write_text(code.read_text().replace('/ (COUNTS_PER_SECOND)','/ COUNTS_PER_SECOND'))
            with self.assertRaisesRegex(ValueError,'main_continuous'):gate.source_check(src)
            code.write_bytes(saved)
            (src/'shadow.h').write_text('#define RUN_US 1\n')
            with self.assertRaisesRegex(ValueError,'Unexpected'):gate.source_check(src)
    def test_old_hook_rejected(self):
        self.assertIn('E1 ENDURANCE',gate.hook())
        self.assertNotIn('C1 TIMERFIX',gate.expected_cmake())
        self.assertIn('set(APP_NAME four_mic_endurance)',gate.expected_cmake())

if __name__=='__main__':unittest.main(verbosity=2)
