import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parents[1]
TASKS = ROOT / 'task-packages/PKG-B-ALG/tasks'
BATCH = ROOT / 'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/trusted-direction-input-20260918'

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

def config():
    return load(HERE/'config.json')

def new_output(path):
    out = Path(path).resolve()
    # Generated evidence never writes into any tracked package.
    if out == ROOT or ROOT in out.parents:
        raise ValueError('output must be outside checkout')
    out.mkdir(parents=True, exist_ok=False)
    return out
