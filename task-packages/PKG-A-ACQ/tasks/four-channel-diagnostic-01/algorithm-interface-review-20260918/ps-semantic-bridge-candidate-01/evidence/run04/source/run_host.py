"""Build host C, compare explicit LE outputs with pinned independent A/B references."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import time
import traceback
import numpy as np

HERE=Path(__file__).resolve().parents[1]
ROOT=next(p for p in HERE.parents if (p/'.git').exists())
TASK='task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/'
PINS={'A':'f879a54cf40359209895af955bcef92accdf79ea','plan':'0abdc91c57787b7c868a797b88f35129de169faf',
      'B':'f5a4cea7a7cf7dcccf09720cfff92131e6157752','core':'e4f9eae3fe7e4104ff8a6827937e326954f90a82',
      'coord':'b0643b11f6441c673d594fb40153567cceb37bd9',
      'main':'fd1b99c966de1f572bcd080f2b2d6860c0ac5ccd'}
REASONS={'UPSTREAM_ERROR':1,'QUEUE_OVERFLOW':2,'ID_DUPLICATE':4,'ID_REVERSE':8,'ID_WRAP':16,
         'INVALID_FLAGS':32,'INVALID_RESERVED':64,'PCM_RANGE':128,'CLIP':256,'DROP':512}

def digest(data):return hashlib.sha256(data).hexdigest()
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def check(ok,detail='mismatch'):
    if not ok:raise AssertionError(detail)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cc',required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False);snap=out/'source';snap.mkdir();inputs=out/'inputs';inputs.mkdir()
    commands=[];tests=[];bindings=[];counter=0
    def save(name,value): (out/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    def run(argv,label):
        nonlocal counter
        counter+=1;start=time.perf_counter();p=subprocess.run(list(map(str,argv)),cwd=ROOT,capture_output=True)
        prefix=f'{counter:03}_{label}'
        (out/(prefix+'-stdout.txt')).write_bytes(p.stdout);(out/(prefix+'-stderr.txt')).write_bytes(p.stderr)
        commands.append(dict(argv=list(map(str,argv)),cwd=str(ROOT),exit_code=p.returncode,host_elapsed_seconds=time.perf_counter()-start,
                             stdout=prefix+'-stdout.txt',stderr=prefix+'-stderr.txt'))
        save('commands.json',commands);return p
    def pin(key,path,name):
        data=subprocess.check_output(['git','show',PINS[key]+':'+path],cwd=ROOT);p=inputs/name;p.write_bytes(data)
        bindings.append(dict(commit=PINS[key],path=path,snapshot=name,sha256=digest(data)));return p
    def test(name,fn):
        try:result=fn();tests.append(dict(name=name,status='PASS',detail=result))
        except Exception:tests.append(dict(name=name,status='FAIL',traceback=traceback.format_exc()))
        print(tests[-1]['status'],name,flush=True);save('tests.json',tests)
    try:
        for d in ('src','tests'):
            for p in (HERE/d).glob('*'):
                if p.is_file(): (snap/p.name).write_bytes(p.read_bytes())
        save('invocation.json',dict(argv=sys.argv,python=sys.version,numpy=np.__version__,pins=PINS,head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),date='2026-09-21'))
        core=load(pin('core','task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/frame-adapter-bram-candidate-01/model/framing_model.py','framing_model.py'),'pinned_core')
        model=load(pin('A',TASK+'increment-20260923/source/logic_adapter.py','logic_adapter.py'),'pinned_adapter')
        bp='task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/'
        gold=json.loads(pin('B',bp+'golden/framing.json','framing.json').read_text(encoding='utf-8'))
        arrays=np.load(pin('B',bp+'golden/synthetic-frames.npz','synthetic-frames.npz'),allow_pickle=False)
        pin('B',bp+'B-RESPONSE-20260923.md','B-response.md')
        pin('coord','deliverables/phase-2026-09-18/recheck-20260921.md','coordination.md')
        pin('plan',TASK+'engineering-closeout-20260923/ROUTE.md','prior-route.md')
        pin('main','docs/reviews/b-fixed-nodes-349501c/REVIEW.md','latest-node-review.md')
        save('bindings.json',bindings)
        def preservation():
            records=[]
            for key,sub in [('A','increment-20260923'),('plan','engineering-closeout-20260923')]:
                prefix=TASK+sub
                names=subprocess.check_output(['git','ls-tree','-r','--name-only',PINS[key],'--',prefix],cwd=ROOT,text=True).splitlines()
                for name in names:
                    frozen=subprocess.check_output(['git','show',PINS[key]+':'+name],cwd=ROOT);actual=(ROOT/name).read_bytes()
                    equal=actual==frozen or (b'\0' not in actual and actual.replace(b'\r\n',b'\n')==frozen.replace(b'\r\n',b'\n'))
                    records.append(dict(path=name,frozen=digest(frozen),working=digest(actual),content_equal=equal))
            save('preservation.json',records);check(all(r['content_equal'] for r in records));return dict(files=len(records),text_CRLF_equivalence_explicit=True)
        test('frozen_A_packages_preserved',preservation)
        version=run([args.cc,'--version'],'compiler-version');check(version.returncode==0,'compiler could not launch')
        common=[args.cc,'-std=c11','-Wall','-Wextra','-Wpedantic','-Wconversion','-Wshadow','-Werror','-I',snap,snap/'ps_bridge.c',snap/'host.c']
        executables=[]
        for opt in ('O0','O2'):
            exe=out/f'host-{opt}.exe';p=run(common+['-'+opt,'-g','-o',exe],'build-'+opt);check(p.returncode==0,'C build failed '+opt)
            p=run([exe],'selftest-'+opt);check(p.returncode==0 and b'HOST_SELFTEST_PASS' in p.stdout,'C selftest failed '+opt)
            text=p.stdout.decode();mem=json.loads(next(x[7:] for x in text.splitlines() if x.startswith('MEMORY ')));save('memory-'+opt+'.json',mem)
            executables.append(exe)
        sanitizer=[]
        for flags,label in [(['-fsanitize=address,undefined','-fno-omit-frame-pointer'],'asan-ubsan'),(['-fsanitize=undefined','-fno-sanitize-recover=all'],'ubsan')]:
            exe=out/(label+'.exe');p=run(common+['-O1','-g']+flags+['-o',exe],'build-'+label)
            if p.returncode:
                sanitizer.append(dict(profile=label,state='UNAVAILABLE_BUILD_FAILED_NOT_TEST_PASS'));continue
            p=run([exe],'selftest-'+label)
            sanitizer.append(dict(profile=label,state='PASS' if p.returncode==0 and b'HOST_SELFTEST_PASS' in p.stdout else 'FAILED_RUN'))
            if p.returncode==0 and b'HOST_SELFTEST_PASS' in p.stdout:executables.append(exe)
        save('sanitizers.json',sanitizer)
        check(not any(r['state']=='FAILED_RUN' for r in sanitizer),'instrumented runtime failed; inspect evidence')
        G=core.Group
        def g(i,**kw):return G(i,(1,-2,3,-4),**kw)
        def replay(name,groups,bcase=None):
            case=out/(('B_' if bcase else 'A_')+name);case.mkdir();a=model.Adapter(core,name)
            accepted=[]
            for group in groups:
                accepted.append(group);a.push(group)
                if a.fault:break
            if not a.fault:a.stop()
            raw=b''.join(struct.pack('<QiiiiII',x.sample_id,*x.pcm,x.flags,x.reserved) for x in groups)
            meta=b''.join(struct.pack('<I',x.source_flags or int(x.integrity_error)) for x in groups)
            (case/'input.bin').write_bytes(raw);(case/'upstream.bin').write_bytes(meta)
            if bcase:check(digest(raw)==bcase['raw_sha256'],'B input hash')
            summaries=[]
            for index,exe in enumerate(executables):
                fpath=case/f'frames-{index}.bin';epath=case/f'events-{index}.jsonl'
                p=run([exe,'replay',case/'input.bin',case/'upstream.bin',fpath,epath],name+'-'+str(index))
                check(p.returncode==0,'replay failed to execute')
                observed=json.loads(next(x[7:] for x in p.stdout.decode().splitlines() if x.startswith('REPLAY ')))
                check(observed['rows']==str(len(accepted)) and bool(observed['failed'])==a.fault)
                data=fpath.read_bytes();width=160+1024*32;check(len(data)==len(a.frames)*width,(name,'frame count',len(data),len(a.frames)))
                for i,frame in enumerate(a.frames):
                    header=struct.unpack_from('<8Q',data,i*width)
                    want=(1,frame['frame_id'],frame['interval_id'],frame['row_start'],frame['row_stop'],int(frame['first_id']),int(frame['last_id']),int(frame['reset_before']))
                    check(header==want,(name,header,want));check(data[i*width+64:i*width+160]==bytes(range(1,97)))
                    decoded=[struct.unpack_from('<QiiiiII',data,i*width+160+j*32) for j in range(1024)]
                    check(tuple(tuple(x[1:5]) for x in decoded)==frame['pcm'])
                    check([x[0] for x in decoded]==list(range(int(frame['first_id']),int(frame['last_id'])+1)))
                    check(all(x[5:]==(0,0) for x in decoded))
                    if bcase:
                        bf=bcase['frames'][i]
                        for field in ('frame_id','interval_id','row_start','row_stop','reset_before'):check(frame[field]==bf[field],field)
                        check(frame['first_id']==bf['first_sample_id'] and frame['last_id']==bf['last_sample_id'])
                        pcm=np.array(frame['pcm'],dtype='<i4').T.copy()
                        check(np.array_equal(pcm,arrays[name+'_frame_'+str(i)]))
                        check(digest(pcm.tobytes())==bf['pcm_channel_major_i32_sha256'])
                ev=[json.loads(x) for x in epath.read_text().splitlines()];errors=[e for e in ev if e['kind']==1]
                check(len(errors)==len(a.events))
                for actual,expected in zip(errors,a.events):
                    check(int(actual['row'])==expected['row'] and actual['id']==expected['id'])
                    check((actual['previous'] if actual['have_previous'] else None)==expected['previous'])
                    check(actual['reasons']==sum(REASONS[x] for x in expected['reasons']))
                    check(actual['flags']==expected['raw_flags'] and bool(actual['fatal'])==expected['fatal'])
                if not a.fault:
                    stop=[e for e in ev if e['kind']==2];check(len(stop)==1)
                    check(stop[0]['unused_tail']==a.core.events[-1].unused_tail)
                if index:
                    check(data==(case/'frames-0.bin').read_bytes() and epath.read_bytes()==(case/'events-0.jsonl').read_bytes(),'optimization/sanitizer output changed')
                summaries.append(observed)
            save(str(case.relative_to(out))+'/comparison.json',dict(frames=len(a.frames),events=a.events,raw_sha256=digest(raw),runs=summaries,oracle='pinned A accepted-row model; frozen B NPZ when specified'))
            return dict(groups=len(groups),accepted=len(accepted),frames=len(a.frames),error_events=len(a.events),builds=len(executables))
        for c in gold['cases']:
            name=c['session_id']
            if name=='s1':continue
            groups=[G((1<<53)+17+j+(7 if name=='gap4000' and j>=1500 else 0),(j-20000,3*j+40000,-5*j+100000,7*j-150000),4 if name=='clip3500' and j==1250 else 0) for j in range(c['groups'])]
            test('B/'+name,lambda n=name,x=groups,c=c:replay(n,x,c))
        cases={
            'zero':[], 'short1023':[g(i) for i in range(1023)],'exact1024':[g(i) for i in range(1024)],
            'before1535':[g(i) for i in range(1535)],'exact1536':[g(i) for i in range(1536)],'multi2048':[g(i) for i in range(2048)],
            'repeated_gap':[g(100),g(103,flags=1),g(105),g(106)]+[g(i) for i in range(107,1130)],
            'all_error':[g(i,flags=1) for i in range(30)],
            'continuous_clip':[g(0)]+[g(i,flags=2) for i in range(1,9)]+[g(i) for i in range(9,1545)],
            'duplicate':[g(2),g(2)],'reverse_after_clip':[g(10,flags=1),g(9)],'wrap':[g((1<<64)-1),g(0)],
            'max_id_frame':[g(i) for i in range((1<<64)-1024,1<<64)],
            'error_code_only':[g(0,source_flags=12)],'integrity_only':[g(0,integrity_error=True)],
            'union':[g(0),G(0,(8388608,-2,3,-4),17,1,False,9)],
            'invalid_flags':[g(0,flags=16)],'reserved':[g(0,reserved=1)],
            's24_edges':[G(i,(-8388608,8388607,-1,0)) for i in range(1536)],
            'bad_signext':[G(0,(16777215,0,0,0))],
            'int32_min':[G(0,(-(1<<31),0,0,0))],
            'int32_max':[G(0,((1<<31)-1,0,0,0))],
            'upstream_high_bit':[g(0,source_flags=1<<31)],
        }
        for name,groups in cases.items():test('A/'+name,lambda n=name,x=groups:replay(n,x))
        def original_counterexamples():
            f=core.Framer();f.start(1)
            for i in range(1024):f.push(g(i,flags=1 if i==511 else 0))
            check(len(f.frames)==1)
            a=model.Adapter(core)
            for i in range(1024):a.push(g(i,flags=1 if i==511 else 0))
            check(len(a.frames)==0)
            replay('old_clip_counterexample',[g(i,flags=1 if i==511 else 0) for i in range(1024)])
            f=core.Framer();f.start(1)
            for x in [g(100),g(103),g(105),g(106)]:f.push(x)
            check([e.sample_id for e in f.events]==[103])
            return dict(original_clip_frames=1,C_frames=0,original_gap_events=[103],C_gap_events=[103,105],expected_original_mismatch=True)
        test('preserved_original_counterexamples',original_counterexamples)
        save('summary.json',dict(tests=len(tests),passed=sum(x['status']=='PASS' for x in tests),failed=sum(x['status']=='FAIL' for x in tests),
             C_selftest_groups_per_build=9,builds=len(executables),sanitizers=sanitizer,
             ARM='NOT_RUN',BSP='NOT_RUN',board='NOT_RUN',realtime='REALTIME_BLOCKED',host_timing='observation only, not Cortex-A9 WCET'))
        check(all(x['status']=='PASS' for x in tests),'comparison failures retained')
        print('HOST_C_CANDIDATE_PASS_NOT_ARM_NOT_BOARD',len(tests),flush=True)
        return 0
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');print(traceback.format_exc(),file=sys.stderr);return 1

if __name__=='__main__':raise SystemExit(main())
