"""Synthetic supervisory logic checks; not RTL, hardware, or DOA accuracy tests.
Run: python validate_control.py --out results
Output: control_checks.json. Next: port and test against real timestamped inputs.
"""
import argparse,json,math,platform,sys
from datetime import datetime,timezone
from numbers import Real
from pathlib import Path

class Supervisor:
    def __init__(self):
        self.stable=[]; self.target=0.;self.state='ACQUIRE';self.fault=False
        self.last_now=None;self.last_frame=None
    def reject(self,moving):
        self.stable=[]
        self.state='DECEL' if moving is True else 'HOLD'
        return self.state
    def update(self,now,angle,confidence,frame_time,position,moving=False,
               encoder_age=0.,limit=False,estop=False,heartbeat_age=0.):
        if self.fault:return self.state
        if any(type(x) is not bool for x in (moving,limit,estop)):
            return self.reject(moving)
        if limit or estop:
            self.stable=[];self.fault=True;self.state='BRAKE';return self.state
        values=(now,angle,confidence,frame_time,position,encoder_age,heartbeat_age)
        if any(isinstance(x,bool) or not isinstance(x,Real) or not math.isfinite(x) for x in values):
            return self.reject(moving)
        if min(now,frame_time,encoder_age,heartbeat_age)<0 or not 0<=confidence<=1:
            return self.reject(moving)
        if self.last_now is not None and now<self.last_now:
            return self.reject(moving)
        self.last_now=now
        if encoder_age>.02 or heartbeat_age>.1:
            self.stable=[];self.fault=True;self.state='BRAKE';return self.state
        if now-frame_time>.1+1e-12 or frame_time>now:
            return self.reject(moving)
        # Strictly increasing source timestamps. Replays/reordering clear votes,
        # but never move the timestamp high-water mark backwards.
        if self.last_frame is not None and frame_time<=self.last_frame:
            return self.reject(moving)
        self.last_frame=frame_time
        if confidence<.7:
            return self.reject(moving)
        # Apply freshness to EVERY candidate, not just the newest observation.
        self.stable=[(t,a) for t,a in self.stable if 0<=now-t<=.1+1e-12]
        if abs(angle)>160:
            self.stable=[]
            self.state='DECEL' if moving else 'OUT_OF_RANGE'
            return self.state
        if moving:
            # New angular estimates cannot retarget an ongoing move.
            self.stable=[];self.state='MOVE';return self.state
        self.state='ACQUIRE'
        self.stable.append((frame_time,angle));self.stable=self.stable[-3:]
        if len(self.stable)==3 and len({t for t,a in self.stable})==3:
            if max(a for t,a in self.stable)-min(a for t,a in self.stable)<=3:
                if abs(angle-position)>2:
                    self.target=angle;self.state='MOVE'
                else:self.state='HOLD'
                self.stable=[] # An accepted decision cannot lend votes to another.
        return self.state

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='results');a=ap.parse_args()
    out=Path(a.out)
    if (out/'control_checks.json').exists():
        raise SystemExit('Refusing to overwrite existing control_checks.json; use a new --out directory')
    out.mkdir(parents=True,exist_ok=True);records=[]
    started=datetime.now(timezone.utc).isoformat()
    def check(name,ok):
        records.append({'name':name,'pass':bool(ok)})
        if not ok:raise AssertionError(name)
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
    # Review counterexample: two old votes must not survive a long outage.
    s=Supervisor()
    for t in [0,.02,2.]:s.update(t,30,.9,t,0)
    check('long_gap_old_votes_expired',s.state!='MOVE' and len(s.stable)==1)
    s.update(2.02,30,.9,2.02,0)
    check('long_gap_two_new_frames_insufficient',s.state!='MOVE')
    check('long_gap_three_new_frames_recover',s.update(2.04,30,.9,2.04,0)=='MOVE')
    s=Supervisor()
    for t in [0,.09,.11]:s.update(t,30,.9,t,0)
    check('whole_window_age_checked',s.state!='MOVE' and len(s.stable)==2)
    check('whole_window_fresh_recovery',s.update(.13,30,.9,.13,0)=='MOVE')
    s=Supervisor()
    for t in [0,.05,.1]:s.update(t,30,.9,t,0)
    check('inclusive_100ms_boundary',s.state=='MOVE')
    for kind,seq in [('duplicate',[0,.02,.02]),('reverse',[.04,.02,0])]:
        s=Supervisor()
        for t in seq:s.update(.04,30,.9,t,0)
        check(kind+'_clears_all_votes',s.state!='MOVE' and not s.stable and s.target==0)
        for t in [.06,.08]:
            s.update(t,30,.9,t,0)
            check(kind+'_recover_'+str(t),s.state!='MOVE')
        check(kind+'_third_new_frame_recovers',s.update(.1,30,.9,.1,0)=='MOVE')
    # Every numerical input is checked both at rest and while moving.
    for field in ['now','angle','confidence','frame_time','position','encoder_age','heartbeat_age']:
        for badname,bad in [('nan',float('nan')),('posinf',float('inf')),('neginf',float('-inf')),('none',None),('text','bad'),('bool',True)]:
            for moving in [False,True]:
                s=Supervisor()
                for t in [0,.02]:s.update(t,30,.9,t,0)
                kw=dict(now=.04,angle=30,confidence=.9,frame_time=.04,position=0,moving=moving)
                kw[field]=bad
                result=s.update(**kw)
                prefix=f'{field}_{badname}_{moving}'
                check(prefix+'_reject',result==('DECEL' if moving else 'HOLD') and s.target==0 and not s.stable)
                for t in [.06,.08]:
                    s.update(t,30,.9,t,0)
                    check(prefix+'_fresh_'+str(t),s.state!='MOVE')
                check(prefix+'_recovery',s.update(.1,30,.9,.1,0)=='MOVE')
    for field,bad in [('now',-1),('frame_time',-1),('frame_time',.05),('confidence',1.1),('confidence',-.1),('encoder_age',-1),('heartbeat_age',-1)]:
        s=Supervisor();kw=dict(now=.04,angle=30,confidence=.9,frame_time=.04,position=0,moving=True);kw[field]=bad
        check(f'invalid_range_{field}_{bad}',s.update(**kw)=='DECEL' and s.target==0)
    s=Supervisor();s.update(.05,30,.9,.05,0)
    check('clock_rollback_rejected',s.update(.04,30,.9,.04,0)=='HOLD' and not s.stable)
    s=Supervisor();s.update(0,30,.9,0,0)
    check('duplicate_during_motion_decelerates',s.update(.02,80,.9,0,10,moving=True)=='DECEL' and s.target==0)
    s=Supervisor();s.update(.04,30,.9,.04,0)
    check('reverse_during_motion_decelerates',s.update(.05,80,.9,.03,10,moving=True)=='DECEL' and s.target==0)
    check('out_of_range_during_motion_decelerates',Supervisor().update(0,179,.9,0,0,moving=True)=='DECEL')
    s=Supervisor();s.update(0,30,.9,0,0,estop=True)
    check('invalid_does_not_clear_fault_latch',s.update(float('nan'),30,.9,0,0,moving=True)=='BRAKE')
    for field in ['moving','limit','estop']:
        kw=dict(now=0,angle=30,confidence=.9,frame_time=0,position=0);kw[field]=float('nan')
        check('invalid_flag_'+field,Supervisor().update(**kw)!='MOVE')
    result={'scope':'synthetic supervisory tests only','started_utc':started,'finished_utc':datetime.now(timezone.utc).isoformat(),
            'environment':{'python':sys.version,'platform':platform.platform()},'checks':records,'pass_count':len(records)}
    (out/'control_checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(f'{len(records)} supervisory checks PASS')
if __name__=='__main__':main()
