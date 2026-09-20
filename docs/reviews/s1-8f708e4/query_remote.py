"""Fetch missing Git objects via authenticated official API; verify every Git object ID.

Uses the existing credential helper in memory only. No credential is printed or archived.
Does not change branch refs, the index, or any working tree.
"""
import base64
import concurrent.futures
import datetime
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import urllib.request

REPO = 'F:/NUEC/develop'
GIT = 'C:/Users/BryanZheng/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
SHA = '8f708e42caf32c1de6f30726298e3edf0e1970b6'
API = 'https://api.github.com/repos/TophBeifong1744/Competition_fpga'
OUT = Path(__file__).resolve().parent
env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
prefix = [GIT, '-c', 'safe.directory=' + REPO, '-C', REPO]
c = subprocess.run(prefix + ['credential', 'fill'],
    input=b'protocol=https\nhost=github.com\npath=TophBeifong1744/Competition_fpga.git\n\n',
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=20)
fields = dict(s.split(b'=', 1) for s in c.stdout.splitlines() if b'=' in s)
if c.returncode or b'password' not in fields:
    raise RuntimeError('No noninteractive credential available')
token = fields[b'password'].decode()

def get(path):
    req = urllib.request.Request(API + path, headers={
        'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
        'User-Agent': 'B-independent-review'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def oid(kind, data):
    return hashlib.sha1(kind.encode() + b' ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def exists(sha):
    return subprocess.run(prefix + ['cat-file', '-e', sha], stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0

written = []
def write(kind, sha, data):
    assert oid(kind, data) == sha, ('API object ID mismatch', kind, sha)
    actual = subprocess.check_output(prefix + ['hash-object', '-t', kind, '-w', '--stdin'], input=data).decode().strip()
    assert actual == sha
    written.append({'type': kind, 'sha': sha, 'bytes': len(data)})

refs={n:get('/git/ref/heads/'+n)['object']['sha'] for n in ('main','codex/toph/background-target-stop-20260917')}
(OUT/'remote-current.json').write_text(json.dumps(refs,indent=2)+'\n')
print(json.dumps(refs))