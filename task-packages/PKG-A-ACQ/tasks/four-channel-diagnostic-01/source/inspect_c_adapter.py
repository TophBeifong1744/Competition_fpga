"""Read the selected EPRO2 only; emit minimal connector evidence, not ERC/DRC."""
import argparse
import hashlib
import json
import math
import zipfile
from pathlib import Path

EXPECTED_SHA = '80ec1919164c3c65ec7ab5e59674ca3a8f2cb67fa497b7656d67f9aea1a43f30'
EXPECTED = {'17':'DATA1','19':'DATA2','21':'CLK1','23':'CLK2',
            '29':'CLK3','31':'CLK4','33':'DATA3','35':'DATA4',
            '37':'GND','38':'3.3V','39':'GND','40':'5V'}

def inspect(path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA:
        raise ValueError('Selected board changed: recheck source before using pin table')
    with zipfile.ZipFile(path) as archive:
        names = [n for n in archive.namelist() if n.endswith('.epru')]
        if len(names) != 1:
            raise ValueError('Ambiguous project')
        source = archive.read(names[0]).decode('utf-8')
    docs, current = {}, None
    for line in source.splitlines():
        if '||' not in line:
            continue
        head, body = line.split('||', 1)
        body = body.removesuffix('|')
        if not body:
            continue
        head, body = json.loads(head), json.loads(body)
        if head['type'] == 'DOCHEAD':
            current = {'header':body, 'records':[]}
            docs[body['uuid']] = current
        else:
            current['records'].append((head, body))
    pcbs = [d for d in docs.values() if d['header']['docType']=='PCB']
    if len(pcbs)!=1:
        raise ValueError('Ambiguous PCB')
    records = pcbs[0]['records']
    attrs = {}
    for head, body in records:
        if head['type']=='ATTR':
            attrs.setdefault(body['parentId'], {})[body['key']] = body['value']
    result = {}
    for head, body in records:
        if head['type']!='COMPONENT':
            continue
        ident = head['id']
        a = attrs.get(ident, {})
        if a.get('Designator') not in ('U1','U2'):
            continue
        nets = {}
        for h, b in records:
            if h['type']=='PAD_NET':
                key = json.loads(h['id'])
                if key[1]==ident:
                    nets[key[2]] = b['padNet']
        assert {k:nets.get(k) for k in EXPECTED} == EXPECTED
        pads = {}
        theta = math.radians(body['angle'])
        for h, b in docs[a['Footprint']]['records']:
            if h['type']=='PAD' and b['num'] in ('1','2','37','38','39','40'):
                x,y = b['centerX'],b['centerY']
                pads[b['num']] = {'footprint_xy_native':[x,y],
                    'pcb_xy_native':[round(body['x']+x*math.cos(theta)-y*math.sin(theta),4),
                                     round(body['y']+x*math.sin(theta)+y*math.cos(theta),4)],
                    'shape':b['defaultPad']['padType']}
        result[a['Designator']] = {'layer':body['layerId'],'angle':body['angle'],
            'footprint':a['Footprint'],'selected_nets':{k:nets[k] for k in EXPECTED},
            'orientation_anchors':pads}
    assert set(result)=={'U1','U2'}
    return {'result':'SOURCE_NET_CHECK_PASS_NOT_ASSEMBLY_TEST','source_sha256':digest,
        'connectors':result,
        'mating_contract':'C connector numbered pin N to baseboard J4 numbered pin N; never infer left/right from opposite-face views.',
        'physical_installation':'Not observed. User must match pin1 and 37/38/39/40 power anchors before powering.',
        'scope':'PCB net and footprint records only; not native ERC/DRC, manufactured connectivity or geometry measurement.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    report=inspect(args.source)
    with args.output.open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2,ensure_ascii=False)
        f.write('\n')
    print(report['result'])
