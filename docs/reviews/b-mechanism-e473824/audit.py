"""Independent review: strict states, scoped float comparison, seals and fresh timeline."""
import argparse, collections, hashlib, importlib.util, json, math, pathlib, subprocess

p = argparse.ArgumentParser()
p.add_argument('--repo', type=pathlib.Path, required=True)
p.add_argument('--run', type=pathlib.Path, required=True)
p.add_argument('--out', type=pathlib.Path, required=True)
a = p.parse_args()
assert not a.out.exists()
root = a.repo / 'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918'
pkg = root / 'acoustic-mechanism-20260921'
load = lambda f: json.loads(f.read_text(encoding='utf-8-sig'))
seal = load(root / 'checkpoint-20260923/SNAPSHOT-SHA256.json')['files']
for rel, expected in seal.items():
    assert hashlib.sha256((root / rel).read_bytes()).hexdigest() == expected, rel
old = load(pkg / 'SNAPSHOT-before-mechanism.json')['files']
assert all(seal[k] == v for k, v in old.items())
stats = dict(float_differences=0, max_absolute_difference=0.0, strict_leaves=0)
allowed = {'angle', 'score', 'norm', 'residual'}
def compare(x, y, path=()):
    assert type(x) is type(y), (path, type(x), type(y))
    if isinstance(x, dict):
        assert x.keys() == y.keys(), path
        for k in x: compare(x[k], y[k], path + (k,))
    elif isinstance(x, list):
        assert len(x) == len(y), path
        for i, (u, v) in enumerate(zip(x, y)): compare(u, v, path + (i,))
    elif isinstance(x, float) and path[-1] in allowed:
        assert math.isfinite(x) and math.isfinite(y), path
        d = abs(x-y)
        assert math.isclose(x, y, abs_tol=1e-10, rel_tol=1e-12), (path, x, y)
        stats['float_differences'] += x != y
        stats['max_absolute_difference'] = max(stats['max_absolute_difference'], d)
    else:
        assert x == y, (path, x, y)
        stats['strict_leaves'] += 1
frames = load(a.run / 'full/frames.json')
compare(load(pkg / 'joint-full-replay/run01/frames.json'), frames)
compare(load(pkg / 'joint-full-replay/run01/result.json'), load(a.run / 'full/result.json'))
compare(load(pkg / 'joint-full-replay/run01/protocol.json'), load(a.run / 'full/protocol.json'))
spec = importlib.util.spec_from_file_location('breaks', pkg / 'acquisition-breaks/analyze.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
expected = load(a.run / 'breaks/result.json')
for capture in expected['captures']:
    rows = [r for r in frames if r['capture'] == capture['capture']]
    for branch in ('baseline', 'joint'):
        assert mod.analyze(rows, branch) == capture[branch], (capture['capture'], branch)
compare(load(pkg / 'acquisition-breaks/run01/result.json'), expected)
byte_results = {}
for name in ('frames.json', 'result.json', 'protocol.json'):
    f, g = pkg / 'joint-full-replay/run01' / name, a.run / 'full' / name
    byte_results[name] = dict(equal=f.read_bytes() == g.read_bytes(), author_sha256=hashlib.sha256(f.read_bytes()).hexdigest(), reviewer_sha256=hashlib.sha256(g.read_bytes()).hexdigest())
result = dict(status='PASS', sealed_files=len(seal), preserved_prior_entries=len(old), frames=len(frames), comparison=stats, bytes=byte_results, fresh_timeline_breaks_equal=True, totals=expected['totals'])
a.out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result, indent=2))
