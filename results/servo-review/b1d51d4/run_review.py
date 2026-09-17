"""Pinned, non-mutating servo review; new output paths only."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import time

p = argparse.ArgumentParser()
p.add_argument('--worktree', required=True)
p.add_argument('--output', required=True)
p.add_argument('--mode', choices=['author', 'independent', 'faults'], default='author')
a = p.parse_args()
root = Path(a.worktree).resolve()
out = Path(a.output).resolve()
out.mkdir(parents=True, exist_ok=False)
bin_dir = Path('F:/AMD/2025.2/Vivado/bin')
records = []

def run(name, command, cwd, expected=0):
    started = time.time()
    proc = subprocess.run(command, cwd=cwd, capture_output=True, timeout=600)
    (out / (name + '.stdout.txt')).write_bytes(proc.stdout)
    (out / (name + '.stderr.txt')).write_bytes(proc.stderr)
    rec = dict(name=name, command=command, cwd=str(cwd), exit_code=proc.returncode,
               expected_exit=expected, elapsed_seconds=round(time.time()-started, 3))
    records.append(rec)
    (out / 'commands.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    print(json.dumps(rec), flush=True)
    return proc

def ps(script, name, expected=0):
    return run(name, ['pwsh.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script], root, expected)

pin = run('identity', ['git', '-c', f'safe.directory={root.as_posix()}', 'rev-parse', 'HEAD'], root)
assert pin.stdout.decode().strip() == 'b1d51d44aa2c055a145b832b7c272fd33b7d0395'
run('clean-before', ['git', '-c', f'safe.directory={root.as_posix()}', 'status', '--porcelain'], root)
ps(f"& '{bin_dir}/vivado.bat' -version; exit $LASTEXITCODE", 'version')
if a.mode == 'author':
    for freq in (100000000, 1000000, 1500000):
        build = out / f'build-{freq}'
        script = f"& './task-packages/PKG-SERVO-PWM/scripts/run_xsim.ps1' -VivadoBin '{bin_dir}' -ClockHz {freq} -OutputDirectory '{build}'; if (-not $?) {{ exit 1 }}"
        proc = ps(script, f'author-{freq}', 1 if freq == 1500000 else 0)
        if freq != 1500000:
            assert proc.returncode == 0, 'Author test failed; inspect raw logs'
            assert b'PASS motor_drive checks=39' in proc.stdout
    target = out / 'build-1000000'
    before = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in target.glob('*.log')}
    proc = ps(f"& './task-packages/PKG-SERVO-PWM/scripts/run_xsim.ps1' -VivadoBin '{bin_dir}' -ClockHz 1000000 -OutputDirectory '{target}'; if (-not $?) {{ exit 1 }}", 'existing-directory', 1)
    after = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in target.glob('*.log')}
    assert proc.returncode != 0 and before == after
    (out/'directory-protection.json').write_text(json.dumps(dict(before=before, after=after, unchanged=before==after), indent=2))
elif a.mode == 'faults':
    source = root / 'task-packages/PKG-SERVO-PWM'
    for fault in ('width', 'no-output', 'compile-error'):
        fixture = out / fault / 'task-packages/PKG-SERVO-PWM'
        shutil.copytree(source, fixture)
        target = fixture / 'rtl/motor_drive.v'
        code = target.read_text(encoding='utf-8')
        if fault == 'width':
            code = code.replace("16'd500 + pulse_offset_us", "16'd501 + pulse_offset_us")
        elif fault == 'no-output':
            code = code.replace("pwm_o                 <= 1'b1;", "pwm_o                 <= 1'b0;")
            code = code.replace("pwm_o <= ((period_us_cnt + 1'b1) < active_pulse_width_us);", "pwm_o <= 1'b0;")
        else:
            code += '\nTHIS_IS_AN_INTENTIONAL_SYNTAX_ERROR\n'
        target.write_text(code, encoding='utf-8')
        proc = ps(f"& '{fixture}/scripts/run_xsim.ps1' -VivadoBin '{bin_dir}' -ClockHz 1000000 -OutputDirectory '{out/fault/'build'}'; if (-not $?) {{ exit 1 }}", fault, 1)
        assert proc.returncode != 0
        text = (proc.stdout + proc.stderr).decode('utf-8', errors='replace')
        assert {'width':'pulse width', 'no-output':'watchdog timeout', 'compile-error':'xvlog failed'}[fault] in text
else:
    tb = Path(__file__).with_name('tb_independent.sv')
    rtl = root / 'task-packages/PKG-SERVO-PWM/rtl/motor_drive.v'
    for freq in (1000000, 3000000):
        build = out / f'build-{freq}'
        build.mkdir()
        commands = [('compile', f"& '{bin_dir}/xvlog.bat' --sv '{rtl}' '{tb}'; exit $LASTEXITCODE"),
                    ('elaborate', f"& '{bin_dir}/xelab.bat' tb_independent -generic_top '\"CLK_FREQ_HZ={freq}\"' -s independent; exit $LASTEXITCODE"),
                    ('simulate', f"& '{bin_dir}/xsim.bat' independent -runall -log simulation.log; exit $LASTEXITCODE")]
        for stage, command in commands:
            proc = run(f'{freq}-{stage}', ['pwsh.exe','-NoProfile','-Command',command],build)
            assert proc.returncode == 0
        assert b'PASS independent' in proc.stdout and b'Fatal:' not in proc.stdout
print('REVIEW RUN COMPLETE', flush=True)
