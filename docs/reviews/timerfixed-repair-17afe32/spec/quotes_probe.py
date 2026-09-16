"""Read-only host GCC argument tracing; -### never runs cc1/as/ld."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('--package', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--gcc', type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
(a.output / 'probe.c').write_text('/* argument tracing fixture: never compiled */\n')
(a.output / 'def').write_text('argument tracing fixture: never linked\n')
sys.path.insert(0, str(a.package))
import command_contract as c

forms = [
    '-DMSG="abc def"',
    '-DMSG="abc"" def"',
    '-DMSG="abc""" def"',
    '-DMSG="abc"""" def"',
    '-DMSG=abc""def',
    '-DMSG=abc"""def',
    '-DMSG="abc\\"def"',
    '-DMSG="abc\\\\"def"',
    '-DMSG="abc\\\\\\"def"',
    '-DMSG="abc def',
]
cases = []
for form in forms:
    raw = str(a.gcc) + ' -### -c probe.c ' + form
    r = subprocess.run(raw, executable=str(a.gcc), cwd=a.output, capture_output=True, text=True)
    parsed = c.command_argv(raw)
    collected = next((x for x in r.stderr.splitlines() if x.startswith('COLLECT_GCC_OPTIONS=')), '')
    cc1 = next((x for x in r.stderr.splitlines() if '/cc1.exe' in x), '')
    cases.append({'raw': raw, 'command_line_to_argv_w': parsed,
                  'returncode': r.returncode, 'collect_gcc_options': collected,
                  'cc1_printed_command': cc1, 'stderr': r.stderr})
(a.output / 'result.json').write_text(json.dumps({'boundary': 'Host GCC 8.1 MinGW -### only; not pinned ARM GCC 13.3', 'cases': cases}, indent=2))
for x in cases:
    print(json.dumps({k: v for k, v in x.items() if k in ('raw', 'command_line_to_argv_w', 'collect_gcc_options', 'returncode')}, ensure_ascii=False))
