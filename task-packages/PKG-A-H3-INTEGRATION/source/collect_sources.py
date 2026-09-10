"""One-time evidence snapshot; immutable Git blobs plus explicit local archives."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
BASE = '9878ccafdda6cd5a522cc9de95c1277bcee70f08'
FFT = 'ac0ff38e954dac094fd84e28b329dcb24dded7fb'
AUTHOR = Path('C:/Users/Toph Beifong/.codex/visualizations/2026/09/05/01a06ff9-0287-7e00-b73d-abf12e6b3035')
SHARED = Path('E:/Users/Toph Beifong/Documents/GitHub/Competition_fpga')
TARGET = ROOT / 'references'
if (ROOT / 'evidence/source-index.json').exists():
    raise RuntimeError('Evidence already sealed; do not re-collect')
entries = []

def put(relative, raw, origin, kind, commit=None):
    destination = TARGET / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.read_bytes() != raw:
            raise RuntimeError('Refuse replacing different evidence: ' + relative)
    else:
        destination.write_bytes(raw)
    entries.append(dict(file='references/' + relative, source=origin, kind=kind,
                        commit=commit, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))

def git(*args):
    return subprocess.check_output(['git', '-c', 'core.longpaths=true', '-c', 'safe.directory=' + REPO.as_posix(), *args], cwd=REPO)

main_files = {
    'architecture.md': 'docs/architecture.md',
    'h1-interface.md': 'docs/minimal-data-interface.md',
    'input-boundary.md': 'docs/input-scale-and-pl-ps-boundary.md',
    'pynq-guide.md': 'docs/pynq-integration-guide.md',
    'four-channel-contract.md': 'hardware/four-channel-sample-interface-contract.md',
    'audio_frames.py': 'task-packages/PKG-B-ALG/payload/model/python/audio_frames.py',
    'tracker-config.json': 'task-packages/PKG-B-ALG/payload/config/sector-tracking.json',
    'b-review.md': 'task-packages/PKG-B-ALG/tasks/input-boundary-adoption-01/review.md',
    'b-contract.json': 'task-packages/PKG-B-ALG/tasks/input-boundary-adoption-01/source-snapshot/fixed-point-contract-01/contract.json',
    'b-ledger.json': 'task-packages/PKG-B-ALG/tasks/input-boundary-adoption-01/source-snapshot/implementation-budget-01/evidence/run02/ledger.json',
}
for name, source in main_files.items():
    put('main/' + name, git('cat-file', 'blob', BASE + ':' + source), source, 'git-blob', BASE)
prefix = 'task-packages/PKG-A-ACQ/tasks/fft-ip-budget-01/'
for source in git('ls-tree', '-r', '--name-only', FFT, '--', prefix).decode().splitlines():
    put('fft/' + source[len(prefix):], git('cat-file', 'blob', FFT + ':' + source), source, 'git-blob-pending-B-review', FFT)
mono_files = ['README.md', 'serial-user-transcript.txt', 'snapshot-manifest.json',
              'snapshot/system.bd', 'snapshot/pcm_capture_axis.v', 'snapshot/pdm_cic3.v',
              'snapshot/single_mic_top.v', 'snapshot/main_mono_capture.c', 'snapshot/single_mic_io.xdc']
for name in mono_files:
    source = AUTHOR / 'mono_acceptance_20260910' / name
    put('mono/' + name, source.read_bytes(), str(source), 'local-post-capture-archive-not-load-proof')
for name in ['ACCEPTANCE_STATUS.md', 'CLOSEOUT.md', 'system_wrapper_utilization_placed.rpt',
             'system_wrapper_timing_summary_routed.rpt', 'manifest.json']:
    source = AUTHOR / 'mono_closeout_20260910' / name
    put('mono-closeout/' + name, source.read_bytes(), str(source), 'local-archive-not-new-measurement')
source = SHARED / 'docs/rtl-language-and-bd-integration.md'
put('policy/rtl-language-and-bd-integration.md', source.read_bytes(), str(source), 'user-approved-policy-uncommitted-at-snapshot')
(ROOT / 'evidence').mkdir(exist_ok=True)
(ROOT / 'evidence/source-index.json').write_text(json.dumps(dict(base_main=BASE, fft_candidate_commit=FFT, entries=entries), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('SOURCE_SNAPSHOT_PASS', len(entries))
