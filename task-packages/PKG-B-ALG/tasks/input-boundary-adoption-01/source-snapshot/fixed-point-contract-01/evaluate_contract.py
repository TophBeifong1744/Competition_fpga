"""Validate draft fields and calculate format-dependent lower storage inventory.
Unspecified engineering parameters remain null, never silently defaulted.
"""
import argparse,hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def storage(count,width):
    bucket=next((w for w in [8,16,32,64,128,256] if width<=w),None)
    assert bucket is not None
    return dict(elements=count,element_bits=width,bit_packed_bytes=math.ceil(count*width/8),
                byte_aligned_element_bytes=count*math.ceil(width/8),software_container_bytes=count*bucket//8)
def evaluate(config):
    assert config['status']=='DRAFT_NOT_FROZEN'
    k=config['known'];assert (k['channels'],k['sample_rate_hz'],k['frame_samples'],k['hop_samples'])==(6,48000,1024,512)
    ledger=read(HERE.parent/'implementation-budget-01/evidence/run02/ledger.json')
    result=[]
    for candidate in config['candidates']:
        formats=candidate['formats'];ranges={}
        for name,f in formats.items():
            if f is None:continue
            assert type(f['W']) is int and type(f['F']) is int and type(f['signed']) is bool
            assert f['W']>0 and 0<=f['F']<f['W']
            low=-(2**(f['W']-1)) if f['signed'] else 0
            high=2**(f['W']-int(f['signed']))-1
            ranges[name]=dict(min=low/2**f['F'],max=high/2**f['F'],lsb=2.**(-f['F']))
        assert formats['cross_component']['W']>=2*formats['fft_component']['W']+1
        assert formats['cross_component']['F']==2*formats['fft_component']['F']
        assert formats['audio_accumulator']['W']>=formats['pcm']['W']+formats['audio_weight']['W']+math.ceil(math.log2(54))
        assert ranges['audio_weight']['max']>=1
        p=formats['pcm']['W'];f=formats['fft_component']['W'];z=formats['cross_component']['W'];g=formats['phat_component']['W'];h=formats['hann']['W'];d=formats['delay_samples']['W'];a=formats['audio_weight']['W']
        inventory={
            'six_channel_frame_ring':storage(6*1024,p),'new_hop_pingpong':storage(2*6*512,p),
            'six_fft_spectra_components':storage(6*513*2,f),'one_pair_cross_components':storage(513*2,z),
            'one_pair_normalized_components':storage(513*2,g),'pair_mask':storage(513,1),
            'one_pair_correlation':storage(1024,formats['correlation']['W']),'delays':storage(15,d),
            'hann':storage(1024,h),'audio_history':storage(8*6,p),'audio_four_weights':storage(4*6*9,a),
            'mono_hop_pingpong':storage(2*512,p)}
        totals={key:sum(v[key] for v in inventory.values()) for key in ['bit_packed_bytes','byte_aligned_element_bytes','software_container_bytes']}
        result.append(dict(name=candidate['name'],ranges=ranges,partial_inventory=inventory,partial_totals=totals,
            omitted=['magnitude workspace width unknown','FFT/IFFT internal RAM','LS/rank workspace','DMA/AXI FIFO and alignment','block exponent arrays','logs and runtime metadata']))
    clock=config['pending_A']['processing_clock_hz'];fft=config['pending_A']['fft_cycles_per_transform'];ifft=config['pending_A']['ifft_cycles_per_transform']
    for value in [clock,fft,ifft]:assert value is None or (type(value) in [int,float] and math.isfinite(value) and value>0)
    return dict(status='VALID_DRAFT_NOT_FIXED_POINT_ACCEPTANCE',known=k,pending_A=config['pending_A'],candidates=result,
        operations_per_frame=ledger['worst_per_frame'],audio_operations=ledger['audio'],
        cycles_available_per_hop=None if clock is None else clock*512/48000,
        serial_fft_ifft_cycles=None if fft is None or ifft is None else 6*fft+15*ifft,
        schedule_warning='Cycle expression only if transforms are serialized on one engine. Overlap, stalls, scaling and other computation still required.',
        selected_candidate=config['arithmetic_candidates']['selected_candidate'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=HERE/'contract.json');p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    result=evaluate(read(args.config))
    result['sources']={args.config.name:sha(args.config),'evaluate_contract.py':sha(Path(__file__)),
        'budget_ledger_sha256':sha(HERE.parent/'implementation-budget-01/evidence/run02/ledger.json')}
    (args.out/'draft-evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],cycles_available=result['cycles_available_per_hop'],candidates=[dict(name=r['name'],partial_totals=r['partial_totals']) for r in result['candidates']]),ensure_ascii=False))
if __name__=='__main__':main()
