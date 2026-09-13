"""Make per-pair diagnostic statistics and explicit disagreement ledger."""
import json
import numpy as np
import run as model

def main():
    output=[]
    for path in sorted((model.HERE/'evidence/run02').glob('*-frames.json')):
        frames=json.loads(path.read_text())
        pairs=[]; disagreements=[]
        for k,pair in enumerate(model.PAIRS):
            stats=dict(pair=pair)
            for branch in ['floating','reference25']:
                rows=[f[branch][k] for f in frames]
                valid=[r for r in rows if r['valid']]
                stats[branch]=dict(valid=len(valid),
                    delay_median=float(np.median([r['tau_samples'] for r in valid])) if valid else None,
                    edge_peaks=sum(r.get('edge_peak',False) for r in rows),
                    median_peak_margin=float(np.median([r['separated_peak_margin'] for r in valid])) if valid else None,
                    global_peak_outside_bound=sum(abs(r.get('global_peak_lag',0)) > r.get('bound_samples',1024) for r in rows))
            pairs.append(stats)
        for f in frames:
            for k,(a,b) in enumerate(zip(f['floating'],f['reference25'])):
                if a['valid']!=b['valid'] or (a['valid'] and b['valid'] and a['peak']!=b['peak']):
                    disagreements.append(dict(row_start=f['row_start'],pair=model.PAIRS[k],floating=a,reference25=b))
        output.append(dict(recording=path.name,pairs=pairs,disagreements=disagreements))
    destination=model.HERE/'evidence/analysis.json'
    if destination.exists(): raise FileExistsError(destination)
    model.dump(destination,output)
    for r in output:
        print(r['recording'])
        for p in r['pairs']: print(p)

if __name__=='__main__': main()
