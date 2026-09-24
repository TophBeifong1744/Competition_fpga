"""Independent, bounded S1 artifact-checker regression; no build or board calls.

Windows/Python 3.11+, standard library. The offline mode needs only this Git
checkout, not the author's F: tools/application. Every mutation stays in a new
codex_out directory. This is checker evidence, never RTL simulation evidence.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import traceback

sys.dont_write_bytecode = True
ENTRY = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('s1_candidate', ENTRY / 'check_load.py')
g = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(g)
FROZEN_IMPLEMENTATION = '9407acdf3cd4e9f14a1779bb0b3d2baf9714c60e413b35f4eb6299cfc71217c1'
S1_ELF_SHA = '4b7823bdefa3776a910a3359b5851fa52c6f4ce89432cc3ee0072dee52ca06a6'
S1_OBJECT_SHA = '3fd07ea3b80a955c660291e4a38fbee2ca022bb10088f725dedea487ba4bc150'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


class ElfMutation:
    """Test-only ELF offsets from the ELF32 file structure, not DUT helpers.

    This locator only edits existing real artifacts. It is not a reference
    execution model. Expected values below come from the frozen S1 contract.
    """
    def __init__(self, path):
        self.raw = bytearray(path.read_bytes())
        assert self.raw[:7] == b'\x7fELF\x01\x01\x01'
        self.h = struct.unpack_from('<HHIIIIIHHHHHH', self.raw, 16)
        self.sections = [struct.unpack_from('<10I', self.raw, self.h[5] + 40*i)
                         for i in range(self.h[11])]
        self.symbols = {}
        for section in self.sections:
            if section[1] != 2:
                continue
            strings = self.sections[section[6]]
            for offset in range(section[4], section[4] + section[5], 16):
                sym = struct.unpack_from('<IIIBBH', self.raw, offset)
                if not sym[5]:
                    continue
                start = strings[4] + sym[0]
                end = self.raw.index(0, start)
                self.symbols[bytes(self.raw[start:end]).decode()] = (sym, offset)

    def symbol_file_offset(self, name):
        sym, _ = self.symbols[name]
        section = self.sections[sym[5]]
        return section[4] + (sym[1] & ~1) - section[3]

    def timer_divisor_offset(self):
        sym, _ = self.symbols['now_us']
        start = self.symbol_file_offset('now_us')
        body = self.raw[start:start + sym[2]]
        needle = struct.pack('<Q', 333333343)
        assert body.count(needle) == 1, 'Independent timer mutation locator ambiguous'
        return start + body.index(needle)

    def executable_phdr(self):
        found = []
        for i in range(self.h[9]):
            off = self.h[4] + i*self.h[8]
            ph = struct.unpack_from('<8I', self.raw, off)
            if ph[0] == 1 and ph[6] & 1 and ph[2] <= 0x100000 < ph[2] + ph[4]:
                found.append((off, ph))
        assert len(found) == 1
        return found[0]


class Runner:
    def __init__(self, out):
        self.out, self.cases = out, []

    def case(self, name, requirement, fn, error=None, exception=ValueError,
             scope='OFFLINE_BOUNDARY'):
        row = dict(id=name, requirement=requirement, scope=scope,
                   expected='ACCEPT' if error is None else 'REJECT', expected_error=error)
        try:
            fn()
            if error is not None:
                raise AssertionError('Negative was accepted')
            row.update(outcome='MATCHED', observed='ACCEPT')
        except Exception as exc:
            row.update(observed=type(exc).__name__, observed_error=str(exc))
            if error is not None and isinstance(exc, exception) and re.search(error, str(exc)):
                row['outcome'] = 'MATCHED'
            else:
                row.update(outcome='FAIL', classification=('TOOL_ENV_FAIL' if isinstance(exc, OSError)
                                                         else 'ASSERTION_FAIL'),
                           traceback=traceback.format_exc())
        self.cases.append(row)
        print(row['outcome'], name, row.get('observed_error', ''))

    def mutation(self, name, original, edit):
        item = ElfMutation(original)
        edit(item)
        assert item.raw != original.read_bytes(), 'Mutation made no change'
        path = self.out / (name + original.suffix)
        path.write_bytes(item.raw)
        return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, help='New directory beneath checkout/codex_out')
    parser.add_argument('--live', action='store_true', help='Also check author-only wrong-platform path')
    args = parser.parse_args()
    out = Path(args.out).resolve()
    assert not out.exists() and (g.REPO / 'codex_out').resolve() in out.parents
    out.mkdir(parents=True)
    save(out / 'request.json', dict(argv=sys.argv, cwd=os.getcwd(), python=sys.version,
                                  platform=sys.platform, seed=None, deterministic=True,
                                  implementation_sha256=sha(ENTRY / 'check_load.py'),
                                  test_sha256=sha(Path(__file__))))
    run = Runner(out)
    try:
        assert sha(ENTRY / 'check_load.py') == FROZEN_IMPLEMENTATION, 'Implementation checkpoint changed'
        assert os.name == 'nt', 'Pinned command parser requires Windows'
        policy = json.loads((ENTRY / 'DEPENDENCIES.json').read_text())
        # Only unit-fixture installed-root relocation: production policy remains
        # unchanged. This exercises BOTH identical closures without A's E: path.
        offline = copy.deepcopy(policy)
        offline['installed_task_root'] = str(g.TASK)
        scene, base, contract = g.dependencies(g.Inputs(), offline)
        run.case('dependency_closure_positive', 'R2',
                 lambda: g.dependencies(g.Inputs(), offline))
        elf = g.SCENE / 'delivery-01/versions/build/four_mic_endurance.elf'
        object_root = g.SCENE / 'command-order-fix-01/before-fix'
        obj = object_root / 'app/build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj'
        manifest = json.loads((object_root / 'SHA256.json').read_text())
        assert manifest['files']['app/build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj'] == S1_OBJECT_SHA
        assert sha(elf) == S1_ELF_SHA and sha(obj) == S1_OBJECT_SHA
        save(out / 'inputs.json', dict(dependencies=policy['dependency_sha256'],
              offline_installed_root_relocation=str(g.TASK),
              fixture_object=dict(path=str(obj), sha256=sha(obj), note='Earlier real S1 object; checker fixture only'),
              fixture_elf=dict(path=str(elf), sha256=sha(elf), reference_commit=policy['startup_reference_commit']),
              production_object='0cb797800bb2f9791d35fa4c81bd995db6696513b0540d959c2e5e2614cabdc2',
              same_build_claim=False))

        # Missing/replaced transitive code must fail BEFORE any import can run.
        dependency_root = out / 'dependency-fixture'
        for relative in policy['dependency_sha256']:
            target = dependency_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(g.TASK / relative, target)
        def dependency_case(kind, relative):
            modified = copy.deepcopy(offline)
            modified['installed_task_root'] = str(dependency_root)
            path = dependency_root / relative
            data = path.read_bytes()
            before = {name: sys.modules.get(name) for name in g.MODULES}
            try:
                if kind == 'missing':
                    path.unlink()
                elif kind == 'replaced':
                    path.write_bytes(b'raise RuntimeError("UNPINNED CODE EXECUTED")\n')
                elif kind == 'omitted_pin':
                    del modified['dependency_sha256'][relative]
                g.dependencies(g.Inputs(), modified)
            finally:
                path.write_bytes(data)
                assert all(sys.modules.get(name) is module for name, module in before.items()), 'Import ran before rejection'

        for label, relative in (('command_contract', g.C1 + 'command_contract.py'),
                                ('startup_reference', g.S1 + 'delivery-01/versions/build/four_mic_endurance.elf')):
            for kind in ('missing', 'replaced', 'omitted_pin'):
                pattern = ('No such file or directory: .*' + re.escape(Path(relative).name) if kind == 'missing' else
                           'Dependency/input mismatch:' if kind == 'replaced' else
                           'Incomplete/unexpected dependency closure')
                run.case(label + '_' + kind, 'R2', lambda k=kind,r=relative: dependency_case(k,r),
                         pattern, FileNotFoundError if kind == 'missing' else ValueError)

        def valid_compiled():
            result = g.compiled(scene, base, obj, elf)
            assert result['divisor'] == 333333343
            assert result['scene'] == [0x53434e31,1,6000000,288000,300000,9600000,64,2,32,48000,2000000]
            assert result['contract'][14:] == [6000000,288000]
            assert result['startup'] == dict(entry=0x100000,symbol='_vector_table',executable_file_backed=True)
            assert result['archive_start'] % 64 == 0 and result['archive_end'] <= 0x01000000
        run.case('archived_s1_composed_compiled', 'R1,R4', valid_compiled)

        def word(item, offset, value):
            struct.pack_into('<I', item.raw, offset, value)
        mutations = [
            ('entry_reserved_rx', lambda x: word(x,24,0x01000000), 'ELF entry differs from fixed vector start'),
            ('entry_thumb_mode', lambda x: word(x,24,0x00100001), 'ELF entry differs from fixed vector start'),
            ('entry_no_file_bytes', lambda x: word(x,x.executable_phdr()[0]+16,0), 'Entry not in exactly one executable file-backed PT_LOAD'),
            ('entry_not_executable', lambda x: word(x,x.executable_phdr()[0]+24,6), 'Entry not in exactly one executable file-backed PT_LOAD'),
            ('vector_symbol_changed', lambda x: word(x,x.symbols['_vector_table'][1]+4,0x100004), 'Entry differs from _vector_table'),
            ('boot_symbol_changed', lambda x: word(x,x.symbols['_boot'][1]+4,0x1000d0), 'Startup _boot changed'),
            ('startup_vector_bytes', lambda x: word(x,x.symbol_file_offset('_vector_table'),0xeafffffe), 'Startup vector/reset bytes changed'),
            ('startup_reset_bytes', lambda x: word(x,x.symbol_file_offset('_boot'),0xeafffffe), 'Startup vector/reset bytes changed'),
            ('old_timer_divisor', lambda x: struct.pack_into('<Q',x.raw,x.timer_divisor_offset(),333333), 'Wrong actual timer divisor'),
            ('old_10s_duration', lambda x: word(x,x.symbol_file_offset('continuous_contract')+14*4,10000000), 'Object/ELF continuous contract mismatch'),
            ('wrong_archive_capacity', lambda x: word(x,x.symbol_file_offset('scene_contract')+4*4,300001), 'Object/ELF S1 archive contract mismatch'),
            ('archive_size_changed', lambda x: word(x,x.symbols['scene_archive'][1]+8,9600064), 'Missing/wrong archive allocation size'),
            ('program_overlaps_rx', lambda x: word(x,x.symbols['end'][1]+4,0x01000001), 'Program/static archive/heap/stack overlaps RX or leaves program DDR'),
        ]
        for name, edit, error in mutations:
            mutant = run.mutation(name, elf, edit)
            run.case(name, 'R4' if name.startswith(('entry','vector','boot','startup')) else 'R1',
                     lambda p=mutant: g.compiled(scene,base,obj,p), error)
        mutant = run.mutation('object_old_timer_divisor', obj,
                             lambda x: struct.pack_into('<Q',x.raw,x.timer_divisor_offset(),333333))
        run.case('object_old_timer_divisor','R1',lambda:g.compiled(scene,base,mutant,elf),'Wrong actual timer divisor')

        app = Path(policy['app'])
        bsp = Path(policy['platform']) / 'export/continuous_platform/sw/standalone_ps7_cortexa9_0'
        cc, ninja = scene.POLICY['compile_command'], scene.POLICY['ninja_commands']
        rows = ninja.splitlines()
        call_commands = lambda c,n: g.commands(scene,contract,c,n,app,bsp)
        run.case('frozen_commands','R3',lambda:call_commands(cc,ninja))
        run.case('only_auxiliary_swap','R3',lambda:call_commands(cc,'\n'.join([rows[1],rows[0],*rows[2:]])))
        for name, changed in (('missing_command', rows[1:]),('extra_command',rows+[rows[0]]),
                              ('duplicate_prerequisite',[rows[0],rows[0],*rows[2:]]),
                              ('compile_link_reordered',[*rows[:2],rows[3],rows[2]])):
            run.case(name,'R3',lambda c=changed:call_commands(cc,'\n'.join(c)),
                     'Generated command count mismatch' if name in ('missing_command','extra_command') else 'Generated commands/linker subarguments or gate mismatch')
        for name, old, new in (('compiler_case','-O2','-o2'),('macro_value','-DSDT','-DSDT=1'),
                              ('compiler_extra',' -O2 ',' -O2 -funroll-loops ')):
            changed=cc.replace(old,new)
            assert changed != cc
            run.case(name,'R3',lambda c=changed:call_commands(c,ninja),'Compiler options or path differs')
        for option in ('-e,main','--defsym,COUNTS_PER_SECOND=333333','--wrap,main','-L,/../lscript.ld'):
            changed=list(rows)
            changed[3]=changed[3].replace('lscript.ld"','lscript.ld",'+option,1)
            assert changed != rows
            run.case('linker_injection_'+option.split(',')[0],'R3',lambda c=changed:call_commands(cc,'\n'.join(c)),
                     'Generated commands/linker subarguments or gate mismatch')
            # Also exercise the approved transitive parser directly: the full
            # S1 envelope rejects first and must not conceal this regression.
            link=contract.link_command('\n'.join(changed))
            run.case('parser_injection_'+option.split(',')[0],'R3',
                     lambda c=link:contract.normalize_command(c,app,bsp),
                     'Expected one absolute -Wl script path, no extra subarguments')
        changed=list(rows);changed[0]+=' && injected_command'
        run.case('gate_command_modified','R3',lambda:call_commands(cc,'\n'.join(changed)),
                 'Generated commands/linker subarguments or gate mismatch')

        # Path checks use real archived launch JSON relocated via its official
        # workspace token. Tiny placeholders prove PATH checks only, not bytes.
        fixture_app=out/'launch-fixture'/'four_mic_endurance'
        launch=fixture_app/'_ide/launch.json'; launch.parent.mkdir(parents=True)
        launch_data=json.loads((g.SCENE/'delivery-01/versions/_ide/launch.json').read_text())
        for relative in ('build/four_mic_endurance.elf','_ide/bitstream/system_continuous_20260915.bit','_ide/psinit/ps7_init.tcl','wrong.elf','wrong.bit'):
            path=fixture_app/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'PATH-ONLY-TEST-FIXTURE')
        launch.write_text(json.dumps(launch_data))
        run.case('archived_launch_paths','R5',lambda:base.launch_paths(fixture_app,fixture_app.parent),scope='OFFLINE_PATH_ONLY')
        for kind in ('elf','bit'):
            altered=copy.deepcopy(launch_data);t=altered['configurations'][0]['targetSetup']
            if kind=='elf':t['downloadElf'][0]['elfFile']=str(fixture_app/'wrong.elf')
            else:t['bitstreamFile']=str(fixture_app/'wrong.bit')
            def reject_launch(value=altered):
                launch.write_text(json.dumps(value))
                try:return base.launch_paths(fixture_app,fixture_app.parent)
                finally:launch.write_text(json.dumps(launch_data))
            run.case('wrong_'+kind+'_launch_path','R5',reject_launch,'Run points to wrong/old artifact path',scope='OFFLINE_PATH_ONLY')
        for name, expected in (('bit',base.POLICY['hardware_sha256']['system_continuous_20260915.bit']),
                               ('xsa',base.POLICY['hardware_sha256']['system_continuous_20260915.xsa'])):
            bad=out/('wrong.'+name);bad.write_bytes(b'INTENTIONALLY-WRONG-'+name.encode())
            run.case('wrong_'+name+'_bytes','R5',lambda p=bad,e=expected:g.Inputs().file(p,e),
                     'Dependency/input mismatch:',scope='OFFLINE_IDENTITY_ONLY')
        tracked=out/'input-race.bin';tracked.write_bytes(b'before')
        tracked_inputs=g.Inputs();tracked_inputs.file(tracked);tracked.write_bytes(b'after')
        run.case('input_changed_after_check','R6',tracked_inputs.unchanged,'Input changed during preflight:')
        if args.live:
            from types import SimpleNamespace
            case_out=out/'wrong-platform';case_out.mkdir()
            arguments=SimpleNamespace(app=policy['app'],platform=policy['platform']+'-wrong',tools_bin='',stage='load')
            run.case('wrong_platform_path','R5',lambda:g.verify(arguments,case_out),'Wrong app/platform path',scope='LIVE_EARLY_REJECTION')
    except Exception as exc:
        run.cases.append(dict(id='environment_or_fixture_setup',outcome='FAIL',classification='TOOL_ENV_FAIL',
                              observed_error=str(exc),traceback=traceback.format_exc()))
    failed=[row for row in run.cases if row['outcome']!='MATCHED']
    result=dict(status='CHECKER_CASES_MATCHED_PENDING_REVIEW' if not failed else 'INCONCLUSIVE',
                claim_stage='PREFLIGHT',implementation_checkpoint='7e9352a94f59c442f715997e8d95785913eac301',
                implementation_sha256=sha(ENTRY/'check_load.py'),test_sha256=sha(Path(__file__)),
                cases=run.cases,total=len(run.cases),matched=len(run.cases)-len(failed),failures=len(failed),
                live_full_load='REUSED_NOT_RERUN',board_test='NOT_RUN',build='NOT_RUN',rtl_simulation='NOT_RUN',
                independent_signoff='PENDING_B_REVIEW',seed=None)
    save(out/'result.json',result)
    print(result['status'],len(run.cases)-len(failed),'/',len(run.cases),str(out))
    return bool(failed)


if __name__=='__main__':
    sys.exit(main())
