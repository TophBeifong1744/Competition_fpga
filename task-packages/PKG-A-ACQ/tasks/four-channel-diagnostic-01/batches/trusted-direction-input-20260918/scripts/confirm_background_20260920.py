"""Incremental background annotation only; preserve payloads and earlier evidence."""
import json,shutil
from pathlib import Path
from prepare import HERE,save,sha

prior=HERE/'evidence/operator-confirmation-20260920-01'
out=HERE/'evidence/background-confirmation-20260920-01'
out.mkdir(parents=True,exist_ok=False)
records=json.loads((prior/'results.json').read_text(encoding='utf-8'))['records']
save(out/'operator-statement.json',dict(statement='前后背景录制时，手机确实暂停播放。微小声音来自鼠标点击',
    applies_to=['trusted_bg_pre_20260920_01','trusted_bg_post_20260920_01'],
    absolute_silence=False,mouse_click_sample_intervals=None))
changes=[]
previous_manifest=json.loads((prior/'CURRENT-DATA-SHA256.json').read_text(encoding='utf-8'))
for relative,expected in previous_manifest.items():
    if sha(HERE/relative)!=expected:raise ValueError('File changed since preceding check: '+relative)
for row in records:
    if 'bg_' not in row['name']:continue
    p=Path(row['directory'])/'metadata.json'
    shutil.copyfile(p,out/(row['name']+'-metadata-before.json'))
    meta=json.loads(p.read_text(encoding='utf-8'))
    r=meta['source_placement_record']
    r.update(playback_paused_confirmed=True,source_mode='background; phone playback paused',
        background_condition_notes='Operator confirms phone playback paused; faint sounds were mouse clicks. Not absolute silence or independent clean/noise ground truth.',
        background_sound_source='mouse clicks',mouse_click_sample_intervals=None)
    meta['metadata_revision']='background-confirmation-20260920-01'
    save(p,meta)
    assert json.loads(p.read_text(encoding='utf-8'))['source_placement_record']['playback_paused_confirmed'] is True
    changes.append(dict(file=str(p),sha256=sha(p),only_annotation_changed=True))
manifest={relative:sha(HERE/relative) for relative in previous_manifest}
for relative,expected in previous_manifest.items():
    if not relative.endswith('/metadata.json'):assert manifest[relative]==expected
save(out/'CURRENT-DATA-SHA256.json',manifest)
save(out/'results.json',dict(status='BACKGROUND_ANNOTATION_UPDATED_PAYLOADS_UNCHANGED',changes=changes,
    prior_reader_checks='8/8 PASS_FORMAT_ONLY in ../operator-confirmation-20260920-01; reused, not rerun',
    actual_checks='Previous full data manifest verified; JSON readback; all non-metadata files unchanged',
    pending='Precise acoustic activity uncertainty and mouse-click intervals unverified; diagnostic development data only'))
save(out/'SHA256.json',{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()})
print('BACKGROUND_CONFIRMED; non-metadata files unchanged; no board operation')
