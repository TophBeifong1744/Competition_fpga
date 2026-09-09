"""Read-only checks for a-input-boundary-0.1, not hardware acceptance."""
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
EXPECTED = {
    'source-snapshot/system.bd': '0a46738f4e400b23a0a0eb944d568e7212e17e5c9c669e99974b441068eb9c64',
    'source-snapshot/test_source.sv': '9dcfed15189390a93e8ca0805aa31608c3dfabd384d1a620a213cfbcd207a677',
    'source-snapshot/test_source_bd.v': '302cbd21dc8d23024c40c94d81bbbabf726965858a32c5ddffb10e1da5138392',
}
for name, expected in EXPECTED.items():
    assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == expected, name
source_files = {
    'docs/minimal-data-interface.md': '5489c6945230d338e3836c8a5d3007ddaf2257190b4cad016615569ae2d0ca00',
    'docs/architecture.md': '04dc37bb61f3eb1e9da15c221ec8c81ce304b4f11563027635aaa6956254eac1',
    'task-packages/PKG-B-ALG/payload/model/python/audio_frames.py': '0ed77ea8db8834576c21206358a8d945b612a176cad742bb266d077ee2a79408',
    'task-packages/PKG-A-ACQ/payload/docs/input-scale-and-pl-ps-boundary.md': '3767353b34dd97e494b9ec1b80de288e8b83c989c12fbcdc0b5eb0e0eac49959',
}
for name, expected in source_files.items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
bd = json.loads((HERE/'source-snapshot/system.bd').read_text(encoding='utf-8'))
components = bd['design']['components']
assert 'test_source_bd_0' in components and 'axi_dma_0' in components
assert not any('xfft' in str(v.get('vlnv','')) for v in components.values())
sys.path.insert(0, str(ROOT/'task-packages/PKG-B-ALG/payload/model/python'))
from audio_frames import adapt_h1
codes = np.array([[-8388608,0,4194304,8388607],[-32768,32767,-1,1]],dtype=np.int32)
recording = SimpleNamespace(samples=codes,sample_ids=np.array([9,10],dtype=np.uint64),
    clean_intervals=[dict(row_start=0,row_stop=2)],metadata=dict(sample_rate_hz=48000),
    file_hashes={},stream_error=np.array([0,0]),missing_intervals=[],direction_policy=lambda:'diagnostic')
out = adapt_h1(recording)
np.testing.assert_array_equal(out.samples,np.array([[-1,0,.5,1-2**-23],[-1/256,32767/2**23,-2**-23,2**-23]]))
np.testing.assert_array_equal(out.sample_ids,[9,10])
np.testing.assert_array_equal(recording.samples,codes)
print('PASS: 7 pinned file hashes; BD source identity; existing adapt_h1 8 scalar conversions and unchanged IDs/input. Software checks only.')
