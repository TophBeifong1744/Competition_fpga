"""Adapt only B's final expectation; original script is retained byte-for-byte."""
import hashlib
from pathlib import Path
import sys
entry=Path(__file__).resolve().parents[1]
script=Path(__file__).resolve().parent/'review-inputs/negative_contract_checks.py'
source=script.read_text()
old="assert all(row['actual'] in ('ACCEPTED', 'EQUAL') for row in rows), 'Review result changed; inspect evidence'"
new="assert all(row['actual'].startswith('REJECTED:') or row['actual']=='DIFFERENT' for row in rows), 'Repair regression failed'"
assert source.count(old)==1
sys.argv=[str(script),str(entry),sys.argv[1]]
exec(compile(source.replace(old,new),str(script)+' [only final assertion adapted]','exec'),{'__file__':str(script),'__name__':'__main__'})
