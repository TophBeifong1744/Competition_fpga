"""Host-only guard fixtures, plus read-only rejection of the actual old E1 files."""
import copy,json,struct,sys,tempfile,unittest,shutil
from types import SimpleNamespace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import check_scene as g
class FakeElf:
    def __init__(self,addr=0x00120000,end=0x00b00000,size=9600128):
        self.entry=0x00100000;self.end=end
        self.symbols={'scene_archive':(0,addr,size,0,0,1)}
        self.sections=[None,(0,8,3,addr,0,size,0,0,64,0)]
        self.loads=[dict(start=0x00100000,end=end)]
        self.allocated=[dict(start=addr,end=addr+size)]
    def symbol_value(self,n):return self.end
class GuardTests(unittest.TestCase):
    def rejects(self,fn,*args):
        with self.assertRaises((ValueError,RuntimeError)):fn(*args)
    def test_01_current_contract(self):
        g.check_values(struct.pack('<16I',*g.CONTRACT),struct.pack('<11I',*g.PROFILE))
    def test_02_old_duration(self):
        self.rejects(g.check_values,struct.pack('<16I',*g.base.CONTRACT),struct.pack('<11I',*g.PROFILE))
    def test_03_each_buffer_field(self):
        for idx in range(1,16):
            with self.subTest(field=idx):
                v=list(g.CONTRACT);v[idx]+=1
                self.rejects(g.check_values,struct.pack('<16I',*v),struct.pack('<11I',*g.PROFILE))
    def test_04_each_scene_field(self):
        for idx in range(11):
            with self.subTest(field=idx):
                v=list(g.PROFILE);v[idx]+=1
                self.rejects(g.check_values,struct.pack('<16I',*g.CONTRACT),struct.pack('<11I',*v))
    def test_05_valid_ranges(self):g.check_ranges(FakeElf())
    def test_06_exact_program_limit(self):g.check_ranges(FakeElf(0x01000000-9600128,0x01000000))
    def test_07_overlap(self):self.rejects(g.check_ranges,FakeElf(0x01000000-9600128+64,0x01000000+64))
    def test_08_wrong_allocation(self):self.rejects(g.check_ranges,FakeElf(size=9600064))
    def test_09_unaligned(self):self.rejects(g.check_ranges,FakeElf(addr=0x00120004))
    def test_10_non_bss(self):
        e=FakeElf();s=list(e.sections[1]);s[1]=1;e.sections[1]=tuple(s)
        self.rejects(g.check_ranges,e)
    def test_11_commands(self):
        self.assertEqual(g.command_tokens('tool -O2 -Wl,-T'),['tool','-O2','-Wl,-T'])
        g.check_commands(g.POLICY['compile_command'],g.POLICY['ninja_commands'])
    def test_12_linker_injections(self):
        for option in ('-e,main','--defsym,COUNTS_PER_SECOND=333333','--wrap,main'):
            with self.subTest(option=option):
                s=g.POLICY['ninja_commands'].replace('lscript.ld"','lscript.ld",'+option,1)
                self.assertNotEqual(s,g.POLICY['ninja_commands'])
                self.rejects(g.check_commands,g.POLICY['compile_command'],s)
    def test_13_options_case(self):
        self.rejects(g.check_commands,g.POLICY['compile_command'].replace('-O2','-o2'),g.POLICY['ninja_commands'])
    def test_14_old_gate(self):
        self.rejects(g.check_commands,g.POLICY['compile_command'],g.POLICY['ninja_commands'].replace('check_scene.py','check_endurance.py'))
    def test_15_wrong_elf_path(self):
        self.rejects(g.check_commands,g.POLICY['compile_command'],g.POLICY['ninja_commands'].replace('-o four_mic_endurance.elf','-o wrong.elf'))
    def test_16_old_object_elf(self):
        old=g.DEPENDENCIES/'endurance-test-01/evidence/user-build-20260916-2052'
        self.rejects(g.compiled,old/'app/build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj',old/'app/build/four_mic_endurance.elf')
    def test_17_candidate_sources_and_old_timer(self):
        with tempfile.TemporaryDirectory(prefix='scene_gate_') as td:
            p=Path(td);shutil.copytree(g.HERE/'proposed-src',p/'src')
            src=p/'src';actual=Path('F:/College/verilog_digital_system/Vitis/four_mic_endurance/src')
            for name in ('UserConfig.cmake','lscript.ld','Empty_applicationExample.cmake'):
                shutil.copyfile(actual/name,src/name)
            g.source_check(src)
            f=src/'continuous/main_continuous.c'
            f.write_text(f.read_text().replace('/ (COUNTS_PER_SECOND)','/ (COUNTS_PER_SECOND / 1000000U)'),encoding='utf-8')
            self.rejects(g.source_check,src)
    def test_18_frozen_old_app_rejected(self):
        # The user has now installed S1; the E1 rejection fixture must stay E1.
        old=g.DEPENDENCIES/'endurance-test-01/evidence/user-build-20260916-2052/app/src'
        self.rejects(g.source_check,old)
    def test_19_reused_real_timer(self):
        old=g.base.REFERENCE
        a=g.timer_layout.inspect(g.base.Elf32(old/'build/main.c.obj',1),1)
        b=g.timer_layout.inspect(g.base.Elf32(old/'runtime/four_mic_continuous.elf',2),2)
        self.assertEqual(a[0],b[0]);self.assertEqual(b[1]['divisor'],333333343)
    def test_20_wrong_divisor_real_object_mutation(self):
        old=g.base.REFERENCE/'build/main.c.obj'
        with tempfile.TemporaryDirectory(prefix='scene_timer_') as td:
            parsed=g.base.Elf32(old,1);sym=g.timer_layout.entry(parsed,'now_us')
            section=parsed.sections[sym[5]]
            _,details=g.timer_layout.inspect(parsed,1)
            offset=section[4]+sym[1]-section[3]+details['pool_offset']
            data=bytearray(old.read_bytes())
            self.assertEqual(struct.unpack_from('<Q',data,offset)[0],333333343)
            struct.pack_into('<Q',data,offset,333333)
            p=Path(td)/'bad.o';p.write_bytes(data)
            self.rejects(g.timer_layout.inspect,g.base.Elf32(p,1),1)
    def test_21_candidate_preflight_fixture_with_real_dependencies(self):
        with tempfile.TemporaryDirectory(prefix='scene_pre_') as td:
            app=Path(td)/'four_mic_endurance';app.mkdir()
            shutil.copytree(g.HERE/'proposed-src',app/'src')
            actual=Path('F:/College/verilog_digital_system/Vitis/four_mic_endurance')
            for name in ('UserConfig.cmake','lscript.ld','Empty_applicationExample.cmake'):
                shutil.copyfile(actual/'src'/name,app/'src'/name)
            shutil.copyfile(actual/'vitis-comp.json',app/'vitis-comp.json')
            args=SimpleNamespace(app=str(app),stage='pre',
                platform='F:/College/verilog_digital_system/Vitis/continuous_platform',
                tools_bin='F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin',
                record_root=str(Path(td)/'records'))
            report=g.verify(args,Path(td))
            self.assertEqual(report['bsp_files'],88)
            self.assertEqual(report['board_test'],'NOT_RUN')
    def test_22_actual_swapped_commands(self):
        p=g.HERE/'command-order-fix-01/before-fix/app/scene_checks/20260917_150013_post_f0ac8be96d/generated-commands.log'
        g.check_commands(g.POLICY['compile_command'],p.read_text())
    def test_23_swapped_prerequisites_only(self):
        rows=g.POLICY['ninja_commands'].splitlines()
        rows[0],rows[1]=rows[1],rows[0]
        g.check_commands(g.POLICY['compile_command'],'\n'.join(rows))
    def test_24_missing_duplicate_extra_prerequisite(self):
        rows=g.POLICY['ninja_commands'].splitlines()
        for altered in (rows[1:], [rows[0],rows[0],*rows[2:]], [*rows,rows[0]]):
            with self.subTest(lines=len(altered)):
                self.rejects(g.check_commands,g.POLICY['compile_command'],'\n'.join(altered))
    def test_25_auxiliary_command_modified(self):
        rows=g.POLICY['ninja_commands'].splitlines()
        for i in (0,1):
            altered=list(rows);altered[i]+=' && extra_command'
            self.rejects(g.check_commands,g.POLICY['compile_command'],'\n'.join(altered))
    def test_26_compile_link_reordering_rejected(self):
        rows=g.POLICY['ninja_commands'].splitlines()
        rows[2],rows[3]=rows[3],rows[2]
        self.rejects(g.check_commands,g.POLICY['compile_command'],'\n'.join(rows))
    def test_27_link_injection_after_auxiliary_swap(self):
        rows=g.POLICY['ninja_commands'].splitlines()
        rows[0],rows[1]=rows[1],rows[0]
        for flag in ('-e,main','--defsym,X=0','--wrap,main'):
            altered=list(rows);altered[3]=altered[3].replace('lscript.ld"','lscript.ld",'+flag,1)
            self.rejects(g.check_commands,g.POLICY['compile_command'],'\n'.join(altered))
    def test_28_real_build_graph(self):
        p=g.HERE/'command-order-fix-01/before-fix/app/build/build.ninja'
        self.assertTrue(g.check_build_graph(p.read_text())['source_guard_before_compile'])
    def test_29_removed_or_duplicated_guard_dependency(self):
        text=(g.HERE/'command-order-fix-01/before-fix/app/build/build.ninja').read_text()
        for old,new in (('phony || print_build_info s1_source_guard','phony || print_build_info'),
                        ('phony || print_build_info s1_source_guard','phony || print_build_info s1_source_guard s1_source_guard'),
                        ('|| cmake_object_order_depends_target_four_mic_endurance.elf','|| print_build_info')):
            altered=text.replace(old,new,1);self.assertNotEqual(altered,text)
            self.rejects(g.check_build_graph,altered)
if __name__=='__main__':unittest.main(verbosity=2)
