"""Additional exact archived-link comparator negatives; no compiler execution."""
import argparse
import json
from pathlib import Path
import sys

p = argparse.ArgumentParser()
p.add_argument('--package', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(a.package))
import check_entry as g

app = Path(g.POLICY['reference_app'])
bsp = Path(g.POLICY['reference_bsp'])
archive = json.loads((a.package / 'user-build-20260916-01/verification-01/ninja-commands.json').read_text())['stdout']
token = '-Wl,"' + app.as_posix() + '/src/lscript.ld"'
results = []
for flags in (',-e,0x01000000', ',--defsym,REVIEW_MARKER=1', ',--wrap=XAxiDma_SimpleTransfer'):
    replacement = token[:-1] + flags + ',-L,/../lscript.ld"'
    altered = archive.replace(token, replacement)
    try:
        accepted = g.verify_link_output(altered, app, bsp)
        status = 'ACCEPTED'
    except ValueError as e:
        status = 'REJECTED: ' + str(e)
    results.append({'extra_linker_flags': flags, 'modified_token': replacement,
                    'status': status, 'expected': 'REJECTED'})
(a.output / 'result.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
