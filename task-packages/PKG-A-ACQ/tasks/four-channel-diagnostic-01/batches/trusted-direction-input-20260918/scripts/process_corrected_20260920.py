"""Process operator-corrected submissions; preserve both revisions and unknown metadata."""
import json
from pathlib import Path
from prepare import HERE, save, sha
from process_capture import process

root=HERE/'evidence/received-20260920-02-corrected'
root.mkdir(parents=True,exist_ok=False)
base=Path('F:/College/verilog_digital_system/Vitis')
prior=HERE/'evidence/received-20260920-01'
results=[]
for name,kind in [('trusted_bg_pre_20260920_01','background'),('trusted_000_20260920_01','target')]:
    record=json.loads((HERE/'operator-record-template.json').read_text(encoding='utf-8'))
    record.update(acquisition_id=name,kind=kind,planned_azimuth_deg=0,
        submission_note='Operator says these replace previously mistakenly supplied same-name files; actual positioning and loading details still pending confirmation.',
        source_mode='phone loudspeaker playback' if kind=='target' else 'background; source-off condition pending operator confirmation')
    record_path=root/(name+'-record.json');save(record_path,record)
    changes={ext:dict(previous=sha(prior/name/(name+'.'+ext)),corrected=sha(base/(name+'.'+ext))) for ext in ('bin','log')}
    status=process(base/(name+'.bin'),base/(name+'.log'),record_path,root/name)
    results.append(dict(name=name,exit_code=status,hash_comparison=changes))
save(root/'submission-correction.json',dict(operator_statement='这个才是正确的，刚才发错了。',
    previous_evidence_preserved=str(prior),previous_saturation_diagnosis_applies_only_to_previous_bytes=True,
    no_hardware_repair_inferred=True,results=results))
save(root/'SHA256.json',{p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file()})
print(json.dumps(results,indent=2))
