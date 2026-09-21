"""Offline accepted-row semantics around frozen A functional model. NOT RTL/CDC."""
MAX_ID=(1<<64)-1
FATAL={'UPSTREAM_ERROR','QUEUE_OVERFLOW','ID_DUPLICATE','ID_REVERSE','ID_WRAP',
       'INVALID_FLAGS','INVALID_RESERVED','PCM_RANGE'}

class Adapter:
    def __init__(self,core_module,session='test'):
        self.module=core_module;self.core=core_module.Framer();self.core.start(1)
        self.session=session;self.previous=None;self.row=0;self.segment_open=False
        self.interval=-1;self.logical_by_raw={};self.rows={};self.events=[];self.frames=[];self.fault=False

    def push(self,g,queue_overflow=False):
        if self.fault or not self.core.active:raise ValueError('session not accepting; explicit new session required')
        reasons=[];previous=self.previous
        if g.integrity_error or g.source_flags:reasons.append('UPSTREAM_ERROR')
        if queue_overflow:reasons.append('QUEUE_OVERFLOW')
        if not 0<=g.sample_id<=MAX_ID:reasons.append('ID_WRAP')
        elif previous is not None:
            if previous==MAX_ID and g.sample_id==0:reasons.append('ID_WRAP')
            elif g.sample_id==previous:reasons.append('ID_DUPLICATE')
            elif g.sample_id<previous:reasons.append('ID_REVERSE')
            elif g.sample_id!=previous+1:reasons.append('DROP')
        if g.flags & ~15:reasons.append('INVALID_FLAGS')
        if g.reserved:reasons.append('INVALID_RESERVED')
        if len(g.pcm)!=4 or any(not -(1<<23)<=v<(1<<23) for v in g.pcm):reasons.append('PCM_RANGE')
        if g.flags&15:reasons.append('CLIP')
        row=self.row;self.row+=1;self.previous=g.sample_id
        if reasons:
            self.events.append(dict(row=row,id=str(g.sample_id),previous=None if previous is None else str(previous),
                reasons=reasons,raw_flags=g.flags,fatal=bool(set(reasons)&FATAL)))
            self.segment_open=False
            if set(reasons)&FATAL:
                self.fault=True;self.core.stop();return
            # Preserve raw flags; map recoverable errors into existing core's upstream event.
            from dataclasses import replace
            self.core.push(replace(g,integrity_error=True));return
        if not self.segment_open:
            self.interval+=1;self.segment_open=True
            self.logical_by_raw[self.core.interval_index]=self.interval
        self.rows[g.sample_id]=row
        before=len(self.core.frames);self.core.push(g)
        if len(self.core.frames)>before:
            f=self.core.frames[-1]
            self.frames.append(dict(session=self.session,frame_id=f.frame_index,
                raw_interval_index=f.interval_index,interval_id=self.logical_by_raw[f.interval_index],
                row_start=self.rows[f.first_id],row_stop=self.rows[f.last_id]+1,
                first_id=str(f.first_id),last_id=str(f.last_id),reset_before=f.reset_before,
                pcm=tuple(x.pcm for x in f.samples)))

    def stop(self):
        if self.core.active:self.core.stop()

def rne_shift4(value):
    if not -(1<<28)<=value<(1<<28):raise ValueError('Not S29')
    q,r=divmod(value,16)
    rounded=q+int(r>8 or (r==8 and q%2!=0))
    clipped=not -(1<<24)<=rounded<(1<<24)
    return max(-(1<<24),min((1<<24)-1,rounded)),clipped

def phat_mask(square,maximum):
    if square<0 or maximum<square:raise ValueError('Bad magnitude squares')
    return square>0 and 2500*square>=maximum

def commit_decision(*,last_id,ttl,available,session_match=True,interval_match=True,
                    control=False,fatal=False,frame_error=False,status_complete=True,already_committed=False):
    if control or fatal:return 'INVALID_AND_CLEAR_HOLD'
    if already_committed and frame_error:return 'RETROSPECTIVE_FAULT_FAIL_STOP'
    if frame_error:return 'INVALID'
    if already_committed:return 'NO_SECOND_COMMIT'
    if not session_match or not interval_match:return 'INVALID_IDENTITY'
    if ttl<0 or last_id+ttl>MAX_ID:return 'INVALID_TTL_OVERFLOW'
    if not status_complete:return 'WAIT_STATUS'
    if available is None:return 'REALTIME_ELIGIBILITY_UNKNOWN'
    if available>last_id+ttl:return 'RESULT_EXPIRED'
    return 'COMMIT_RESEARCH_ONLY'
