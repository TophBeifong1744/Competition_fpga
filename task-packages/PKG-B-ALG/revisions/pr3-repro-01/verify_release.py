"""Fail closed on missing/corrupt declared historical or revision files."""
from common import HERE, read, verify_entries, verify_package
import json

def check():
    result=verify_package()
    manifest=read(HERE/'files.json')
    verify_entries(HERE,manifest['files'])
    return result|dict(revision_files=len(manifest['files']))

if __name__=='__main__':print(json.dumps(check(),ensure_ascii=False,indent=2))
