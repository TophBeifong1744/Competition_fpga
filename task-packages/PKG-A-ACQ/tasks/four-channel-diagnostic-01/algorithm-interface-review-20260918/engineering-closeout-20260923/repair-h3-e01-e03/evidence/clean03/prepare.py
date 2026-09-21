"""Export exact Git blobs to a NEW standalone directory; never reads sibling work files."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

BASE = 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/'
PINS = {'engineering': '0abdc91c57787b7c868a797b88f35129de169faf',
        'logic': 'f879a54cf40359209895af955bcef92accdf79ea',
        'review': '02f4ec23d771bd33a04ae3f297178ca34d537eb8'}


def prepare(repo, output):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError('REFUSE_OVERWRITE')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE)
    # Fail before creating output if any object is missing. No branch fallback.
    for sha in PINS.values():
        git('cat-file', '-e', sha+'^{commit}')
    selected = [('engineering', BASE+'engineering-closeout-20260923/'),
                ('logic', BASE+'increment-20260923/'),
                ('review', 'docs/reviews/a-h3-two-20260921/')]
    pending = []
    for name, prefix in selected:
        for path in git('ls-tree', '-r', '--name-only', PINS[name], '--', prefix).decode().splitlines():
            rel = Path('pinned')/name/path[len(prefix):]
            if '..' in rel.parts or rel.is_absolute():
                raise ValueError('UNSAFE_PATH')
            data = git('show', PINS[name]+':'+path)
            blob = git('rev-parse', PINS[name]+':'+path).decode().strip()
            pending.append((rel, data, dict(commit=PINS[name], path=path, blob=blob)))
    output.mkdir(parents=True)
    rows = []
    for rel, data, binding in pending:
        target = output/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        rows.append(dict(file=rel.as_posix(), sha256=hashlib.sha256(data).hexdigest(), **binding))
    for name in ('results.py', 'run_checks.py', 'prepare.py'):
        data = Path(__file__).with_name(name).read_bytes()
        (output/name).write_bytes(data)
        rows.append(dict(file=name, sha256=hashlib.sha256(data).hexdigest(), kind='uncommitted_repair'))
    (output/'bindings.json').write_text(json.dumps(rows, indent=2)+'\n', encoding='utf-8')
    print('PREPARED_EXACT_OBJECTS', output, len(rows))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--repo', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    prepare(a.repo, a.out)
