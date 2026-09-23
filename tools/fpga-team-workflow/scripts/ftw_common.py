"""Shared deterministic I/O. No shell evaluation or implicit network writes."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import yaml

sys.dont_write_bytecode = True
PACKAGE = Path(__file__).resolve().parents[1]

class Refusal(ValueError):
    pass

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()

def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def read(path):
    data = yaml.safe_load(Path(path).read_text(encoding='utf-8-sig'))
    if not isinstance(data, (dict, list)):
        raise Refusal(f'Expected mapping or list: {path}')
    return data

def require_schema(data, version=1):
    if not isinstance(data, dict) or data.get('schema_version') != version:
        raise Refusal('Unsupported or missing schema_version')

def no_links(path):
    """Reject reparse points in every existing path component, including ancestors."""
    p = Path(os.path.abspath(path))
    for item in [p, *p.parents]:
        try:
            st = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(st.st_mode) or getattr(st, 'st_file_attributes', 0) & 0x400:
            raise Refusal(f'Link/reparse point is not supported: {item}')
        if stat.S_ISREG(st.st_mode) and st.st_nlink > 1:
            raise Refusal(f'Writable hardlink is not supported: {item}')
    return p

def relative(value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise Refusal(f'Expected portable relative path: {value!r}')
    p = PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or any(c in value for c in '\x00\r\n'):
        raise Refusal(f'Path escapes root: {value!r}')
    return p.as_posix()

def safe_path(root, value):
    root = no_links(root)
    rel = relative(value)
    p = no_links(root / rel)
    if not p.is_relative_to(root):
        raise Refusal(f'Path escapes root: {value}')
    return p

def contains(parent, child):
    a, b = PurePosixPath(relative(parent)), PurePosixPath(relative(child))
    return b == a or a in b.parents

def tree(path, exclude=()):
    p = no_links(path)
    if not p.exists():
        return None
    if not p.is_dir():
        raise Refusal(f'Expected directory: {p}')
    result = {}
    for base, dirs, files in os.walk(p, followlinks=False):
        for name in dirs + files:
            item = Path(base) / name
            rel = item.relative_to(p).as_posix()
            no_links(item)
            if rel in exclude:
                continue
            if item.is_file():
                result[rel] = file_hash(item)
    return dict(sorted(result.items()))

def write_json(path, data, *, overwrite=False):
    p = no_links(path)
    if p.exists() and not overwrite:
        raise Refusal(f'Refusing to overwrite: {p}')
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    if overwrite:
        tmp = p.with_name(p.name + '.pending')
        if tmp.exists():
            raise Refusal(f'Pending write already exists: {tmp}')
        with tmp.open('x', encoding='utf-8') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, p)
    else:
        with p.open('x', encoding='utf-8') as stream:
            stream.write(text)

def run(argv, cwd=None, allowed=(0,), timeout=60, data=None):
    r = subprocess.run([str(x) for x in argv], cwd=cwd, input=data,
                       capture_output=True, timeout=timeout, shell=False)
    if r.returncode not in allowed:
        raise Refusal(f'Command failed ({r.returncode}): {argv[0]}: '
                      + r.stderr.decode('utf-8', errors='replace')[-2000:])
    return r

def git(root, *args, allowed=(0,), data=None):
    return run(['git', '-c', 'core.quotepath=false', '-C', no_links(root), *args],
               allowed=allowed, data=data).stdout.decode('utf-8', errors='strict')

def git_state(root):
    actual = Path(git(root, 'rev-parse', '--show-toplevel').strip()).resolve()
    if actual != no_links(root).resolve():
        raise Refusal('Pass the exact repository root, not a nested directory')
    state = {
        'head': git(root, 'rev-parse', 'HEAD').strip(),
        'branch': git(root, 'branch', '--show-current').strip(),
        'porcelain': git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all', '--ignored'),
        'sparse_enabled': git(root, 'config', '--get', 'core.sparseCheckout', allowed=(0, 1)).strip(),
    }
    sparse_file = Path(git(root, 'rev-parse', '--git-path', 'info/sparse-checkout').strip())
    if not sparse_file.is_absolute():
        sparse_file = Path(root) / sparse_file
    state['sparse_patterns'] = file_hash(sparse_file) if sparse_file.is_file() else None
    state['fingerprint'] = digest(state)
    return state

def result(status='OK', **values):
    return {'schema_version': 1, 'status': status, **values}

def emit(data, out=None):
    if out:
        write_json(out, data)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return {'OK': 0, 'BLOCKED': 2, 'INCONCLUSIVE': 3, 'NEEDS_USER_ACTION': 4}.get(data.get('status'), 3)

def guard_main(fn):
    try:
        code = fn()
    except (Refusal, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, yaml.YAMLError) as exc:
        code = emit(result('BLOCKED', error=str(exc)))
    raise SystemExit(code or 0)
