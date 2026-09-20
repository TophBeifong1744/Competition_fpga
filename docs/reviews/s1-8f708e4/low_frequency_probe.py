"""Reproduce the focused descriptive spectrum probe (configured sample rate)."""
import json
from pathlib import Path
import numpy as np
p=Path('F:/NUEC/review-worktrees/s1-8f708e4/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/background-target-stop-20260917/delivery-01/c-scene-20260917-01/raw.bin')
x=np.frombuffer(p.read_bytes(),dtype='<u4').reshape(-1,8)[:96000,2:6].view('<i4').astype(float)
x-=x.mean(axis=0)
f=np.fft.rfftfreq(len(x),1/48000)
a=abs(np.fft.rfft(x*np.hanning(len(x))[:,None],axis=0))**2
m=(f>=40)&(f<=60)
r={'background_peak_40_60_hz':f[m][a[m].argmax(axis=0)].tolist(),'background_correlation':np.corrcoef(x.T).tolist()}
# Original result created by equivalent inline Python command; do not overwrite.
assert r==json.loads((Path(__file__).parent/'low-frequency-probe.json').read_text())
print(json.dumps(r))
