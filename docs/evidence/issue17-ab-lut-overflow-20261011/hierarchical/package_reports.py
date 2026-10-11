"""Index vendor reports and preserve their exact hierarchy values in JSON."""
from pathlib import Path
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parent

def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def write(name, value):
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def parse_hierarchy(stage):
    source = ROOT / f'{stage}_utilization_hierarchical.rpt'
    rows, header, stack = [], None, {}
    for number, line in enumerate(source.read_text(encoding='utf-8').splitlines(), 1):
        if not line.startswith('|') or not line.endswith('|'):
            continue
        fields = line.split('|')[1:-1]
        if fields[0].strip() == 'Instance':
            header = [f.strip() for f in fields]
            continue
        if header is None:
            continue
        assert len(fields) == len(header), (source, number)
        values = dict(zip(header, [f.strip() for f in fields]))
        for column in header[2:]:
            values[column] = int(values[column])
        leading = len(fields[0]) - len(fields[0].lstrip())
        assert leading >= 1 and (leading - 1) % 2 == 0, (number, leading)
        level = (leading - 1) // 2
        label = values['Instance']
        own = label.startswith('(') and label.endswith(')')
        if level == 0:
            path = '.'
        elif own:
            path = stack[level - 1]
        else:
            parent = stack[level - 1]
            path = label if parent == '.' else parent + '/' + label
        if not own:
            stack[level] = path
        rows.append({'source_line': number, 'depth': level, 'row_kind': 'local_only' if own else 'subtree_total', 'instance_path': path, **values})
    assert rows and rows[0]['instance_path'] == '.'
    content = {'source_report': source.name, 'source_sha256': sha(source), 'note': 'Values copied from native report; subtree rows overlap and must not be summed. Parenthesized native rows are direct local usage. No counts reconstructed from RTL.', 'stage': stage, 'rows': rows}
    write(f'{stage}_utilization_hierarchical.json', content)
    return content

def main():
    manifest = json.loads((ROOT / 'input-manifest.json').read_text(encoding='utf-8'))
    protected = []
    for item in manifest['inputs']:
        p = Path(item['path'])
        stat = p.stat()
        assert stat.st_size == item['bytes'] and stat.st_mtime_ns == item['mtime_ns'], str(p)
        assert sha(p) == item['sha256'], str(p)
        protected.append(item['path'])
    summaries = {}
    for stage in ['synth', 'opt']:
        hierarchy = parse_hierarchy(stage)
        with (ROOT / f'{stage}_blackboxes.tsv').open(encoding='utf-8', newline='') as f:
            blackboxes = list(csv.DictReader(f, delimiter='\t'))
        with (ROOT / f'{stage}_primitive_counts_by_parent.tsv').open(encoding='utf-8', newline='') as f:
            primitive_groups = list(csv.DictReader(f, delimiter='\t'))
        root = hierarchy['rows'][0]
        summaries[stage] = {'totals': root, 'blackboxes': blackboxes, 'hierarchy_rows': len(hierarchy['rows']), 'direct_primitive_groups': len(primitive_groups), 'direct_primitive_count': sum(int(r['count']) for r in primitive_groups), 'top_by_logic_luts': sorted([r for r in hierarchy['rows'] if r['row_kind'] == 'subtree_total' and r['instance_path'] != '.'], key=lambda r: r['Logic LUTs'], reverse=True)[:15]}
    write('summary.json', summaries)
    command_prefix = "if([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString() -ne 'X64'){throw 'Unsupported actual OS architecture'}; $env:PROCESSOR_ARCHITECTURE='AMD64'; $env:COMPUTERNAME=[Environment]::MachineName; $env:PATH='C:\\AMDDesignTools\\2025.2\\Vivado\\bin;'+$env:PATH; "
    outputs = []
    names = ['native_help.tcl','native_help.log','native_help.jou','export_reports.tcl','export_reports.log','export_reports.jou','processes-before-export.json','input-manifest.json','package_reports.py','summary.json']
    for stage in ['synth','opt']:
        names += [f'{stage}_{suffix}' for suffix in ['utilization_hierarchical.rpt','utilization_hierarchical.json','utilization_total.rpt','blackboxes.tsv','primitive_counts_by_parent.tsv']]
    for name in names:
        p = ROOT / name
        assert p.is_file()
        outputs.append({'path': name, 'bytes': p.stat().st_size, 'sha256': sha(p)})
    write('run-manifest.json', {'mode': 'ANALYZE', 'primary_writer_mode': 'BUILD_FLOW diagnostics only', 'profile': 'DIAGNOSTIC_SMOKE', 'claim': 'Existing-checkpoint resource-report export only', 'tool': 'Vivado 2025.2 SW6299465 IP6300035 SharedData6298862', 'cwd': ROOT.as_posix(), 'commands': [{'command': command_prefix + 'vivado -mode batch -source native_help.tcl -log native_help.log -journal native_help.jou', 'exit_code': 0}, {'command': command_prefix + 'vivado -mode batch -source export_reports.tcl -log export_reports.log -journal export_reports.jou', 'exit_code': 0}, {'command': 'python package_reports.py', 'exit_code': 0}], 'input_manifest_sha256': sha(ROOT/'input-manifest.json'), 'unchanged_protected_inputs_count': len(protected), 'all_input_bytes_and_mtimes_unchanged': True, 'outputs': outputs, 'limits': ['Synth DCP has four unresolved IP black boxes; its totals exclude those IPs', 'Opt DCP is existing post-opt/pre-place checkpoint, not routed; it is the complete linked-resource baseline', 'Native spreadsheet export is GUI-only in installed help, so no GUI was launched: native full text plus exact-value JSON and primitive TSV were exported', 'Primitive counts are not packed LUT-site counts; use native utilization for LUT resource totals', 'No synthesis, optimization, placement, routing, source/constraint/project changes, checkpoint writes, or IP regeneration performed']})
    print(json.dumps({'totals': {s: v['totals'] for s,v in summaries.items()}, 'blackbox_counts': {s: len(v['blackboxes']) for s,v in summaries.items()}, 'protected_inputs_unchanged': len(protected)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
