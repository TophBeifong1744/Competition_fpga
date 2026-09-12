"""Dual-axis selection budgets, NOT a dual-axis dynamic or hardware simulation.
Run: python size_dual_axis.py --out results-reproduced-dual-axis
Writes selection_budget.json in a NEW directory. Stdlib only.
Next: verify purchased unit's continuous torque, load inertia and brake delay.
"""
import argparse,json,math,platform,sys,itertools
from pathlib import Path
from datetime import datetime,timezone

def pitch_budget(payload,offset,inertia):
    moving_mass=payload+.2
    gravity=moving_mass*9.81*offset
    demand=inertia*math.radians(60)+gravity+.06+.03+.05
    return dict(payload_kg=payload,moving_mass_kg=moving_mass,cg_offset_m=offset,
        inertia_kg_m2=inertia,gravity_Nm=gravity,demand_Nm=demand,
        required_continuous_with_factor_2_Nm=2*demand,
        passes_1Nm_candidate=2*demand<=1)

def stop_budget(J,v_deg,assist,brake,stored_energy):
    delay=.03;v=math.radians(v_deg);v1=v+assist/J*delay
    if brake<=assist:return dict(pass_budget=False,reason='brake cannot overcome worst assisting torque')
    rigid=v*delay+.5*assist/J*delay**2+J*v1*v1/(2*(brake-assist))
    total=math.degrees(rigid+stored_energy/(brake-assist))+1.5
    return dict(J_kg_m2=J,initial_speed_deg_s=v_deg,assist_Nm=assist,
        brake_min_Nm=brake,total_delay_s=delay,stored_energy_J=stored_energy,
        rigid_travel_deg=math.degrees(rigid),travel_with_energy_and_tolerance_deg=total,
        available_deg=10,pass_budget=total<10)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    cases=[pitch_budget(m,e,j) for m,e,j in itertools.product([.05,.5,1.],[.005,.01,.02],[.003,.006,.012])]
    worst=max(cases,key=lambda x:x['demand_Nm'])
    yaw=[dict(inertia_kg_m2=j,demand_Nm=j*math.radians(90)+.06+.03+.05) for j in [.01,.025,.04]]
    stops={'yaw':stop_budget(.04,65,.14,.6,.01),
           'pitch':stop_budget(.012,35,worst['gravity_Nm']+.06+.03+.05,.8,.01)}
    negative=pitch_budget(1,.1,.012)
    weak_brake=stop_budget(.012,35,worst['gravity_Nm']+.06+.03+.05,.2,.01)
    passed=all(c['passes_1Nm_candidate'] for c in cases) and all(2*c['demand_Nm']<=1 for c in yaw)
    passed &= all(c['pass_budget'] for c in stops.values())
    passed &= not negative['passes_1Nm_candidate'] and not weak_brake['pass_budget']
    result={'scope':'analytical sizing and conservative energy budgets only; no coupled dynamics, product or hardware qualification',
        'executed_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),
        'pitch_cases':cases,'yaw_cases':yaw,'worst_pitch':worst,'stops':stops,
        'negative_offset_100mm':negative,'negative_pitch_brake_0p2Nm':weak_brake,'budget_checks_pass':bool(passed)}
    (a.out/'selection_budget.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
    print(json.dumps({k:result[k] for k in ['worst_pitch','stops','budget_checks_pass']},indent=2))
    if not passed:raise SystemExit(1)
if __name__=='__main__':main()
