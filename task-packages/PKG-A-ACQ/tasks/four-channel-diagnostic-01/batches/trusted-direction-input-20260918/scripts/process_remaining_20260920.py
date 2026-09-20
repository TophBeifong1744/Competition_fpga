"""Archive/check the remaining six submissions; planned angles are not measured truth."""
import json
from pathlib import Path
from prepare import HERE, save, sha
from process_capture import process

root=HERE/'evidence/received-20260920-03-remaining'
root.mkdir(parents=True,exist_ok=False)
base=Path('F:/College/verilog_digital_system/Vitis')
names=[('m045',1,-45),('m045',2,-45),('000',2,0),('p045',1,45),('p045',2,45),('bg_post',1,None)]
items=[]
for label,take,angle in names:
    name=f'trusted_{label}_20260920_{take:02d}'
    record=json.loads((HERE/'operator-record-template.json').read_text(encoding='utf-8'))
    record.update(acquisition_id=name,kind='background' if angle is None else 'target',planned_azimuth_deg=angle,
        submission_note='User supplied remaining files; angle is filename/planned condition only. Actual placement, settings and loading confirmation pending.')
    rec=root/(name+'-record.json');save(rec,record)
    code=process(base/(name+'.bin'),base/(name+'.log'),rec,root/name)
    items.append(dict(name=name,exit_code=code))
save(root/'execution.json',dict(results=items,board_operations_by_agent=False))
save(root/'SHA256.json',{p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file()})
previous=HERE/'evidence/received-20260920-02-corrected'
summary=[]
for parent in (previous,root):
    for folder in sorted(parent.iterdir()):
        if not folder.is_dir() or not (folder/'result.json').exists():continue
        r=json.loads((folder/'result.json').read_text(encoding='utf-8'))
        a=json.loads((folder/'alignment.json').read_text(encoding='utf-8')) if (folder/'alignment.json').exists() else {}
        summary.append(dict(name=folder.name,path=str(folder),result=r,
            alignment=[dict(channel=c['channel'],status=c['status'],file_fits=c.get('source_file_fits_capture'),
                file_interval_s=[v/48000 for v in c.get('source_file_interval_mapped_samples',[])],
                marker_interval_s=c['measured_marker_separation_s']) for c in a.get('channels',[])]))
save(root/'eight-recordings-summary.json',summary)
print(json.dumps([dict(name=v['name'],status=v['result']['status'],error=v['result'].get('error'),
    groups=v['result'].get('capture',{}).get('groups'),flags=v['result'].get('capture',{}).get('flagged_rows'),alignment=v['alignment']) for v in summary],indent=2))
