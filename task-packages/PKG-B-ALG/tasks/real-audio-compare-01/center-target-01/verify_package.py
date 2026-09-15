"""Check committed delivery bindings; does not grant acoustic acceptance."""
import argparse
import json
from pathlib import Path
import render_center as renderer

HERE=Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def check(condition, message):
    if not condition: raise ValueError(message)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--create-manifest',action='store_true')
    args=ap.parse_args()
    manifest=HERE/'MANIFEST.json'
    if args.create_manifest:
        check(not manifest.exists(),'manifest already exists')
        files=sorted(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
        with manifest.open('x',encoding='utf-8') as f:
            json.dump({p.relative_to(HERE).as_posix():renderer.base.sha(p) for p in files},f,indent=2)
            f.write('\n')
    hashes=read(manifest)
    for name,want in hashes.items():
        check(renderer.base.sha(HERE/name)==want,'package file mismatch: '+name)
    cfg=read(HERE/'config.json')
    pins=renderer.verify_pins(cfg)
    report=read(HERE/'evidence/audio-run01/result.json')
    check(report['pins']==pins,'render input pins differ')
    check(report['config']==cfg,'render configuration differs')
    check(report['render_config']==read(HERE/'render-config.json'),'render settings differ')
    for name,want in report['source_sha256'].items():
        check(renderer.base.sha(renderer.base.ROOT/name)==want,'source mismatch: '+name)
    for row in report['records']:
        check(len(row['files'])==4,'four paired output files required')
        check({(f['branch'],f['mode']) for f in row['files']}==
              {('single','raw'),('single','preview'),('manual','raw'),('manual','preview')},'output roles differ')
        check(len({f['frames'] for f in row['files']})==1,'output lengths differ')
        for f in row['files']:
            check(renderer.base.sha(HERE/'evidence/audio-run01'/f['file'])==f['sha256'],'audio hash mismatch')
    listening=read(HERE/'evidence/listening-01.json')
    check(listening['recording']==cfg['recording'],'wrong listening recording')
    for name,want in listening['presented_files'].items():
        check(renderer.base.sha(HERE/'evidence'/name)==want,'listening audio mismatch')
    audit=read(HERE/'evidence/audit-01.json')
    check(audit['audit_source_sha256']==renderer.base.sha(HERE/'audit_audio.py'),'audit source changed')
    check(audit['status']=='AUTHOR_CROSSCHECK_PASS','audit did not pass')
    print(f'PASS: {len(hashes)} package files, {len(pins)} input/dependency pins, 4 WAVs and new listening bindings verified.')

if __name__=='__main__': main()
