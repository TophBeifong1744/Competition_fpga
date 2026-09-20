"""Preserve and inspect the two failed precheck recordings; no board operations."""
import json
import shutil
from pathlib import Path
import numpy as np
from prepare import HERE, PREVIOUS, APP, load_module, save, sha
from process_capture import align

out=HERE/'evidence/received-20260920-01'
out.mkdir(parents=True,exist_ok=False)
old=load_module('audit_old_scene',PREVIOUS/'finish_scene.py')
results=[]
for name in ('trusted_bg_pre_20260920_01','trusted_000_20260920_01'):
    folder=out/name;folder.mkdir()
    for ext in ('bin','log'):
        source=Path('F:/College/verilog_digital_system/Vitis')/(name+'.'+ext)
        target=folder/source.name;shutil.copyfile(source,target)
        assert sha(source)==sha(target)
    raw=(folder/(name+'.bin')).read_bytes()
    log=(folder/(name+'.log')).read_text(encoding='utf-8-sig')
    u=np.frombuffer(raw,'<u4').reshape(-1,8);pcm=u[:,2:6].view('<i4')
    ids=u[:,0].astype(np.uint64)+(u[:,1].astype(np.uint64)<<32)
    h=2166136261
    for b in raw:h=((h^b)*16777619)&0xffffffff
    groups,packets,nb,fnv,guard=old.one(log,r'^SCENE_INTEGRITY_PASS groups=(\d+) packets=(\d+) bytes=(\d+) fnv1a32=([0-9A-Fa-f]{8}) guard_ok=(\d+)\s*$')
    channels=[]
    for c in range(4):
        stats=dict(min=int(pcm[:,c].min()),max=int(pcm[:,c].max()),zeros=int((pcm[:,c]==0).sum()),clip_flags=int(((u[:,6]>>c)&1).sum()))
        stats['uart_stats_match']=tuple(stats.values())==tuple(map(int,old.one(log,rf'^mic{c} min=(-?\d+) max=(-?\d+) zeros=(\d+) clip_flags=(\d+)\s*$')))
        stats.update(channel=c,constant=bool(np.all(pcm[:,c]==pcm[0,c])),unique_codes=len(np.unique(pcm[:,c])))
        channels.append(stats)
    try:
        old.verify(raw,log)
        strict_gate='PASS'
    except Exception as exc:
        strict_gate='REJECTED: '+str(exc)
    flags,counts=np.unique(u[:,6],return_counts=True)
    row=dict(name=name,status='REJECTED_AS_TRUSTED_FOUR_CHANNEL_INPUT',bytes=len(raw),groups=len(u),seconds=len(u)/48000,
        first_id=int(ids[0]),last_id=int(ids[-1]),ids_contiguous=bool(np.all(np.diff(ids)==1)),
        fnv1a32=f'{h:08X}',fnv_matches_uart=h==int(fnv,16),
        uart_counts_match=(int(groups),int(packets),int(nb),int(guard))==(len(u),len(u)//250,len(raw),1),
        reserved_zero=bool(np.all(u[:,7]==0)),signed24_valid=bool(np.all((pcm>=-8388608)&(pcm<=8388607))),
        flags_counts={f'0x{int(f):08X}':int(n) for f,n in zip(flags,counts)},channels=channels,
        unchanged_strict_verifier=strict_gate,sha256={p.name:sha(p) for p in folder.iterdir() if p.is_file()},
        limits='Raw integrity facts do not make saturated channels usable; root cause not established. No flags cleared or normalization applied.')
    save(folder/'analysis.json',row)
    if '000' in name:
        save(folder/'marker-search-not-acceptance.json',align(pcm))
    results.append(row)
pre=json.loads((HERE/'evidence/preflight-01/result.json').read_text(encoding='utf-8'))
bindings={}
for name,expected in [('build/four_mic_endurance.elf',pre['compiled']['elf_sha256']),
                      ('_ide/launch.json',pre['launch_config_sha256']),
                      ('_ide/bitstream/system_continuous_20260915.bit','b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf')]:
    p=APP/name;actual=sha(p)
    bindings[name]=dict(sha256=actual,matches_preflight=actual==expected)
save(out/'summary.json',dict(status='STOP_REMAINING_RECORDINGS_INPUT_FAULT',captures=results,host_version_binding=bindings,
    root_cause='UNDETERMINED',new_board_operations=False,firmware_modified=False,passed_captures=0))
save(out/'SHA256.json',{p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file()})
print(json.dumps(dict(output=str(out),captures=[dict(name=r['name'],groups=r['groups'],fnv_match=r['fnv_matches_uart'],ids_contiguous=r['ids_contiguous'],flags=r['flags_counts'],strict_gate=r['unchanged_strict_verifier']) for r in results],host_versions=bindings),indent=2))
