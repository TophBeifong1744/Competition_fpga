from pathlib import Path
import numpy as np
import json, hashlib, zipfile
base=Path(__file__).parent
evidence=base.parent/'mono_acceptance_20260910'
result={}
for name in ['quiet_03','music_04']:
    raw=(evidence/'quiet_music'/f'{name}.bin').read_bytes()
    x=np.frombuffer(raw,dtype='<i4').reshape(-1,4)[:,2].astype(float)
    a=x-x.mean();s=np.abs(np.fft.rfft(a*np.hanning(len(a))))**2
    # Non-DC local maxima; resolution 1 Hz at nominal fs.
    peaks=[i for i in range(2,100) if s[i]>s[i-1] and s[i]>=s[i+1]]
    peaks=sorted(peaks,key=lambda i:s[i],reverse=True)[:5]
    frames=[]
    for i,b in enumerate(x.reshape(10,4800)):
        frames.append(dict(start_s=i/10,mean=float(b.mean()),rms_ac=float(np.sqrt(np.mean((b-b.mean())**2))),minimum=float(b.min()),maximum=float(b.max())))
    result[name]=dict(sha256=hashlib.sha256(raw).hexdigest(),low_peak_bins_hz=peaks,low_peaks_relative_db=[float(10*np.log10(s[i]/s[1:100].max())) for i in peaks],frames_100ms=frames,pcm_multiple_of_32=bool(np.all(x.astype(np.int32)%32==0)),equal_adjacent_fraction=float(np.mean(x[1:]==x[:-1])),identical_100ms_blocks=len({b.tobytes() for b in x.reshape(10,4800)})<10)
snap=evidence/'snapshot'
with zipfile.ZipFile(snap/'system_single_mic.xsa') as z:
    bits=[n for n in z.namelist() if n.endswith('.bit')]
    result['xsa_bit_members']=bits
    result['xsa_bit_matches_launch_snapshot']=len(bits)==1 and z.read(bits[0])==(snap/'system_single_mic.bit').read_bytes()
    inits=[n for n in z.namelist() if n.endswith('ps7_init.tcl')]
    result['xsa_init_members']=inits
    result['xsa_init_matches_launch_snapshot']=len(inits)==1 and z.read(inits[0])==(base/'ps7_init.tcl').read_bytes()
(base/'low_frequency_result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(result,indent=2))
