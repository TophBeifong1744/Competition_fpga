"""S1 recording: bind raw data to UART, reuse H1 exporter/reader, fixed-gain WAV.
Offline only. Does not modify/build/load any Vivado or Vitis project.
"""
import argparse,copy,csv,hashlib,json,math,re,shutil,struct,subprocess,sys,wave
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
TASK=HERE.parents[1]
REPO=next(p for p in HERE.parents if (p/'docs/team-workflow.md').is_file())
SOURCE=TASK/'source'
sys.path.insert(0,str(SOURCE))
from export_four import export,decode,HEADER
READER=REPO/'task-packages/PKG-B-ALG/payload/model/python/h1_reader.py'
OLD_META=TASK/'batches/center-target-20260914/delivery-01/c-center-target-20260914-01/metadata.json'
APP=Path('F:/College/verilog_digital_system/Vitis/four_mic_endurance')
POST=APP/'scene_checks/20260917_150930_post_63989c521b/result.json'
def need(ok,msg):
    if not ok:raise ValueError(msg)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def one(log,pattern):
    found=re.findall(pattern,log,re.M)
    need(len(found)==1,'Missing/duplicate log field: '+pattern)
    return found[0]
def verify(raw,log):
    need(len(raw)>0 and len(raw)%32==0,'Truncated/empty BIN')
    u=np.frombuffer(raw,dtype='<u4').reshape(-1,8)
    n=len(u);pcm=u[:,2:6].view('<i4')
    ids=u[:,0].astype(np.uint64)+(u[:,1].astype(np.uint64)<<32)
    need(bool(np.all(ids[1:]>ids[:-1]) and np.all(ids[1:]-ids[:-1]==1)),'ID discontinuity/wrap')
    need(bool(np.all((pcm>=-8388608)&(pcm<=8388607))),'Invalid signed24')
    need(bool(np.all(u[:,7]==0) and np.all((u[:,6]&0xfffffff0)==0)),'Unsupported flags/reserved')
    need(288000<=n<=300000 and n%250==0,'S1 group/packet bounds')
    groups,packets,nb,fnv,guard=one(log,r'^SCENE_INTEGRITY_PASS groups=(\d+) packets=(\d+) bytes=(\d+) fnv1a32=([0-9A-Fa-f]{8}) guard_ok=(\d+)\s*$')
    need((int(groups),int(packets),int(nb),int(guard))==(n,n//250,len(raw),1),'PASS count/guard mismatch')
    h=2166136261
    for byte in raw:h=((h^byte)*16777619)&0xffffffff
    need(h==int(fnv,16),'BIN/UART FNV mismatch')
    row=one(log,r'^SESSION 0 result=OK groups=(\d+) packets=(\d+) bytes_checked=(\d+) stop_sent=(\d+)\s*$')
    need(tuple(map(int,row))==(n,n//250,len(raw),1),'SESSION inconsistency')
    row=one(log,r'^CHECK first_failure=OK verified_packets=(\d+) verified_groups=(\d+) guard_checked_per_verified_packet=(\d+)\s*$')
    need(tuple(map(int,row))==(n//250,n,1),'CHECK inconsistency')
    first,last,elapsed,drain,check,gap=one(log,r'^first=([0-9A-Fa-f]{16}) last=([0-9A-Fa-f]{16}) capture_command_us=(\d+) drain_us=(\d+) max_check_us=(\d+) max_arm_gap_us=(\d+)\s*$')
    need((int(first,16),int(last,16))==(int(ids[0]),int(ids[-1])),'First/last ID mismatch')
    need(6000000<=int(elapsed)<8000000 and 0<=int(drain)<2000000,'Timing/stop timeout')
    src,sr,length,active,o0,o1,bg,bl,bv=one(log,r'^SOURCE=([0-9A-Fa-f]{8}) DMA_SR=([0-9A-Fa-f]{8}) length=(\d+) active=(-?\d+) owners=(\d+),(\d+) bad_group=(\d+) bad_lane=(\d+) bad_value=([0-9A-Fa-f]{8})\s*$')
    need((int(src,16),int(sr,16),int(length),int(active),int(o0),int(o1))==(0xc100000a,0x1002,8000,-1,0,0),'Source/DMA not safely drained')
    need((int(bg),int(bl),int(bv,16))==(249,3,int(u[-1,5])),'Successful check cursor not tied to final raw value')
    base,bytes_,words=one(log,r'^READY_FOR_DDR_DUMP base=([0-9A-Fa-f]{8}) bytes=(\d+) words=(\d+)\s*$')
    need(int(bytes_)==len(raw) and int(words)*4==len(raw),'Dump lengths disagree')
    alloc,data,capacity,total,each=one(log,r'^ARCHIVE allocation=([0-9A-Fa-f]{8}) data=([0-9A-Fa-f]{8}) capacity_bytes=(\d+) total_bytes=(\d+) guard_each=(\d+)\s*$')
    need(int(data,16)==int(base,16)==int(alloc,16)+64 and
         (int(capacity),int(total),int(each))==(9600000,9600128,64),'Archive layout mismatch')
    need(one(log,r'^PROFILE=(.*)$').strip()=='S1_6S_RAW target_us=6000000 min_groups=288000 capacity_groups=300000 record_bytes=32 timeout_us=2000000','Wrong profile')
    need(one(log,r'^SUMMARY (.*)$').strip()=='started=1 completed=1 failures=0; diagnostic only; NOT acoustic acceptance','Wrong session summary')
    need('CONTINUOUS_FAIL' not in log and 'RESET_TIMEOUT' not in log,'Failure in capture log')
    traces=re.findall(r'^TRACE packet=(\d+) slot=(\d+) SR=([0-9A-Fa-f]{8}) SOURCE=([0-9A-Fa-f]{8}) length=(\d+)\s*$',log,re.M)
    need(len(traces)==16,'Missing final traces')
    for expected,t in zip(range(n//250-16,n//250),traces):
        pi,slot,ds,ss,sz=t
        need((int(pi),int(slot),int(ds,16),int(sz))==(expected,expected%2,0x1002,8000),'Trace order/status/length')
        need(int(ss,16)&0xff000000==0xc1000000 and int(ss,16)&0x00ffff24==0,'Trace source fault')
    stats=[]
    for c in range(4):
        actual=dict(min=int(pcm[:,c].min()),max=int(pcm[:,c].max()),zeros=int((pcm[:,c]==0).sum()),clip_flags=int(((u[:,6]>>c)&1).sum()))
        reported=one(log,rf'^mic{c} min=(-?\d+) max=(-?\d+) zeros=(\d+) clip_flags=(\d+)\s*$')
        need(tuple(actual.values())==tuple(map(int,reported)),f'mic{c} raw/UART statistics mismatch')
        stats.append(actual)
    return dict(groups=n,packets=n//250,bytes=len(raw),seconds=n/48000,
        first_id=int(ids[0]),last_id=int(ids[-1]),fnv1a32=f'{h:08X}',source_status=src,dma_status=sr,
        archive_data=int(base,16),capture_command_us=int(elapsed),drain_us=int(drain),
        max_check_us=int(check),max_arm_gap_us=int(gap),channels=stats,flagged_rows=int((u[:,6]!=0).sum()))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--serial',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'logs').mkdir();(out/'versions').mkdir()
    shutil.copyfile(a.serial,out/'logs/original-serial.log')
    result=dict(status='INCOMPLETE',evidence_level='diagnostic',new_board_operation_by_agent=False)
    commands=[]
    try:
        raw=a.raw.read_bytes();log=a.serial.read_text(encoding='utf-8-sig')
        checked=verify(raw,log);result['capture']=checked
        post=json.loads(POST.read_text(encoding='utf-8'))
        need(post['status']=='S1_ARTIFACT_PASS_NOT_LOAD_NOT_BOARD','Missing build receipt')
        need(sha(APP/'build/four_mic_endurance.elf')==post['compiled']['elf_sha256'],'ELF changed since matched build')
        need(checked['archive_data']==post['compiled']['archive_data'],'Dump address does not match ELF')
        build=one(log,r'^FOUR SCENE S1 candidate build (.*)$').strip()
        firmware=(APP/'build/four_mic_endurance.elf').read_bytes()
        need(build[:-9].encode() in firmware and build[-8:].encode() in firmware,'UART/ELF build date/time mismatch')
        for name,digest in post['source_sha256'].items():need(sha(APP/'src'/name)==digest,'Source changed: '+name)
        for name in ('src','build/four_mic_endurance.elf','build/memory.map','_ide/launch.json'):
            target=out/'versions'/name;target.parent.mkdir(parents=True,exist_ok=True)
            if (APP/name).is_dir():shutil.copytree(APP/name,target)
            else:shutil.copyfile(APP/name,target)
        shutil.copyfile(POST,out/'versions/build-result.json')
        hw=TASK/'continuous-prototype-01/board-run-20260915-02/runtime'
        bit=APP/'_ide/bitstream/system_continuous_20260915.bit'
        need(sha(bit)==sha(hw/'system_continuous_20260915.bit'),'Hardware version differs')
        save(out/'versions/hardware-reference.json',dict(bit_path=str(bit),bit_sha256=sha(bit),
            frozen_bit=str(hw/'system_continuous_20260915.bit'),frozen_xsa=str(hw/'system_continuous_20260915.xsa'),
            frozen_xsa_sha256=sha(hw/'system_continuous_20260915.xsa'),
            basis='Previously checked Run configuration, unchanged host files and matching UART build; not FPGA readback attestation'))
        cap=out/'c-scene-20260917-01'
        meta=export(a.raw,cap,acquisition_id=cap.name,config_version='four-channel-continuous-s1-6s-raw-20260917-v1',
            source_kind='hardware-audio',provenance='Toph Beifong: one live-voice Run, background/speech/stopped-speech; paired UART/BIN',
            capture_point='four PDM -> CIC3 R64 gain32 signed24 -> 8-word record -> DMA S2MM two slots -> PS validated raw copy -> CPU-owned DDR archive -> post-stop flush -> XSDB BIN')
        old=json.loads(OLD_META.read_text(encoding='utf-8'))
        for key in ('coordinates_m','geometry_version','coordinate_system','geometry_record','adapter_interface','calibration_status'):
            meta[key]=copy.deepcopy(old[key])
        meta['provisional_fields']=copy.deepcopy(old['provisional_fields'])
        meta['geometry_reuse_basis']='Existing C-board declared-square geometry retained for this task; not a new geometric measurement or calibration.'
        record=dict(source_mode='live human voice',spoken_words='就让我忘了这一切',
            source_reference='mic0',reported_direction='+X',reported_distance_m_approx=0.05,
            reported_relative_height_m_approx=0,measurement_method=None,position_uncertainty_m=None,
            source_position_model_m=[0.05,0,0],array_center_model_m=[0.02,0.02,0],
            center_relative_vector_model_m=[0.03,-0.02,0],center_distance_model_m=math.hypot(.03,.02),
            center_azimuth_model_deg=math.degrees(math.atan2(-.02,.03)),
            model_note='Derived ONLY from approximate user placement and prior declared square; NOT measured angle/distance truth or validated far-field.',
            reported_activity_seconds_approx=[dict(label='background',start=0,end=2),dict(label='speech',start=2,end=5),dict(label='post_speech_background',start=5,end=checked['seconds'])],
            activity_basis='Operator approximate 2s quiet / 3s speech / 1s after; no synchronized trigger or precision sample labels',
            precise_activity_sample_indices=None,activity_uncertainty_seconds=None,
            playback_device='not applicable: live voice',playback_effects='not applicable: live voice',
            acoustic_voice_level=None,independent_clean_reference=None,independent_noise_reference=None,
            microphone_internal_processing='not independently verified',far_field_validated=False,
            precision_direction_ground_truth=False,recording_datetime=None,
            timestamp_note='Filename and firmware build dates do not independently timestamp acoustic acquisition')
        save(out/'actual-record.json',record);meta['source_placement_record']=record
        meta['processing']='No extra host filtering, DC removal, normalization, gap filling or renumbering in BIN/CSV. Existing frontend PDM/CIC3 R64 gain32 and signed24 saturation remain.'
        meta['firmware_config_version']='S1_6S_RAW';meta['serial_sha256']=sha(a.serial)
        meta['recording_notes']=dict(operator='Toph Beifong',fnv1a32=checked['fnv1a32'],single_continuous_run=True,
            stopping='One explicit acquisition stop after >=6 seconds; full packet drain; no within-segment restart')
        meta['limits']='Near-field live voice diagnostic only; approximate activity/model geometry, no independent clean/noise reference. No SNR gain, target-detection/lock behavior, M1/H3 or direction-accuracy claim.'
        save(cap/'metadata.json',meta);shutil.copyfile(a.serial,cap/'serial.log')
        rows=decode(raw)
        with (cap/'samples.csv').open(encoding='utf-8',newline='') as f:
            reader=csv.reader(f);need(next(reader)==HEADER,'CSV header')
            count=0
            for count,(expected,actual) in enumerate(zip(rows,reader,strict=True),1):need(list(map(str,expected))==actual,'CSV does not match raw')
            need(count==checked['groups'],'CSV count')
        pcm=np.frombuffer(raw,dtype='<u4').reshape(-1,8)[:,2:6].view('<i4')
        gain=12;audio=np.rint(pcm.astype(np.float64)*gain/256)
        need(bool(np.all((audio>=-32768)&(audio<=32767))),'Fixed-gain WAV would introduce clipping; preserve data and review')
        for c in range(4):
            p=cap/f'mic{c}.wav';payload=audio[:,c].astype('<i2').tobytes()
            with wave.open(str(p),'wb') as w:w.setparams((1,2,48000,0,'NONE','not compressed'));w.writeframes(payload)
            with wave.open(str(p),'rb') as w:need(w.getnframes()==len(pcm) and w.readframes(len(pcm))==payload,'WAV readback mismatch')
        save(cap/'listening.json',dict(formula='round-to-nearest-ties-to-even(PCM24*12/256)',gain=12,
            sample_rate_hz=48000,output='signed16 mono, one file per lane',extra_clipping=0,
            common_gain_entire_record_and_all_channels=True,per_segment_normalization=False,agc=False))
        phases=[]
        for label,start,end in [('background',0,96000),('speech',96000,240000),('after',240000,len(pcm))]:
            values=pcm[start:end].astype(np.float64)
            phases.append(dict(label=label,start_index_for_summary=start,end_exclusive=end,
                basis='nominal operator timing, NOT detected onset/offset',mean=values.mean(axis=0).tolist(),
                raw_rms=np.sqrt((values*values).mean(axis=0)).tolist()))
        save(out/'phase-statistics.json',dict(phases=phases,units='original PCM integer codes',not_snr=True))
        cmd=[sys.executable,'-B',str(READER),str(cap)]
        p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=120)
        (out/'logs/h1-reader.stdout.json').write_text(p.stdout,encoding='utf-8');(out/'logs/h1-reader.stderr.log').write_text(p.stderr,encoding='utf-8')
        commands.append(dict(argv=cmd,returncode=p.returncode));need(p.returncode==0,'H1 reader failed')
        need(json.loads(p.stdout)['status']=='PASS_FORMAT_ONLY','Unexpected reader status')
        need(sha(a.raw)==sha(cap/'raw.bin') and sha(a.serial)==sha(cap/'serial.log'),'Input changed during export')
        result.update(status='DIAGNOSTIC_INPUT_SELF_CHECK_PASS_NOT_B_ACCEPTANCE',csv_bin_exact=True,wav_readback_exact=True,
            reader='PASS_FORMAT_ONLY',new_continuous_raw_recording=True,not_independent_clean_noise_reference=True)
        save(out/'dependencies.json',{str(p.relative_to(REPO)):sha(p) for p in (Path(__file__),SOURCE/'export_four.py',READER,OLD_META)})
    except Exception as exc:
        result.update(status='FAILED',error=str(exc))
        if not (out/'c-scene-20260917-01/raw.bin').exists():shutil.copyfile(a.raw,out/'failed-input.bin')
        raise
    finally:
        save(out/'RESULT.json',result);save(out/'commands.json',commands)
        save(out/'SHA256.json',dict(files={p.relative_to(out).as_posix():sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SHA256.json'}))
        print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
