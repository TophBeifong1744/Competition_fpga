"""Verify delivery files and reused sources against committed hashes."""
import argparse
import json
import run as model

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--create',action='store_true')
    args=ap.parse_args()
    path=model.HERE/'MANIFEST.json'
    if args.create:
        if path.exists(): raise FileExistsError(path)
        dependencies=[model.HERE.parents[1]/'payload/model/python'/n for n in ['h1_reader.py','six_mic_baseline_core.py']]
        dependencies += [model.HERE.parent/p for p in ['phat-fixed-03/integration/chain.py','phat-fixed-03/phat_model.py','fft-window-02/window_model.py','fft-bitexact-01/compare_cmodel.py']]
        files=sorted(p for p in model.HERE.rglob('*') if p.is_file())+dependencies
        model.dump(path,{p.relative_to(model.ROOT).as_posix():model.sha(p) for p in files})
    manifest=json.loads(path.read_text())
    for name,expected in manifest.items():
        assert model.sha(model.ROOT/name)==expected, name
    print(f'PASS: {len(manifest)} delivery/dependency files SHA-256 match (manifest excludes itself).')

if __name__=='__main__': main()
