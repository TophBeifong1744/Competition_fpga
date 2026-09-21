"""Verify final run hashes, source bindings, markdown local links and narrow scope."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    a = p.parse_args()
    repo, here = a.repo.resolve(), Path(__file__).resolve().parent
    run = here/'evidence/run05'
    checked = 0
    for rel, expected in json.loads((run/'OUTPUT-SHA256.json').read_text()).items():
        assert sha(run/rel) == expected, rel
        checked += 1
    runner = json.loads((run/'runner.json').read_text())
    assert [x['exit_code'] for x in runner['commands']] == [0, 0, 0]
    for rel, expected in runner['source_sha256'].items():
        assert sha(here/rel) == expected, rel
    for rel, expected in json.loads((run/'checks/result.json').read_text())['source_sha256'].items():
        assert sha(repo/rel) == expected, rel
    links = 0
    for path in here.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):
                continue
            assert (path.parent/target.split('#')[0]).exists(), (path.name, target)
            links += 1
    # All tracked modifications, including staged edits, must be within this increment.
    changed = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=repo, text=True).splitlines()
    prefix = here.relative_to(repo).as_posix()+'/'
    assert all(path.startswith(prefix) for path in changed), changed
    result = dict(status='DELIVERY_CHECK_PASS', output_files=checked, local_links=links,
                  final_source_files=len(runner['source_sha256']), scope_prefix=prefix)
    with a.out.open('x', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
