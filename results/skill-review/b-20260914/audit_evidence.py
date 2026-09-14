import hashlib,json,pathlib,re,subprocess
R=pathlib.Path(__file__).parent
W1=pathlib.Path('F:/NUEC/review-worktrees/b-skl001-c562466')
W2=pathlib.Path('F:/NUEC/review-worktrees/b-skl002-55039cf')
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
out={}
for name,w,sha,paths in [('skl001',W1,'c562466805aff08201cd457cc2e6ee7464a3566f',['skill/fpga-module-verification','task-packages/PKG-A-SKILLS']),('skl002',W2,'55039cf8bfab2bd6112192c8bd646d427a52a642',['skill/pynq-overlay-dma-validation'])]:
 raw=subprocess.check_output(['git','-C',str(w),'ls-tree','-r','-z',sha,'--',*paths])
 checks=[]
 for e in raw.split(b'\0'):
  if not e:continue
  meta,p=e.split(b'\t');oid=meta.split()[-1].decode();path=p.decode()
  b=(w/path).read_bytes();actual=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
  checks.append(dict(path=path,git_blob=oid,worktree_blob=actual,match=oid==actual))
 out[name+'_tracked_byte_identity']=checks
 diff=subprocess.check_output(['git','-C',str(w),'diff','--name-only','ccaeae1c0ac9be07e006ffed09cb7f16bf064906',sha]).decode().splitlines()
 out[name+'_candidate_scope']=dict(changed_count=len(diff),changed_paths=diff,all_within_scope=all(any(p.startswith(s+'/') for s in paths) for p in diff))
 check=subprocess.run(['git','-C',str(w),'diff','--check','ccaeae1c0ac9be07e006ffed09cb7f16bf064906',sha,'--',*paths],capture_output=True)
 (R/(name+'-diff-check.log')).write_bytes(check.stdout+check.stderr)
 out[name+'_diff_check']=dict(exit_code=check.returncode,lines=len(check.stdout.splitlines()),note='Historical raw logs are not rewritten for whitespace checks.')
manifest=json.loads((W1/'task-packages/PKG-A-SKILLS/manifest.json').read_bytes())
out['skl001_manifest']=[dict(path=e['path'],expected=e['sha256'],actual=h(W1/e['path']),match=h(W1/e['path'])==e['sha256']) for e in manifest['files']]
out['skl001_external_inputs']=[dict(path=e['path'],match=hashlib.sha256((W1/e['path']).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==e['normalized_sha256']) for e in manifest['external_inputs']]
def binding_walk(obj,w,label,result):
 if isinstance(obj,dict):
  if 'source_sha256' in obj:
   result.extend(dict(report=label,path=p,match=h(w/p)==digest,actual=h(w/p),expected=digest) for p,digest in obj['source_sha256'].items())
  for value in obj.values():binding_walk(value,w,label,result)
 elif isinstance(obj,list):
  for value in obj:binding_walk(value,w,label,result)
out['skl002_source_bindings']=[]
for p in (W2/'skill/pynq-overlay-dma-validation/evidence').glob('*.json'):
 binding_walk(json.loads(p.read_bytes()),W2/'skill/pynq-overlay-dma-validation',p.name,out['skl002_source_bindings'])
binding_walk(json.loads((W2/'skill/pynq-overlay-dma-validation/results/b-review-tests.json').read_bytes()),W2/'skill/pynq-overlay-dma-validation','b-review-tests.json',out['skl002_source_bindings'])
out['xsim_bindings']=[]
roots=[W1/'task-packages/PKG-A-SKILLS/evidence',R/'xsim-examples',R/'forward/runs']+list(R.glob('xsim-b-*'))+[R/'xsim-latency-mutant']
for root in roots:
 for p in root.rglob('result.json'):
  d=json.loads(p.read_bytes());base=p.parent;checks=[]
  for s in d.get('sources',[]):checks.append(dict(kind='source',path=s['snapshot'],match=h(base/s['snapshot'])==s['sha256']))
  for c in d.get('commands',[]):
   if 'log_sha256' in c:checks.append(dict(kind='log',path=c['stage']+'.log',match=h(base/(c['stage']+'.log'))==c['log_sha256']))
  for key,filename in [('manifest_sha256','case.json'),('contract_sha256','contract.md')]:
   if key in d:checks.append(dict(kind='input',path=filename,match=h(base/'inputs'/filename)==d[key]))
  out['xsim_bindings'].append(dict(result=str(p),status=d['status'],stage=d['stage'],runner_sha256=d.get('runner_sha256'),checks=checks,all_match=all(c['match'] for c in checks)))
log=R/'xsim-b-golden/simulate.log'
if log.exists():
 rows=re.findall(r'^B_RESULT a=(-?\d+) b=(-?\d+) y=([0-9a-fA-F]{2})$',log.read_text(),re.M)
 assert len(rows)==65536,len(rows)
 assert all((int(a),int(b))==(-128+i//256,-128+i%256) for i,(a,b,y) in enumerate(rows))
 actual=bytes(int(y,16) for a,b,y in rows);expected=(R/'b-golden/golden.bin').read_bytes()
 (R/'b-golden/observed.bin').write_bytes(actual)
 mismatches=[i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
 out['independent_numeric_golden']=dict(count=len(rows),mismatch_count=len(mismatches),first_mismatch=mismatches[:1],expected_sha256=hashlib.sha256(expected).hexdigest(),observed_sha256=hashlib.sha256(actual).hexdigest(),source_log=str(log))
(R/'evidence-audit.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
for key,value in out.items():
 if isinstance(value,list):print(key,'count',len(value),'mismatches',sum(not x.get('match',x.get('all_match',True)) for x in value))
 else:print(key,value if 'changed_paths' not in value else {k:v for k,v in value.items() if k!='changed_paths'})
