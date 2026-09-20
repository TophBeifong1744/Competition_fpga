"""Version operator metadata; preserve previous metadata/manifests and raw payloads."""
import copy,json,shutil,subprocess,sys
from pathlib import Path
from prepare import HERE,save,sha

out=HERE/'evidence/operator-confirmation-20260920-01'
out.mkdir(parents=True,exist_ok=False)
repo=next(p for p in HERE.parents if (p/'docs/team-workflow.md').is_file())
reader=repo/'task-packages/PKG-B-ALG/payload/model/python/h1_reader.py'
statement=dict(device_model='Xiaomi 15 Pro',output_device='phone loudspeaker',player_application=None,
    fixed_volume_percent=85,same_wav_volume_effects_off_confirmed=True,
    distance_reference='array center',reported_distance_m_approx=1.5,position_method='visual estimate',
    same_height_approx=True,operator_error_statement='偏差不超过5cm',
    interpretation='Operator estimated positional deviation <=0.05 m, not instrument calibration or quantified angular/height uncertainty',
    array_not_moved=True,background_statement='有微小声音',
    background_playback_paused=None,background_sound_source=None,
    same_run_entry_and_no_within_segment_reset=True)
save(out/'operator-statement.json',statement)
records=[]
for parent_name in ('received-20260920-02-corrected','received-20260920-03-remaining'):
    parent=HERE/'evidence'/parent_name
    for folder in sorted(parent.iterdir()):
        cap=folder/folder.name
        if not (cap/'metadata.json').is_file():continue
        backup=out/'before'/folder.name;backup.mkdir(parents=True)
        meta_path=cap/'metadata.json';shutil.copyfile(meta_path,backup/'metadata.json')
        meta=json.loads(meta_path.read_text(encoding='utf-8'))
        raw_sha=sha(cap/'raw.bin');csv_sha=sha(cap/'samples.csv')
        r=meta['source_placement_record']
        r.update(device_model='Xiaomi 15 Pro',output_device='phone loudspeaker',player_application=None,
            volume_setting='85%',operator_reported_effects='All visible effects off; same fixed WAV and volume confirmed for batch',
            array_geometry_unchanged_confirmed=True,actual_center_distance_m_approx=1.5,
            actual_relative_height_m_approx=0,position_measurement_method='visual estimate, operator report',
            estimated_distance_error_m=None,estimated_angle_error_deg=None,estimated_height_error_m=None,
            operator_estimated_position_deviation_bound_m=0.05,
            uncertainty_note='5 cm is an operator positional estimate; axis-specific, angular and measurement uncertainty not established',
            loading_record='Operator confirms same Run entry and no reset during each segment; host binding saved separately',
            submission_note='Operator setting/placement update 2026-09-20; filename angle remains approximate visually positioned label, not precision truth',
            operator_confirmation=str((out/'operator-statement.json').relative_to(HERE)))
        if r['kind']=='target':r['actual_center_reference_azimuth_deg_approx']=r['planned_azimuth_deg']
        else:
            r.update(background_condition_notes='Operator reports faint sounds; source unspecified; not claimed absolute silence',
                     playback_paused_confirmed=None,no_people_speaking_during_take=None)
        meta['metadata_revision']='operator-confirmation-20260920-01'
        save(meta_path,meta)
        save(out/(folder.name+'-record.json'),r)
        cmd=[sys.executable,'-B',str(reader),str(cap)]
        p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=180)
        (out/(folder.name+'-reader.json')).write_text(p.stdout,encoding='utf-8')
        (out/(folder.name+'-reader.stderr.log')).write_text(p.stderr,encoding='utf-8')
        ok=p.returncode==0 and json.loads(p.stdout).get('status')=='PASS_FORMAT_ONLY'
        assert sha(cap/'raw.bin')==raw_sha and sha(cap/'samples.csv')==csv_sha
        records.append(dict(name=folder.name,directory=str(cap),reader_exit=p.returncode,format_pass=ok,
            raw_and_csv_unchanged=True,previous_metadata_sha256=sha(backup/'metadata.json'),
            updated_metadata_sha256=sha(meta_path),command=cmd))
        print(folder.name, 'PASS_FORMAT_ONLY' if ok else 'FAILED',flush=True)
save(out/'results.json',dict(records=records,pending='Background playback paused and faint sound source; acoustic activity uncertainty remains unverified'))
files={}
for item in records:
    cap=Path(item['directory'])
    for p in sorted(cap.iterdir()):
        if p.is_file():files[p.relative_to(HERE).as_posix()]=sha(p)
save(out/'CURRENT-DATA-SHA256.json',files)
save(out/'SHA256.json',{p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file()})
