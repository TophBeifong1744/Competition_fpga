"""Reuse existing export/reader for one centered-target capture; no board or build calls."""
import argparse
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback
import wave
import numpy as np

ROOT = Path(__file__).resolve().parent
TASK = ROOT.parents[1]
REPO = TASK.parents[3]
SOURCE = TASK/'source'
READER = REPO/'task-packages/PKG-B-ALG/payload/model/python/h1_reader.py'
OLD = TASK/'batches/c-adapter-first-20260913/delivery-01'
sys.path[:0] = [str(SOURCE), str(READER.parent)]
from export_c_capture import verify
from export_four import decode
from h1_reader import CONFIG_FIELDS, ReaderSession


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def save(p, obj):
    with p.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def check_capture(d):
    raw = (d/'raw.bin').read_bytes()
    serial = (d/'serial.log').read_text(encoding='utf-8-sig')
    fnv = verify(raw, serial)
    rows = decode(raw)
    with (d/'samples.csv').open(encoding='utf-8', newline='') as f:
        actual = list(csv.reader(f))
    if actual[1:] != [[str(v) for v in row] for row in rows]:
        raise ValueError('CSV/BIN mismatch')
    pcm = np.array([r[1:5] for r in rows], dtype=np.int32)
    flags = np.frombuffer(raw, dtype='<u4').reshape(-1,8)[:,6]
    stats = []
    for c in range(4):
        v = pcm[:,c]
        fields = re.search(rf'mic{c} min=(-?\d+) max=(-?\d+) zeros=(\d+) clipped=(\d+)', serial)
        measured = [int(v.min()),int(v.max()),int(np.count_nonzero(v==0)),int(np.count_nonzero(flags & (1<<c)))]
        if not fields or list(map(int,fields.groups())) != measured:
            raise ValueError('BIN/serial amplitude/clip statistics mismatch')
        expected = np.rint(v.astype(np.float64)*12/256)
        if np.any((expected < -32768)|(expected > 32767)):
            raise ValueError('Fixed-gain listening would clip; retain failure and review conversion')
        with wave.open(str(d/f'mic{c}.wav'),'rb') as w:
            if (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes()) != (1,2,48000,len(rows)):
                raise ValueError('WAV format mismatch')
            if w.readframes(len(rows)) != expected.astype('<i2').tobytes():
                raise ValueError('WAV derivative mismatch')
        stats.append({'channel':c,'min':measured[0],'max':measured[1], 'zeros':measured[2], 'clip_flags':measured[3],
                      'mean':float(v.mean()), 'rms_without_mean':float(np.sqrt(np.mean((v.astype(float)-v.mean())**2))),
                      'unique_values':int(len(np.unique(v)))})
    summary = ReaderSession().load(d).summary()
    return {'groups':len(rows),'bytes':len(raw),'duration_s_configured':len(rows)/48000,
            'first_id':rows[0][0],'last_id':rows[-1][0],'fnv1a32':f'{fnv:08X}',
            'error_rows':sum(r[5] for r in rows),'channels':stats,
            'identical_channel_pairs':[[i,j] for i in range(4) for j in range(i+1,4) if np.array_equal(pcm[:,i],pcm[:,j])],
            'csv_bin_exact':True,'wav_exact_common_gain':12,'wav_extra_clipping':0,
            'reader':summary}


def verify_archive(out):
    manifest = json.loads((out/'SHA256.json').read_text(encoding='utf-8'))
    for name,digest in manifest.items():
        p = (out/name).resolve()
        if not p.is_relative_to(out.resolve()) or sha(p) != digest:
            raise ValueError('Archive mismatch: '+name)
    if {p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()} != set(manifest)|{'SHA256.json'}:
        raise ValueError('Unlisted/missing archive files')
    result = check_capture(out/'c-center-target-20260914-01')
    session = ReaderSession()
    for p in (OLD/'c-adapter-quiet-20260913-01',OLD/'c-adapter-speech-20260913-01',out/'c-center-target-20260914-01'):
        session.load(p)
    print(json.dumps({'status':'ARCHIVE_CHECK_PASS_NOT_B_ACCEPTANCE','files':len(manifest),
        'groups':result['groups'],'fnv1a32':result['fnv1a32'],'error_rows':result['error_rows']},indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--verify', type=Path)
    p.add_argument('--raw', type=Path)
    p.add_argument('--serial', type=Path)
    p.add_argument('--inspection', type=Path)
    p.add_argument('--record', type=Path)
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if a.verify:
        verify_archive(a.verify)
        return
    if not all((a.raw,a.serial,a.inspection,a.record,a.output)):
        p.error('Supply raw, serial, inspection, record and fresh output')
    out = a.output.resolve()
    if not out.is_relative_to(ROOT) or out == ROOT:
        p.error('New output must be within this batch')
    out.mkdir(exist_ok=False)
    commands = []

    def run(argv, name, cwd=REPO):
        with (out/'logs'/name).open('x',encoding='utf-8') as log:
            proc = subprocess.run([str(x) for x in argv],cwd=cwd,stdout=log,stderr=subprocess.STDOUT,shell=False)
        commands.append({'argv':[str(x) for x in argv],'cwd':str(cwd),'returncode':proc.returncode})
        if proc.returncode:
            raise ValueError(f'{name} failed; preserve output')

    try:
        (out/'logs').mkdir()
        (out/'versions').mkdir()
        inputs = {'raw':{'path':str(a.raw),'sha256':sha(a.raw)},'serial':{'path':str(a.serial),'sha256':sha(a.serial)}}
        verify(a.raw.read_bytes(), a.serial.read_text(encoding='utf-8-sig'))
        record = json.loads(a.record.read_text(encoding='utf-8'))
        shutil.copyfile(a.record, out/'actual-record.json')
        inspection = json.loads((a.inspection/'report.json').read_text(encoding='utf-8'))
        if inspection['status'] != 'DISK_PRECHECK_PASS_NOT_BOARD_TEST':
            raise ValueError('Missing matching-file precheck')
        for name,row in inspection['loading'].items():
            original = Path(row['path'])
            if sha(original) != row['sha256']:
                raise ValueError('Loading input changed since inspection: '+name)
            shutil.copyfile(original, out/'versions'/name)
            if sha(out/'versions'/name) != row['sha256']:
                raise ValueError('Loading snapshot mismatch')
        shutil.copyfile(a.inspection/'report.json',out/'versions/loading-record.json')
        old_meta_path = OLD/'c-adapter-speech-20260913-01/metadata.json'
        old_meta = json.loads(old_meta_path.read_text(encoding='utf-8'))
        cap = out/'c-center-target-20260914-01'
        # This reuses the previously confirmed unchanged assembly, not a new electrical test.
        run([sys.executable,'-B',SOURCE/'export_c_capture.py',a.raw,a.serial,cap,
             '--acquisition-id',cap.name,'--operator','Toph Beifong',
             '--scene','Reported live voice, mouth on array-center +X at 1.5m and approximately level; see actual-record.json',
             '--numbered-mating-confirmed'],'export.log')
        shutil.copyfile(cap/'metadata.json',out/'logs/original-exporter-metadata.json')
        meta = json.loads((cap/'metadata.json').read_text(encoding='utf-8'))
        # Same geometry and processing: preserve the full existing H1 configuration, not scene-specific notes.
        for k in CONFIG_FIELDS:
            if k in old_meta:
                meta[k] = copy.deepcopy(old_meta[k])
        meta['config_version'] = old_meta['config_version']
        meta['firmware_config_version'] = old_meta['firmware_config_version']
        meta['geometry_record'] = copy.deepcopy(old_meta['geometry_record'])
        meta['adapter_interface'] = copy.deepcopy(old_meta['adapter_interface'])
        meta['source_placement_record'] = record
        meta['loading_record'] = '../versions/loading-record.json'
        meta['assembly_confirmation_basis'] = record['existing_assembly_confirmation']
        meta['config_version_note'] = 'Only source scene/acquisition changed; geometry and all H1 configuration fields match the previous declared-square configuration.'
        meta['processing'] = 'No additional host processing of captured PCM; frontend PDM CIC3 R64, gain32 and signed24 saturation already applied. IDs and flags preserved.'
        meta['limits'] = 'Diagnostic only. Reported approximate source position is not precision ground truth; no synchronized clean/noise reference, SNR gain, far-field or H3 acceptance.'
        (cap/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        pcm = np.array([r[1:5] for r in decode((cap/'raw.bin').read_bytes())],dtype=np.int32)
        for c in range(4):
            values = np.rint(pcm[:,c].astype(np.float64)*12/256)
            if np.any((values < -32768)|(values > 32767)):
                raise ValueError('WAV would clip; keep original and review separately')
            with wave.open(str(cap/f'mic{c}.wav'),'wb') as w:
                w.setparams((1,2,48000,0,'NONE','not compressed'))
                w.writeframes(values.astype('<i2').tobytes())
        save(cap/'listening.json',{'gain':12,'formula':'round(PCM24*12/256)','sample_rate_hz':48000,
            'extra_clipping':0,'not_raw_pcm_replacement':True,'per_channel_normalization':False,'agc':False})
        result = check_capture(cap)
        run([sys.executable,'-B','-m','unittest','-v','test_export','test_c_capture_gate'],'export-tests.log',SOURCE)
        run([sys.executable,'-B',READER,cap],'h1-reader.log')
        run([sys.executable,'-B',READER,OLD/'c-adapter-quiet-20260913-01',OLD/'c-adapter-speech-20260913-01',cap],'h1-coexistence.log')
        for key,path in [('raw',a.raw),('serial',a.serial)]:
            if sha(path) != inputs[key]['sha256'] or sha(cap/('raw.bin' if key=='raw' else 'serial.log')) != inputs[key]['sha256']:
                raise ValueError('Source/copy changed')
        deps = [Path(__file__),a.record,old_meta_path,SOURCE/'export_four.py',SOURCE/'export_c_capture.py',READER]
        save(out/'inputs.json',inputs)
        save(out/'dependencies.json',{f.relative_to(REPO).as_posix():sha(f) for f in deps})
        save(out/'RESULT.json',{'status':'PASS_MINIMAL_DIAGNOSTIC_INPUT_SELF_CHECK_NOT_B_REVIEW',
             'checked_utc':datetime.now(timezone.utc).isoformat(),'capture':result,
             'new_synthesis_or_timing':False,'new_continuous_capture_test':False,
             'raw_data_unchanged':True,'source_position_precision_verified':False,
             'independent_clean_or_noise_reference_supplied':False})
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except Exception:
        (out/'FAILURE.txt').write_text(traceback.format_exc(),encoding='utf-8')
        raise
    finally:
        save(out/'commands.json',commands)
        save(out/'SHA256.json',{q.relative_to(out).as_posix():sha(q) for q in sorted(out.rglob('*')) if q.is_file()})


if __name__ == '__main__':
    main()
