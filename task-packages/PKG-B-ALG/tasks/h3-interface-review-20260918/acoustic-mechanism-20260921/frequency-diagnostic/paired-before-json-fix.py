"""Common-support comparisons; never compare unpaired stability medians as gain."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    rows=json.loads(a.input.read_text());modes=list(rows[0]['variants']);report={}
    dist=lambda a,b:abs((a-b+180)%360-180)
    for group,items in [('selected_nonmarker',[r for r in rows if not r['background'] and not r['marker_excluded']]),('background',[r for r in rows if r['background']])]:
        report[group]={};items=sorted(items,key=lambda r:(r['capture'],r['start']))
        for mode in modes[1:]:
            full=[];changed=[]
            for x,y in zip(items,items[1:]):
                if x['capture']!=y['capture'] or y['start']-x['start']!=512:continue
                if all(r['variants'][k]['valid'] for r in (x,y) for k in ('full',mode)):
                    full.append(dist(x['variants']['full']['angle'],y['variants']['full']['angle']))
                    changed.append(dist(x['variants'][mode]['angle'],y['variants'][mode]['angle']))
            delta=np.array(changed)-np.array(full)
            binloss=[sum(r['variants']['full']['retained_bins'])-sum(r['variants'][mode]['retained_bins']) for r in items]
            assert all(v>=0 for v in binloss)
            report[group][mode]=dict(common_adjacent=len(full),full_jump_median=None if not full else float(np.median(full)),variant_jump_median=None if not full else float(np.median(changed)),delta_median=None if not full else float(np.median(delta)),improved=sum(v<0 for v in delta),worsened=sum(v>0 for v in delta),unchanged=sum(v==0 for v in delta),frames_with_removed_retained_bins=sum(v>0 for v in binloss),total_frames=len(items),pair_bin_shortfalls=sum(reason=='FEWER_THAN_12_BINS' for r in items for reason in r['variants'][mode]['pair_reasons']))
    result=dict(input_sha256=hashlib.sha256(a.input.read_bytes()).hexdigest(),groups=report,scope='common support diagnostic; no target truth or selection of winner')
    (a.out/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(report['selected_nonmarker'],indent=2))
if __name__=='__main__':main()
