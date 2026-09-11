"""Check transcribed resource numbers against saved raw Vivado reports."""
import json
from pathlib import Path
import re

R=Path(__file__).resolve().parent.parent/'evidence/run01/reports'


def util(text, label):
    m=re.search(r'\|\s*'+re.escape(label)+r'\*?\s*\|\s*([0-9.]+)',text)
    assert m, label
    return float(m.group(1))


def main():
    summary=json.loads((R/'resource-summary.json').read_bytes())
    for stage,name in [('OOC_synthesis','synth'),('OOC_placed_and_routed_core','route')]:
        values=summary[stage]
        text=(R/f'{name}-utilization.rpt').read_text()
        assert 'xc7z020clg400-2' in text and '2025.2' in text
        for key,label in [('LUT','Slice LUTs'),('FF','Slice Registers'),('DSP48E1','DSPs'),
                          ('RAMB18E1','RAMB18'),('RAMB36','RAMB36/FIFO'),('BRAM_tiles','Block RAM Tile')]:
            assert values[key]==util(text,label),(stage,key)
        timing=(R/f'{name}-timing.rpt').read_text().splitlines()
        i=next(i for i,line in enumerate(timing) if 'WNS(ns)' in line)
        columns=timing[i+2].split()
        assert float(columns[0])==values['WNS_ns']
        assert float(columns[4])==values['WHS_ns']
    xci=json.loads((R/'ss_fft29.xci').read_bytes())['ip_inst']
    assert xci['component_reference']=='xilinx.com:ip:xfft:9.1' and xci['ip_revision']=='15'
    cfg=xci['parameters']['component_parameters']
    for key,value in {'input_width':'29','phase_factor_width':'24','transform_length':'1024',
                      'implementation_options':'radix_2_burst_io','rounding_modes':'convergent_rounding',
                      'output_ordering':'natural_order','scaling_options':'scaled',
                      'target_clock_frequency':'100','throttle_scheme':'nonrealtime'}.items():
        assert cfg[key][0]['value']==value, key
    print('PASS resource transcription and generated XCI config; not system timing acceptance')


if __name__=='__main__':
    main()
