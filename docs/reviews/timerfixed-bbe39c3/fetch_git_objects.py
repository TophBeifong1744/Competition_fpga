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
SHA = 'bbe39c38dc36ccb4c0492f492b86f6c46d885fbe'
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

ref = get('/git/ref/heads/codex/toph/timerfixed-entry-20260916')
assert ref['object']['sha'] == SHA
commit = get('/git/commits/' + SHA)
assert commit['sha'] == SHA
assert [p['sha'] for p in commit['parents']] == ['8371f014711e04553749e6c2ffc29f34b9d5ccc9']
(OUT / 'api-commit.json').write_text(json.dumps(commit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(OUT / 'api-ref.json').write_text(json.dumps(ref, indent=2) + '\n', encoding='utf-8')

# The API normalizes commit dates to UTC. Recover original offsets only by matching
# the requested immutable Git SHA; no candidate is accepted without that exact hash.
zones = ['+0800', '+0000'] + [f'{"+" if n >= 0 else "-"}{abs(n)//4:02d}{abs(n)%4*15:02d}' for n in range(-48, 57)]
zones = list(dict.fromkeys(zones))
def identity(person, zone):
    stamp = int(datetime.datetime.fromisoformat(person['date'].replace('Z', '+00:00')).timestamp())
    return f"{person['name']} <{person['email']}> {stamp} {zone}"

raw_commit = None
for author_zone, committer_zone, ending in itertools.product(zones, zones, ['\n', '']):
    raw = ('tree ' + commit['tree']['sha'] + '\n' +
           ''.join('parent ' + p['sha'] + '\n' for p in commit['parents']) +
           'author ' + identity(commit['author'], author_zone) + '\n' +
           'committer ' + identity(commit['committer'], committer_zone) + '\n\n' +
           commit['message'] + ending).encode('utf-8')
    if oid('commit', raw) == SHA:
        raw_commit = raw
        break
assert raw_commit is not None, 'Cannot reconstruct exact commit object; stop'

pending_trees = [commit['tree']['sha']]
blobs = set()
seen = set()
while pending_trees:
    sha = pending_trees.pop()
    if sha in seen or exists(sha):
        continue
    seen.add(sha)
    tree = get('/git/trees/' + sha)
    assert tree['sha'] == sha and not tree.get('truncated')
    entries = sorted(tree['tree'], key=lambda x: x['path'].encode() + (b'/' if x['type'] == 'tree' else b''))
    data = b''.join(format(int(x['mode'], 8), 'o').encode() + b' ' + x['path'].encode() + b'\0' + bytes.fromhex(x['sha']) for x in entries)
    write('tree', sha, data)
    for x in entries:
        if x['type'] == 'tree': pending_trees.append(x['sha'])
        elif x['type'] == 'blob' and not exists(x['sha']): blobs.add(x['sha'])
        else: assert x['type'] in ('blob', 'commit'), x
    assert len(seen) < 150, 'Unexpectedly large missing tree closure'
print('Missing blob objects:', len(blobs), flush=True)
def read_blob(sha):
    value = get('/git/blobs/' + sha)
    assert value['sha'] == sha and value['encoding'] == 'base64'
    return sha, base64.b64decode(value['content'])
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    for sha, data in pool.map(read_blob, sorted(blobs)):
        write('blob', sha, data)
write('commit', SHA, raw_commit)
# Traverse the resulting commit tree to ensure every referenced object is present.
subprocess.check_call(prefix + ['rev-list', '--objects', '--missing=error', SHA], stdout=subprocess.DEVNULL)
after = get('/git/ref/heads/codex/toph/timerfixed-entry-20260916')
assert after['object']['sha'] == SHA
result = {'status': 'PASS_EXACT_GIT_OBJECTS_FROM_OFFICIAL_API', 'sha': SHA,
          'author_timezone': author_zone, 'committer_timezone': committer_zone,
          'remote_branch_before_after': SHA, 'written_objects': written,
          'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
(OUT / 'api-fetch-result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(result['status'], SHA, 'objects=' + str(len(written)), flush=True)
