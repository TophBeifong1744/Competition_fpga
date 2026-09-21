"""Check this work area's links and outputs without rerunning source algorithms."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path('F:/NUEC/review-worktrees/algorithm-closeout-20260923')
SHA = 'fe67547635ff254f9f91c7f917e8dedb6daf3363'
errors = []
links = []
for path in HERE.glob('*.md'):
    for label, target in re.findall(r'\[([^\]]+)\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
        if '://' in target:
            continue
        dest = (path.parent / target.split('#')[0]).resolve()
        links.append(dict(file=path.name, target=target, exists=dest.exists()))
        if not dest.exists():
            errors.append('broken link: '+target)
r = json.loads((HERE/'checks-02/result.json').read_text(encoding='utf-8'))
b = json.loads((HERE/'checks-02/budget.json').read_text(encoding='utf-8'))
assert r['commit'] == SHA and not r['errors'] and r['frozen_arrays'] == 120
assert not r['algorithms_executed'] and not r['old_tests_rerun']
assert b['total_wcet_cycles'] is None and b['actual_resources'] is None
assert b['historical_slot_sum_cycles'] == 103364 and b['listed_bytes'] == 107496
argv = ['git','-c','safe.directory='+ROOT.as_posix(),'-C',str(ROOT)]
env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
head = subprocess.check_output(argv+['rev-parse','HEAD'],env=env).decode().strip()
status = subprocess.check_output(argv+['status','--porcelain','--untracked-files=all'],env=env).decode()
assert head == SHA and status == r['source_status_before'] == ''
report = dict(status='PASS_DELIVERY_LINKS_AND_SCOPE' if not errors else 'FAIL',
              checked_markdown_links=len(links), links=links, errors=errors,
              source_head=head, source_status=status, algorithm_tests_run=False)
out = HERE/'delivery-check.json'
if out.exists():
    raise FileExistsError(out)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest = {str(p.relative_to(HERE)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(HERE.rglob('*')) if p.is_file() and p.name != 'WORK-SHA256.json'}
with (HERE/'WORK-SHA256.json').open('x',encoding='utf-8') as f:
    json.dump(manifest,f,ensure_ascii=False,indent=2)
    f.write('\n')
print(json.dumps(dict(status=report['status'], links=len(links), files=len(manifest), errors=errors)))
raise SystemExit(bool(errors))
