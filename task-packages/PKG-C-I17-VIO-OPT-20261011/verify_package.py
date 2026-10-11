"""只读核验源交接包；不生成工程、不运行 EDA、不操作板卡。"""
from pathlib import Path
import hashlib, json, sys
root=Path(__file__).resolve().parent

def fail(message):
    raise ValueError(message)

def relative(value):
    p=Path(value)
    if p.is_absolute() or '..' in p.parts:
        fail('UNSAFE_PATH '+value)
    q=(root/p).resolve()
    if root not in q.parents:
        fail('OUTSIDE_PACKAGE '+value)
    return q

try:
    manifest=json.loads((root/'manifest.json').read_text('utf-8'))
    seen=set()
    for record in manifest['files']:
        rel=record['path']
        if rel in seen: fail('DUPLICATE '+rel)
        seen.add(rel)
        data=relative(rel).read_bytes()
        if len(data)!=record['bytes'] or hashlib.sha256(data).hexdigest()!=record['sha256']:
            fail('CONTENT_MISMATCH '+rel)
    source_map=json.loads((root/'source-map.json').read_text('utf-8'))['files']
    for record in source_map:
        data=relative(record['package_path']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=record['sha256']:fail('SOURCE_MAP_MISMATCH '+record['package_path'])
    rtl=[x for x in source_map if x['kind']=='RTL']
    assert len(rtl)==36 and len({Path(x['package_path']).name for x in rtl})==36
    listing=[x.strip() for x in (root/'project/script/src_list.txt').read_text('utf-8').splitlines() if x.strip() and not x.startswith('#')]
    settings=json.loads((root/'project/project-settings.json').read_text('utf-8'))
    assert listing==[x['path'] for x in settings['synthesis_source_order']]
    assert set(listing)=={x['package_path'] for x in rtl}
    assert settings['part']=='xc7z020clg400-1' and settings['top']=='i17_vio_board_top'
    assert len(settings['constraints'])==2
    assert settings['constraints'][1]['used_in']==['implementation']
    assert len(settings['xci_reference_files'])==4
    for rel in settings['xci_reference_files']:
        inst=json.loads(relative(rel).read_text('utf-8'))['ip_inst']
        config=json.loads((root/'project/ip/config'/ (inst['xci_name']+'.json')).read_text('utf-8'))
        params={g:{k:v[0].get('value') for k,v in vals.items()} for g,vals in inst['parameters'].items()}
        assert config['parameters']==params
        assert config['gen_directory']==inst['gen_directory'] and config['reference_only'] is True
        pp=params['project_parameters']
        assert (pp['DEVICE'],pp['PACKAGE'],pp['SPEEDGRADE'])==('xc7z020','clg400','-1')
    assert len((root/'project/data/hann-u18f17.mem').read_text().splitlines())==1024
    print('INTEGRITY_OK files=%d rtl=36 xci_reference=4 xdc=2 hann=1024' % len(seen))
    print('STATIC_ONLY; compilation/synthesis/implementation/board acceptance NOT CLAIMED')
except (ValueError, OSError, KeyError, AssertionError) as exc:
    print('INTEGRITY_FAIL '+str(exc),file=sys.stderr)
    sys.exit(1)
