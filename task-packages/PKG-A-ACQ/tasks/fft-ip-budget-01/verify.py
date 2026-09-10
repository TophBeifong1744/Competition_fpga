"""Seal/check this self-contained A delivery; no hardware acceptance implied."""
import argparse, hashlib, json, math, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--seal',action='store_true');p.add_argument('--out',type=Path)
a=p.parse_args()
manifest=ROOT/'hashes.json'
if a.seal:
    files={f.relative_to(ROOT).as_posix():digest(f) for f in sorted(ROOT.rglob('*'))
           if f.is_file() and f!=manifest and '__pycache__' not in f.parts}
    with manifest.open('x',encoding='utf-8') as h: json.dump(files,h,indent=2)
else:
    if a.out is None: p.error('--out must name a new directory outside the package')
    output=a.out.resolve()
    if output==ROOT or ROOT in output.parents: p.error('keep new verification outside the sealed package')
    output.mkdir(parents=True,exist_ok=False)
    hashes=json.loads(manifest.read_text(encoding='utf-8'))
    for name,expected in hashes.items(): assert digest(ROOT/name)==expected,name
    evidence=ROOT/'evidence/run01'
    subprocess.run([sys.executable,'-B',str(ROOT/'vectors.py'),'--out',str(output/'vectors')],check=True)
    assert digest(output/'vectors/inputs.mem')==digest(evidence/'inputs.mem'), 'input codes changed'
    ref_new=json.loads((output/'vectors/reference.json').read_text())
    ref_old=json.loads((evidence/'reference.json').read_text())
    max_ref_delta=max(abs(v-w) for x,y in zip(ref_new,ref_old,strict=True)
                      for z,t in zip(x,y,strict=True) for v,w in zip(z,t,strict=True))
    assert max_ref_delta<=1e-7, max_ref_delta
    subprocess.run([sys.executable,'-B',str(ROOT/'check_results.py'),'--vectors',str(output/'vectors'),
        '--sim',str(evidence),'--out',str(output/'check.json')],check=True)
    actual=json.loads((output/'check.json').read_text())
    recorded=json.loads((evidence/'check.json').read_text())
    assert actual.keys()==recorded.keys()
    for key,value in actual.items():
        if key in ['max_component_error_codes','rms_component_error_codes']:
            assert math.isclose(value,recorded[key],rel_tol=1e-9,abs_tol=1e-7),key
        else: assert value==recorded[key],key
    c=json.loads((ROOT/'contract.json').read_text())
    assert sum(c['fft_stage_right_shifts'])==sum(c['ifft_stage_right_shifts'])==10
    assert sum(v<<(2*i) for i,v in enumerate(c['fft_stage_right_shifts']))<<1==int(c['inverse_config_hex'],16)
    assert int(c['forward_config_hex'],16)==int(c['inverse_config_hex'],16)|1
    assert c['planned_service_slot_cycles']>=actual['measured_serial_config_interval_cycles']
    assert c['planned_transform_cycles_per_hop']==21*c['planned_service_slot_cycles']
    assert c['hop_cycles_floor_at_target_clock']==100000000*512//48000
    assert c['remaining_non_fft_budget_cycles_before_safety_margin']==c['hop_cycles_floor_at_target_clock']-c['planned_transform_cycles_per_hop']
    print(f'PASS: {len(hashes)} hashes; exact input codes; reference max delta={max_ref_delta}; reference bytes equal={digest(output/"vectors/reference.json")==digest(evidence/"reference.json")}; complete output/cycle check; budget arithmetic. Not an independent XSim rerun.')
