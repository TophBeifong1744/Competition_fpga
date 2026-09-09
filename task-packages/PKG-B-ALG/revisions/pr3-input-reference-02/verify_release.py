"""Verify new transport files as well as all previously accepted evidence."""
from pathlib import Path
import reference_inputs as r

def main():
    manifest=r.read(r.HERE/'files.json')
    for relative,digest in manifest.items():assert r.sha(r.HERE/relative)==digest,relative
    old=r.read(r.OLD/'files.json');r.common.verify_entries(r.OLD,old.get('files',old))
    previous=r.common.verify_package();refs=r.References()
    print('PASS',len(manifest),'new revision entries;',len(refs.records),'RIR keys;',len(refs.index['coverage']),'coverage bindings;',previous['unique_frozen_files'],'historical frozen paths')

if __name__=='__main__':main()
