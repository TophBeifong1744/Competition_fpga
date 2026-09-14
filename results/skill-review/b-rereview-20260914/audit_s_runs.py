import hashlib,json,pathlib,re,subprocess
R=pathlib.Path(__file__).parent
W=pathlib.Path('F:/NUEC/review-worktrees/b-skl001-a7e1ea9')
SHA='a7e1ea976da91ba735af5c0a79fffdc7d10c121f'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
items=[]
for p in sorted(list((R/'xsim-examples').rglob('result.json'))+list((R/'s-independent').rglob('result.json'))):
    v=json.loads(p.read_text(encoding='utf-8'));checks=[]
    for c in v['commands']:
        checks.append(dict(kind='log',path=c['stage'],passed=h(p.parent/(c['stage']+'.log'))==c['log_sha256']))
        if c['stage']!='simulate':checks.append(dict(kind='tool_stage',path=c['stage'],passed=c['returncode']==0 and not c['timed_out']))
    for s in v['sources']:
        snap=p.parent/s['snapshot'];checks.append(dict(kind='snapshot',path=s['snapshot'],passed=h(snap)==s['sha256'] and snap.read_bytes()==pathlib.Path(s['path']).read_bytes()))
        source=pathlib.Path(s['path'])
        if source.is_relative_to(W):
            data=subprocess.check_output(['git','-C',str(W),'show',SHA+':'+source.relative_to(W).as_posix()])
            checks.append(dict(kind='candidate_git_source',path=source.relative_to(W).as_posix(),passed=data==snap.read_bytes()))
    checks.append(dict(kind='runner',passed=v['runner_sha256']==h(W/'skill/fpga-module-verification/scripts/run_xsim.py')))
    checks.append(dict(kind='tool_version',passed='2025.2' in (p.parent/'version.log').read_text(encoding='utf-8')))
    log=(p.parent/'simulate.log').read_text(encoding='utf-8')
    accounting=re.findall(r'ACCOUNTING width=(\d+) sent=(\d+) consumed=(\d+) discarded=(\d+) pending=(\d+)',log)
    if v['status']=='PASS_SIMULATION' and v['name']=='elastic':
        checks.append(dict(kind='actual_accounting',passed=accounting==[(str(w),'177','176','1','0') for w in (1,8,16)]))
    items.append(dict(path=p.relative_to(R).as_posix(),status=v['status'],stage=v['stage'],checks_count=v.get('checks'),accounting=accounting,checks=checks))
(R/'skl001-result-audit.json').write_text(json.dumps(items,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(runs=len(items),checks=sum(len(i['checks']) for i in items),bad=[i for i in items if not all(c['passed'] for c in i['checks'])]),indent=2))
assert all(all(c['passed'] for c in i['checks']) for i in items)
