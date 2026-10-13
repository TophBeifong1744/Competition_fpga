"""Freeze exact C-to-A increment; never modify the native Vivado checkout.

Run: python simulation/package_i17_continuous.py
Output: deliverables/i17-continuous-control-20261013-<content-id>.zip + sha256.
Next: A integrates the seven RTL sources in the existing project per README.
"""
from pathlib import Path
import csv
import difflib
import hashlib
import json
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/evidence/issue19-continuous-control-20261013'
RUNS=ROOT/'codex_out/i17-continuous-control-20261013/runs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def package():
    rtl=json.loads((DOC/'candidate-files.json').read_text())['rtl']
    native=json.loads((ROOT/'codex_out/i17-continuous-control-20261013/preimages.json').read_text())
    (DOC/'patches').mkdir(exist_ok=True)
    for item in native:
        before=Path(item['native']);after=ROOT/item['target']
        if sha(before)!=item['preimage_sha256']:raise RuntimeError('native preimage changed: '+str(before))
        item['candidate_sha256']=sha(after)
        diff=''.join(difflib.unified_diff(before.read_text().splitlines(True),after.read_text().splitlines(True),
            fromfile='native/'+before.name,tofile=item['target']))
        (DOC/'patches'/f'{before.name}.patch').write_text(diff,encoding='utf-8')
    write(DOC/'preimages.json',native)
    for item in json.loads((DOC/'reference-manifest.json').read_text()):
        if sha(DOC/item['path'])!=item['sha256']:raise RuntimeError('reference changed: '+item['path'])
    chosen=['control-7','export-1','watchdog-2','canary_export-1','full_probe-1','full_stop-5','full_stall-1','full_first-1','full_noise-1']
    checks=[]
    for name in chosen:
        folder=RUNS/name
        if not (folder/'run.json').exists():continue
        record=json.loads((folder/'run.json').read_text())
        match=all(Path(p).is_file() and sha(Path(p))==h for p,h in record['sources'].items())
        stopped=(folder/'external-stop.json').exists()
        stopped_record=json.loads((folder/'external-stop.json').read_text()) if stopped else {}
        verdict=stopped_record['verdict'] if stopped else record.get('verdict','RUNNING')
        summary={'run':name,'verdict':verdict,'source_matches_current':match,
            'scope':record['scope'],'stages':record['stages']}
        checks.append(summary)
        if 'verdict' not in record and not stopped:continue
        for log_name,h in (stopped_record if stopped else record).get('logs',{}).items():
            p=folder/log_name
            if not p.is_file() or sha(p)!=h:raise RuntimeError('evidence log changed: '+str(p))
        target=DOC/'originals'/name;target.mkdir(parents=True,exist_ok=True)
        for p in [folder/'run.json',*folder.glob('*.log'),*folder.glob('events.csv'),*folder.glob('external-stop.json')]:
            if p.is_file():(target/p.name).write_bytes(p.read_bytes())
        # Retain the old frozen source for explicit mismatched/failed evidence.
        if not match:
            for p in (folder/'sources').glob('*'):
                if p.suffix in ('.sv','.v'):
                    q=target/'sources'/p.name;q.parent.mkdir(exist_ok=True);q.write_bytes(p.read_bytes())
    natural=next((x for x in checks if x['run']=='full_noise-1'),{})
    natural_ok=natural.get('verdict')=='FUNCTIONAL_SIM_PASS' and natural.get('source_matches_current')
    observations=[]
    if natural.get('verdict')!='RUNNING' and (RUNS/'full_noise-1/events.csv').is_file():
        for row in csv.reader((RUNS/'full_noise-1/events.csv').read_text().splitlines()):
            if row and row[0]=='REPORT':
                identity=int(row[5],16)
                observations.append({'cycle':int(row[1]),'angle_q8':int(row[2]),'angle_deg':int(row[3]),
                    'eligible':int(row[4]),'sid':(identity>>432)&0xffffffff,
                    'generation':(identity>>597)&((1<<64)-1),'identity_hex':row[5]})
        write(DOC/'natural-observations.json',{'source_csv_sha256':sha(RUNS/'full_noise-1/events.csv'),
            'scope':'RTL observations, not measured acoustic direction or physical motion','reports':observations})
    # 额外核真实新SID报告资格，避免只有重启事件却没有恢复方向交付被写成通过。
    restart_qualified=bool(observations and observations[-1]['sid']==4 and observations[-1]['eligible']==1)
    natural_ok=natural_ok and restart_qualified
    write(DOC/'validation.json',{'status':'RTL_THREE_NATURAL_REPORTS_STOP_RESTART_PASS' if natural_ok else 'CONTROL_UNIT_PASS_FULL_CHAIN_UNVERIFIED',
        'checks':checks,'restart_report_qualified':restart_qualified,
        'natural_scope':'Three reports, >=2 motor commands, diagnostic consumption, general in-flight STOP, held STOP, warm recovery and qualified new SID first report',
        'whole_chain_9m_cycles':'UNVERIFIED','stop_during_active_fft_ifft':'UNVERIFIED',
        'default_warmup':'UNVERIFIED','physical_resources_sta_cdc':'NOT_RUN',
        'board_follow_stop_restart':'NOT_RUN','pynq':'UNVERIFIED','a_integrated':'UNVERIFIED'})
    inputs={p:sha(ROOT/p) for p in rtl}
    identifier=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    write(DOC/'candidate-manifest.json',{'rtl_content_id':identifier,'rtl':inputs,
        'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'part':'xc7z020clg400-1','tool':'Vivado 2025.2','clock_hz':61440000,
        'native_project_written':False,'physical_build_run':False})
    # 中文用途：交接表只转录原件判定；失败、运行中和错候选不能合并成PASS。
    table=['# 准确候选验证摘要','',f'七产品源内容ID：`{identifier}`。','',
        '| 原件运行 | 实际判定 | 全部冻结源匹配当前 |', '|---|---|---|']
    table += [f"| {x['run']} | {x['verdict']} | {x['source_matches_current']} |" for x in checks]
    table += ['', '局部控制、导出背压、watchdog及检查器canary按各自原件复用；不因包装重新运行。',
        'full_first 的资格Fatal保留为SIM_FAIL；两次长测主动停止保留中断，不作PASS。',
        'full_noise若通过，只覆盖三自然报告、至少两条实际转台命令、记录消费、一般在途STOP、保持STOP、warm恢复及新SID首结果。',
        '9M整链、活动FFT/IFFT中STOP、默认4096 warmup、全板资源/STA/CDC、实板与PYNQ均未获得通过证据。',
        '各运行完整配置、冻结源哈希、阶段与日志哈希见originals；范围判定见validation.json与review.md。','']
    (DOC/'validation-summary.md').write_text('\n'.join(table),encoding='utf-8')
    assets=[ROOT/p for p in rtl]+[ROOT/'simulation/run_i17_continuous.py',Path(__file__).resolve(),
        *sorted((ROOT/'simulation/tb/c_board').glob('tb_i17_*.sv')),*sorted(p for p in DOC.rglob('*') if p.is_file())]
    manifest={p.relative_to(ROOT).as_posix():sha(p) for p in assets}
    if len(manifest)!=len(assets):raise RuntimeError('duplicate package path')
    payload_id=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()[:8]
    output=ROOT/'deliverables'/f'i17-continuous-control-20261013-{identifier[:12]}-{payload_id}.zip'
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        for p in assets:archive.write(p,p.relative_to(ROOT).as_posix())
        archive.writestr('SHA256SUMS.json',json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(output) as archive:
        for name,h in manifest.items():
            if hashlib.sha256(archive.read(name)).hexdigest()!=h:raise RuntimeError('ZIP mismatch: '+name)
    output.with_suffix('.sha256').write_text(sha(output)+'  '+output.name+'\n',encoding='ascii')
    print(json.dumps({'path':str(output),'sha256':sha(output),'entries':len(manifest),
        'rtl_content_id':identifier,'status':json.loads((DOC/'validation.json').read_text())['status']},indent=2))

if __name__=='__main__':package()
