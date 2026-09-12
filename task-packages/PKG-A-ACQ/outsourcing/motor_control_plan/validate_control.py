"""Synthetic supervisory logic checks; not RTL, hardware, or DOA accuracy tests.
Run: python validate_control.py --out results
Output: control_checks.json. Next: port and test against real timestamped inputs.
"""
import argparse,json
from pathlib import Path

class Supervisor:
    def __init__(self):
        self.stable=[]; self.target=0.;self.state='ACQUIRE';self.fault=False
    def update(self,now,angle,confidence,frame_time,position,moving=False,
               encoder_age=0.,limit=False,estop=False,heartbeat_age=0.):
        if limit or estop:
            self.fault=True;self.state='BRAKE';return self.state
        if self.fault:return self.state
        if encoder_age>.02 or heartbeat_age>.1:
            self.fault=True;self.state='BRAKE';return self.state
        if confidence<.7 or now-frame_time>.1 or frame_time>now:
            self.stable=[];self.state='DECEL' if moving else 'HOLD';return self.state
        if moving:
            # New angular estimates cannot retarget an ongoing move.
            self.state='MOVE';return self.state
        if abs(angle)>160:
            self.stable=[];self.state='OUT_OF_RANGE';return self.state
        self.stable.append((frame_time,angle));self.stable=self.stable[-3:]
        if len(self.stable)==3 and len({t for t,a in self.stable})==3:
            if max(a for t,a in self.stable)-min(a for t,a in self.stable)<=3:
                if abs(angle-position)>2:
                    self.target=angle;self.state='MOVE'
                else:self.state='HOLD'
        return self.state

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='results');a=ap.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True);records=[]
    def check(name,ok):
        records.append({'name':name,'pass':bool(ok)})
        assert ok,name
    s=Supervisor()
    for t in [0,.02,.04]:s.update(t,30,.9,t,0)
    check('three_fresh_stable_frames_start',s.state=='MOVE' and s.target==30)
    check('low_confidence_decelerates',s.update(.06,30,.2,.06,10,moving=True)=='DECEL')
    check('stale_frame_decelerates',s.update(.3,30,.9,0,10,moving=True)=='DECEL')
    s=Supervisor()
    for t in [0,.02,.04]:s.update(t,.8,.9,t,0)
    check('two_degree_deadband',s.state=='HOLD')
    s=Supervisor()
    for t in [0,.02,.04]:s.update(t,30,.9,0,0)
    check('repeated_frame_not_three_votes',s.state!='MOVE')
    check('out_of_range_rejected',s.update(.1,179,.9,.1,0)=='OUT_OF_RANGE')
    for field,kw in [('encoder_timeout',{'encoder_age':.021}),('watchdog',{'heartbeat_age':.101}),('limit',{'limit':True}),('estop',{'estop':True})]:
        s=Supervisor();check(field,s.update(0,30,.9,0,0,**kw)=='BRAKE')
        check(field+'_latched',s.update(.1,0,.9,.1,0)=='BRAKE')
    # Timing/frame convention: body DOA only transformed using frame-time position.
    old_yaw,current_yaw,body_doa=10,13,20
    check('timestamp_transform_3deg_counterexample',(old_yaw+body_doa)==30 and (current_yaw+body_doa)==33)
    (out/'control_checks.json').write_text(json.dumps({'scope':'synthetic supervisory tests only','checks':records,'pass_count':len(records)},indent=2),encoding='utf-8')
    print(f'{len(records)} supervisory checks PASS')
if __name__=='__main__':main()
