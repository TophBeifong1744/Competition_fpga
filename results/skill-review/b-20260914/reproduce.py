"""Replay observed review defects against exact candidates; never approves a fix.

python -B reproduce.py --skl001-root <checkout> --skl002-root <checkout> \
  --vivado-bin <Vivado2025.2/bin> --output <new-directory>
"""
import argparse,json,pathlib,subprocess,sys
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--skl001-root',type=pathlib.Path,required=True)
p.add_argument('--skl002-root',type=pathlib.Path,required=True)
p.add_argument('--vivado-bin',type=pathlib.Path,required=True)
p.add_argument('--output',type=pathlib.Path,required=True)
a=p.parse_args();root=pathlib.Path(__file__).resolve().parent
for checkout,sha in [(a.skl001_root,'c562466805aff08201cd457cc2e6ee7464a3566f'),(a.skl002_root,'55039cf8bfab2bd6112192c8bd646d427a52a642')]:
 actual=subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD']).decode().strip()
 if actual!=sha:p.error('Use the exact reviewed checkout; a new SHA needs a new review: '+actual)
a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
records=[]
def run(label,cmd,cwd,code,status,result):
 with (a.output/(label+'.stdout.log')).open('wb') as o,(a.output/(label+'.stderr.log')).open('wb') as e:
  r=subprocess.run(cmd,cwd=cwd,stdout=o,stderr=e)
 observed=json.loads(result.read_bytes()) if result.exists() else {}
 record=dict(label=label,command=cmd,cwd=str(cwd),exit_code=r.returncode,status=observed.get('status'),expected_observation=status,matched=r.returncode==code and observed.get('status')==status)
 records.append(record)
 (a.output/'replay.json').write_text(json.dumps(dict(meaning='Reproduces observed results, including false PASS. NOT approval.',records=records),indent=2))
 print(json.dumps(record))
runner=a.skl001_root.resolve()/'skill/fpga-module-verification/scripts/run_xsim.py'
for label,case,status,code in [('candidate-tb-two-stages','latency-mutant','PASS_SIMULATION',0),('b-tb-original','b-latency-original','PASS_SIMULATION',0),('b-tb-two-stages','b-latency-two-stage','FAIL_SIMULATION',1)]:
 target=a.output/label
 cmd=[sys.executable,'-B',str(runner),'--case',str(root/case/'case.json'),'--vivado-bin',str(a.vivado_bin.resolve()),'--output',str(target)]
 run(label,cmd,a.skl001_root.resolve(),code,status,target/'result.json')
validator=a.skl002_root.resolve()/'skill/pynq-overlay-dma-validation/scripts/validate_profile.py'
fixtures=root/'skl002-independent/thermal'
for label,profile,ev in [('missing-dma-ip','missing-dma-ip.json',None),('missing-control-ip','missing-control-ip.json',None),('duplicate-run','profile.json','duplicate-evidence.json')]:
 target=a.output/(label+'.json')
 cmd=[sys.executable,'-B',str(validator),'--profile',str(fixtures/profile),'--mode','offline','--output',str(target)]
 if ev:cmd+=['--evidence',str(fixtures/ev)]
 run(label,cmd,a.skl002_root.resolve(),0,'PASS',target)
sys.exit(0 if all(r['matched'] for r in records) else 1)
