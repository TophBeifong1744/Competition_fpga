"""Delivery integrity check; SHA equality is not acoustic acceptance."""
import argparse
import json
from pathlib import Path
import check_inputs as inputs

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--create-manifest',action='store_true')
    args=ap.parse_args()
    here=inputs.HERE
    path=here/'MANIFEST.json'
    if args.create_manifest:
        if path.exists(): raise FileExistsError(path)
        files=sorted(p for p in here.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
        data={p.relative_to(here).as_posix():inputs.sha(p) for p in files}
        path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    for name,expected in json.loads(path.read_text(encoding='utf-8')).items():
        if inputs.sha(here/name)!=expected: raise ValueError('DELIVERY_HASH_MISMATCH: '+name)
    report=json.loads((here/'evidence/audio-run01/result.json').read_text(encoding='utf-8'))
    for name,expected in {**report['input_hashes'],**report['sources']}.items():
        if inputs.sha(inputs.ROOT/name)!=expected: raise ValueError('SOURCE_INPUT_MISMATCH: '+name)
    count=0
    for rec in report['records']:
        sizes=set()
        for item in rec['files']:
            file=here/'evidence/audio-run01'/item['file']
            if inputs.sha(file)!=item['sha256']: raise ValueError('AUDIO_HASH_MISMATCH')
            sizes.add(item['frames']);count+=1
        if len(sizes)!=1: raise ValueError('UNALIGNED_OUTPUT_LENGTHS')
    feedback=json.loads((here/'evidence/listening-01.json').read_text(encoding='utf-8'))
    for name,expected in feedback['presented_files'].items():
        if inputs.sha(here/'evidence'/name)!=expected: raise ValueError('LISTENING_FILE_MISMATCH')
    print(f'PASS: delivery manifest, reused sources, frozen inputs, {count} WAVs and listening bindings verified.')

if __name__=='__main__': main()
