"""Offline S1 checks/export and provisional marker alignment. Never talks to a board."""
import argparse
import copy
import csv
import json
import re
import shutil
import subprocess
import sys
import traceback
import wave
from pathlib import Path
import numpy as np
from prepare import HERE, PREVIOUS, APP, load_module, save, sha, write_wav

TASK=HERE.parents[1]
REPO=next(p for p in HERE.parents if (p/'docs/team-workflow.md').is_file())
PLAY=HERE/'playback-v1'

def read_wav(path):
    with wave.open(str(path),'rb') as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate())!=(1,2,48000):
            raise ValueError('Marker WAV format')
        return np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(float)

def marker_peak(x, template):
    """Mean-removed normalized correlation FOR ALIGNMENT ONLY, no PCM rewriting."""
    x=np.asarray(x,dtype=float);t=template-template.mean();m=len(t);n=len(x)
    if n<m: raise ValueError('Capture shorter than marker')
    size=1 << (n+m-2).bit_length()
    corr=np.fft.irfft(np.fft.rfft(x,size)*np.fft.rfft(t[::-1],size),size)[m-1:n]
    s=np.r_[0.,np.cumsum(x)];ss=np.r_[0.,np.cumsum(x*x)]
    energy=np.maximum(0.,ss[m:]-ss[:-m]-(s[m:]-s[:-m])**2/m)
    denominator=np.sqrt(energy*np.dot(t,t))
    score=np.zeros_like(corr)
    np.divide(np.abs(corr),denominator,out=score,where=denominator>1e-8)
    peak=int(np.argmax(score));masked=score.copy()
    masked[max(0,peak-m):min(len(masked),peak+m)]=0
    return dict(index=peak,absolute_correlation=float(score[peak]),
                runner_up_outside_marker_width=float(masked.max()))

def align(pcm):
    timeline=json.loads((PLAY/'timeline.json').read_text(encoding='utf-8'))
    templates=[read_wav(PLAY/f'marker-{label}.wav') for label in ('start','end')]
    rows=[]
    for lane in range(4):
        a,b=[marker_peak(pcm[:,lane],t) for t in templates]
        interval=(b['index']-a['index'])/48000
        confident=(min(a['absolute_correlation'],b['absolute_correlation'])>=0.15
                   and abs(interval-4.25)<=0.05
                   and all(v['absolute_correlation']>1.5*v['runner_up_outside_marker_width'] for v in (a,b)))
        row=dict(channel=f'mic{lane}',start_marker=a,end_marker=b,
            measured_marker_separation_s=interval,
            status='CANDIDATE_ALIGNMENT_REVIEW_REQUIRED' if confident else 'UNRESOLVED')
        if confident:
            # Map source timeline onto each recorded lane using two acoustic markers.
            scale=(b['index']-a['index'])/(213600-9600)
            mapped=lambda sample: a['index']+(sample-9600)*scale
            row.update(source_to_capture_scale=scale,
                speech_interval_source_mapped_samples=[mapped(v) for v in timeline['speech_source_interval']],
                source_file_interval_mapped_samples=[mapped(0),mapped(230400)],
                source_file_fits_capture=(mapped(0)>=0 and mapped(230400)<=len(pcm)))
        rows.append(row)
    return dict(channels=rows,algorithm='absolute normalized matched correlation against frozen chirps; two-point affine map',
        thresholds=dict(min_correlation=0.15,peak_ratio=1.5,separation_tolerance_s=0.05),
        thresholds_scope='heuristic marker search only, NOT B target-presence thresholds or measured uncertainty',
        exact_activity_labels=False,activity_uncertainty_seconds=None,
        required_followup='Review waveform/listening, multipath and marker clipping. Source-mapped speech window is a prediction, not actual acoustic onset/offset. Preserve uncertainty; no scoring of markers.',
        source_sha256=sha(PLAY/'soundsight-target-v1.wav'))

def dump(log_path, output):
    # Print only. Never execute XSDB or overwrite a dump.
    if output.exists(): raise ValueError('BIN destination already exists')
    path=output.resolve().as_posix()
    if any(c in path for c in '{}\n\r'): raise ValueError('Unsupported Tcl filename')
    old=load_module('existing_scene',PREVIOUS/'finish_scene.py')
    log=log_path.read_text(encoding='utf-8-sig')
    a,b,c=old.one(log,r'^READY_FOR_DDR_DUMP base=([0-9A-Fa-f]{8}) bytes=(\d+) words=(\d+)\s*$')
    count,packets,nb,fnv,guard=old.one(log,r'^SCENE_INTEGRITY_PASS groups=(\d+) packets=(\d+) bytes=(\d+) fnv1a32=([0-9A-Fa-f]{8}) guard_ok=(\d+)\s*$')
    pre=json.loads((HERE/'evidence/preflight-01/result.json').read_text(encoding='utf-8'))
    if not (int(a,16)==pre['compiled']['archive_data'] and 288000<=int(count)<=300000
            and int(count)%250==0 and int(packets)*250==int(count) and int(guard)==1
            and int(nb)==int(b)==int(c)*4==int(count)*32): raise ValueError('Dump fields disagree with fixed S1 contract')
    print('connect -url tcp:127.0.0.1:3121')
    print('targets -set -filter {name =~ "*Cortex-A9*#0"}')
    print(f'mrd -bin -file {{{path}}} -size w 0x{a} {c}')

def process(raw_path, log_path, record_path, out):
    out.mkdir(parents=True,exist_ok=False)
    inputs=out/'inputs';inputs.mkdir()
    shutil.copyfile(raw_path,inputs/'raw.bin');shutil.copyfile(log_path,inputs/'serial.log')
    shutil.copyfile(record_path,inputs/'operator-record.json')
    result=dict(status='INCOMPLETE',board_operation_by_agent=False)
    try:
        old=load_module('existing_scene',PREVIOUS/'finish_scene.py')
        raw=(inputs/'raw.bin').read_bytes();log=(inputs/'serial.log').read_text(encoding='utf-8-sig')
        checked=old.verify(raw,log)
        record=json.loads(record_path.read_text(encoding='utf-8-sig'))
        aid=record['acquisition_id'];kind=record['kind']
        if not re.fullmatch(r'[a-zA-Z0-9_-]+',aid) or kind not in ('background','target'):
            raise ValueError('Invalid acquisition ID/kind')
        pre_path=HERE/'evidence/preflight-01/result.json'
        pre=json.loads(pre_path.read_text(encoding='utf-8'))
        if pre['status']!='REUSED_S1_LOAD_PREFLIGHT_PASS_NOT_BOARD': raise ValueError('No preflight')
        if checked['archive_data']!=pre['compiled']['archive_data']: raise ValueError('Archive/ELF mismatch')
        checks=[(APP/'build/four_mic_endurance.elf',pre['compiled']['elf_sha256']),
                (APP/'build/memory.map',pre['map_sha256']),
                (APP/'build/CMakeFiles/four_mic_endurance.elf.dir/main.c.obj',pre['compiled']['object_sha256']),
                (APP/'_ide/launch.json',pre['launch_config_sha256'])]
        checks += [(APP/'src'/name,digest) for name,digest in pre['source_sha256'].items()]
        checks += [(Path(pre['load_paths']['bit']),'b15991bc0f8595970361be553b542e334dbb7dca268c01864ecd80fcffbbffaf')]
        for file,digest in checks:
            if sha(file)!=digest: raise ValueError('Version changed: '+str(file))
        firmware=(APP/'build/four_mic_endurance.elf').read_bytes()
        build=old.one(log,r'^FOUR SCENE S1 candidate build (.*)$').strip()
        if not(build[:-9].encode() in firmware and build[-8:].encode() in firmware): raise ValueError('UART/ELF build time mismatch')
        cap=out/aid
        meta=old.export(inputs/'raw.bin',cap,acquisition_id=aid,
            config_version='four-channel-continuous-s1-6s-raw-20260917-v1',source_kind='hardware-audio',
            provenance='Toph Beifong board operation; development data, not independent held-out validation',
            capture_point='PDM -> CIC3 R64 gain32 signed24 -> 8-word groups -> DMA two RX slots -> validated PS copy to archive -> flush after drain -> XSDB BIN')
        prior=json.loads(old.OLD_META.read_text(encoding='utf-8'))
        # Historical model is retained with its evidence level, never filled from planned angles.
        for key in ('coordinates_m','geometry_version','coordinate_system','geometry_record','adapter_interface','calibration_status','provisional_fields'):
            meta[key]=copy.deepcopy(prior[key])
        meta['geometry_reuse_basis']='Prior operator-declared 40 mm coplanar square, not precision calibration. Current mounting confirmation is in operator record; absent means unconfirmed.'
        meta['source_placement_record']=record
        meta['development_data']=True
        meta['processing']='BIN/CSV unchanged PCM integers and original IDs/flags. Existing PDM/CIC and signed24 processing remain; no extra DC removal, filtering, gain normalization, gap fill or renumbering.'
        meta['limits']='Diagnostic development input. No SNR gain, precision angle truth, independent validation, formal M1/H3 or closed-loop claim.'
        save(cap/'metadata.json',meta);shutil.copyfile(inputs/'serial.log',cap/'serial.log')
        rows=old.decode(raw)
        with (cap/'samples.csv').open(encoding='utf-8',newline='') as f:
            reader=csv.reader(f)
            if next(reader)!=old.HEADER: raise ValueError('CSV header mismatch')
            for expected,actual in zip(rows,reader,strict=True):
                if list(map(str,expected))!=actual: raise ValueError('BIN/CSV mismatch')
        pcm=np.frombuffer(raw,'<u4').reshape(-1,8)[:,2:6].view('<i4')
        audio=np.rint(pcm.astype(float)*12/256)
        if np.any((audio<-32768)|(audio>32767)): raise ValueError('Common gain 12 introduces WAV clipping; keep failure, review global batch gain')
        for lane in range(4):
            write_wav(cap/f'mic{lane}.wav',audio[:,lane])
            if not np.array_equal(read_wav(cap/f'mic{lane}.wav'),audio[:,lane]): raise ValueError('WAV readback')
        save(cap/'listening.json',dict(gain=12,formula='round-even(PCM24 * 12 / 256)',
            signed_bits=16,sample_rate_hz=48000,common_all_channels_and_recordings=True,extra_clipping=0,agc=False))
        if kind=='target':save(out/'alignment.json',align(pcm))
        else:save(out/'alignment.json',dict(status='NOT_APPLICABLE_BACKGROUND',exact_activity_labels=False))
        cmd=[sys.executable,'-B',str(old.READER),str(cap)]
        p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=180)
        (out/'reader.stdout.json').write_text(p.stdout,encoding='utf-8');(out/'reader.stderr.log').write_text(p.stderr,encoding='utf-8')
        save(out/'reader-command.json',dict(argv=cmd,returncode=p.returncode))
        if p.returncode or json.loads(p.stdout).get('status')!='PASS_FORMAT_ONLY': raise ValueError('H1 reader rejected')
        save(out/'version-binding.json',dict(load_preflight=str(pre_path),sha256=sha(pre_path),
            host_files={str(p):sha(p) for p,_ in checks},operator_loading_evidence=record.get('loading_record'),
            limitation='Host files/Run configuration and UART verified; NOT FPGA readback attestation'))
        save(out/'dependencies.json',{str(p):sha(p) for p in (Path(__file__),HERE/'scripts/prepare.py',PREVIOUS/'finish_scene.py',old.SOURCE/'export_four.py',old.READER,old.OLD_META)})
        result.update(status='FORMAT_AND_INTEGRITY_PASS_SCENE_REVIEW_PENDING',capture=checked,
            csv_bin_exact=True,wav_readback_exact=True,reader='PASS_FORMAT_ONLY',new_board_run_by_agent=False)
    except Exception as exc:
        result.update(status='FAILED_PRESERVED_INPUTS',error=str(exc),traceback=traceback.format_exc())
    save(out/'result.json',result)
    save(out/'sha256.json',{p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='sha256.json'})
    print(result['status'],out)
    return 0 if result['status']=='FORMAT_AND_INTEGRITY_PASS_SCENE_REVIEW_PENDING' else 1

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
    d=sub.add_parser('dump-command');d.add_argument('--serial',type=Path,required=True);d.add_argument('--bin-output',type=Path,required=True)
    d=sub.add_parser('process')
    for name in ('raw','serial','record','out'):d.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    if a.cmd=='dump-command':dump(a.serial,a.bin_output);return 0
    return process(a.raw,a.serial,a.record,a.out)

if __name__=='__main__':sys.exit(main())
