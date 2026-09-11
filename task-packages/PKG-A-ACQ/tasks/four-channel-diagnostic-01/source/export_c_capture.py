"""Verify a complete user capture/log pair, then reuse the existing H1 exporter."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from export_four import decode, export

CONFIG = 'four-channel-c-adapter-v1'

def verify(raw, serial):
    if len(raw)!=1024000:
        raise ValueError('Expected exactly 1024000 bytes; keep original/failed dump')
    if 'FOUR_CAPTURE_FAIL' in serial or serial.count('FOUR_CAPTURE_INTEGRITY_PASS')!=1:
        raise ValueError('Need one complete successful acquisition, not mixed or failed sessions')
    if serial.count('FOUR PDM capture '+CONFIG)!=1:
        raise ValueError('Missing/wrong/duplicate capture configuration header')
    if not re.search(r'FOUR_CAPTURE_INTEGRITY_PASS groups=32000 bytes=1024000 packets=128\b',serial):
        raise ValueError('Capture count mismatch')
    packets=re.findall(r'DONE packet=(\d+) actual_bytes=(\d+) DMA_SR=([0-9a-fA-F]{8})',serial)
    if len(packets)!=128 or any(int(p)!=i or int(n)!=8000 or int(sr,16)&0x4770 or not int(sr,16)&0x1000 for i,(p,n,sr) in enumerate(packets)):
        raise ValueError('Incomplete/mixed packet log or DMA error')
    final=re.search(r'DMA_SR=([0-9a-fA-F]{8}) SOURCE_STATUS=([0-9a-fA-F]{8}) sync_error=0 overflow=0 fnv1a32=([0-9a-fA-F]{8})',serial)
    if not final or int(final[1],16)&0x4770 or int(final[2],16)&0xffff0025 or not int(final[2],16)&8:
        raise ValueError('Source/DMA status not complete and clean of fatal errors')
    digest=2166136261
    for byte in raw:
        digest=((digest^byte)*16777619)&0xffffffff
    if digest!=int(final[3],16):
        raise ValueError('BIN/serial FNV mismatch: wrong or stale dump')
    rows=decode(raw)
    ids=re.search(r'first_id_hex=([0-9a-fA-F]{16}) last_id_hex=([0-9a-fA-F]{16})',serial)
    if not ids or [rows[0][0],rows[-1][0]]!=[int(ids[1],16),int(ids[2],16)] or any(row[0]!=rows[0][0]+i for i,row in enumerate(rows)):
        raise ValueError('Capture ID mismatch/gap')
    return digest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw',type=Path)
    parser.add_argument('serial',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--acquisition-id',required=True)
    parser.add_argument('--operator',required=True)
    parser.add_argument('--scene',required=True)
    parser.add_argument('--numbered-mating-confirmed',action='store_true')
    args=parser.parse_args()
    if not args.numbered_mating_confirmed:
        parser.error('User must confirm numbered connector mating, no camera conflict, correct power/ground before declaring hardware audio')
    raw=args.raw.read_bytes()
    serial=args.serial.read_text(encoding='utf-8-sig')
    fnv=verify(raw,serial)
    mapping=json.loads(Path(__file__).with_name('c_adapter_mapping.json').read_text(encoding='utf-8'))
    meta=export(args.raw,args.output,acquisition_id=args.acquisition_id,config_version=CONFIG,
        source_kind='hardware-audio',provenance=f'User-declared board capture; operator={args.operator}; scene={args.scene}; paired full UART log and DDR BIN verified',
        capture_point='four PDM -> unchanged CIC3 R64 gain32 signed24 -> 8-word record -> AXI DMA S2MM -> DDR -> JTAG BIN')
    meta['adapter_interface']=mapping
    meta['geometry_version']='c-adapter-unmeasured-v1'
    meta['provisional_fields']['channel_order']='Configured DATA1..4 mapping plus user-confirmed numbered mating; acoustic lane identity not independently measured.'
    meta['recording_notes']={'operator':args.operator,'scene':args.scene,'numbered_mating':'user-confirmed','fnv1a32':f'{fnv:08X}'}
    meta['serial_sha256']=hashlib.sha256(args.serial.read_bytes()).hexdigest()
    (args.output/'serial.log').write_bytes(args.serial.read_bytes())
    (args.output/'metadata.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('CAPTURE_EXPORT_INTEGRITY_PASS_NOT_ACOUSTIC_ACCEPTANCE',len(raw),f'{fnv:08X}')
