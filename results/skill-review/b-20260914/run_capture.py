import datetime,json,pathlib,subprocess,sys,time
root=pathlib.Path(__file__).parent
label,cwd,*cmd=sys.argv[1:]
p=root/label;p.mkdir(parents=True,exist_ok=False)
t=time.time()
with (p/'stdout.log').open('wb') as o,(p/'stderr.log').open('wb') as e:
    r=subprocess.run(cmd,cwd=cwd,stdout=o,stderr=e)
record=dict(command=cmd,cwd=cwd,exit_code=r.returncode,started_utc=datetime.datetime.fromtimestamp(t,datetime.timezone.utc).isoformat(),elapsed_seconds=time.time()-t)
(p/'command.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record))
print((p/'stdout.log').read_text(encoding='utf-8',errors='replace')[-2500:])
print((p/'stderr.log').read_text(encoding='utf-8',errors='replace')[-2500:])
sys.exit(r.returncode)
