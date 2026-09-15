#include "continuous_core.h"
#include <string.h>
const char *failure_name(enum failure f) {
    static const char *const names[]={"OK","ABI","SOURCE_ERROR","DMA_ERROR","DMA_TIMEOUT",
        "PACKET_TIMEOUT","STOP_TIMEOUT","OWNERSHIP","ARM_ERROR","LENGTH_ERROR","GUARD_ERROR",
        "ID_ERROR","RANGE_ERROR","FLAGS_ERROR","COUNTER_ERROR","START_STATE"};
    return (unsigned)f<sizeof(names)/sizeof(names[0]) ? names[f] : "UNKNOWN";
}
void session_init(struct session *s) {
    memset(s,0,sizeof(*s)); s->active=-1;
    for(unsigned c=0;c<4;c++){s->minimum[c]=8388607;s->maximum[c]=-8388608;}
}
static enum failure check_packet(struct session *s,const uint32_t *p) {
    for(unsigned i=PACKET_BYTES/4;i<SLOT_STRIDE/4;i++) {
        if(p[i]!=SENTINEL){s->bad_value=p[i];return GUARD_ERROR;}
    }
    for(unsigned g=0;g<GROUPS_PER_PACKET;g++) {
        const uint32_t *w=p+g*WORDS_PER_GROUP;
        uint64_t id=((uint64_t)w[1]<<32)|w[0];
        s->bad_group=g;s->bad_lane=0;s->bad_value=w[0];
        if(s->have_id && (s->last_id==UINT64_MAX || id!=s->last_id+1U)) return ID_ERROR;
        if(!s->have_id){s->first_id=id;s->have_id=1;}
        s->last_id=id;s->bad_value=w[6];
        if((w[6]&~15U)||w[7]) return FLAGS_ERROR;
        for(unsigned c=0;c<4;c++) {
            int32_t v=(int32_t)w[c+2];s->bad_lane=c;s->bad_value=w[c+2];
            if(v < -8388608 || v > 8388607) return RANGE_ERROR;
            if(v<s->minimum[c])s->minimum[c]=v;
            if(v>s->maximum[c])s->maximum[c]=v;
            if(!v)s->zeros[c]++;
            if(w[6]&(1U<<c))s->clips[c]++;
        }
    }
    if(s->groups>UINT32_MAX-GROUPS_PER_PACKET || s->packets==UINT32_MAX)return COUNTER_ERROR;
    s->groups+=GROUPS_PER_PACKET;s->packets++;
    return OK;
}
enum failure session_run(struct session *s,const struct io *io) {
    uint64_t now;
    if(s->failed)return s->failed; // A failed state cannot silently be reused.
    s->last_source=io->source(io->ctx);
    if((s->last_source&0xff000000U)!=SOURCE_SIGNATURE){s->failed=ABI;return ABI;}
    if((s->last_source&(SOURCE_FATAL|SOURCE_REJECTED|0xc1U)) || !(s->last_source&2U)) {
        s->failed=START_STATE;return START_STATE;
    }
    for(unsigned i=0;i<SLOT_COUNT;i++)if(s->owner[i]!=FREE){s->failed=OWNERSHIP;return OWNERSHIP;}
    s->start_us=s->last_progress=io->time_us(io->ctx);
    io->run(io->ctx,1);
    for(;;) {
        now=io->time_us(io->ctx);
        s->last_source=io->source(io->ctx); s->last_sr=io->dma_status(io->ctx);
        if((s->last_source&0xff000000U)!=SOURCE_SIGNATURE){s->failed=ABI;break;}
        if(s->last_source&(SOURCE_FATAL|SOURCE_REJECTED)){s->failed=SOURCE_ERROR;break;}
        if(s->last_sr&DMA_ERRORS){s->failed=DMA_ERROR;break;}
        if(!s->stop_sent && now-s->start_us>=RUN_US && s->groups>=MIN_GROUPS) {
            io->run(io->ctx,0); s->stop_sent=1;s->stop_us=now;
        }
        if(s->active>=0) {
            if((s->last_sr&DMA_DONE)==DMA_DONE) {
                unsigned a=(unsigned)s->active;
                s->last_length=io->dma_length(io->ctx);
                if(s->owner[a]!=DMA_OWNED){s->failed=OWNERSHIP;break;}
                if(s->last_length!=PACKET_BYTES){s->failed=LENGTH_ERROR;break;}
                struct trace *t=&s->recent[s->trace_count++%16];
                t->packet=s->packets;t->slot=a;t->sr=s->last_sr;t->source=s->last_source;t->length=s->last_length;
                s->owner[a]=CPU_READY;s->active=-1;s->last_progress=now;
            } else if(now-s->armed_us>=TIMEOUT_US){s->failed=DMA_TIMEOUT;break;}
        }
        // Re-read AFTER observing completion; the earlier value may include the
        // packet that just completed. Never arm using that stale credit.
        s->last_source=io->source(io->ctx);
        // Complete-packet gate prevents a spurious final DMA from waiting forever.
        if(s->active<0 && (s->last_source&0x40U)) {
            unsigned a=s->next_slot;
            if(s->owner[a]!=FREE){s->failed=OWNERSHIP;break;}
            io->prepare(io->ctx,a); // CPU-owned until flush+invalidate completes.
            s->owner[a]=DMA_OWNED;
            if(io->arm(io->ctx,a,PACKET_BYTES)){s->failed=ARM_ERROR;break;}
            s->active=(int)a;s->next_slot=a^1U;s->armed_us=io->time_us(io->ctx);
            uint64_t gap=s->armed_us-s->last_progress;
            if(gap>s->max_arm_gap_us)s->max_arm_gap_us=gap;
        }
        for(unsigned a=0;a<SLOT_COUNT;a++)if(s->owner[a]==CPU_READY) {
            uint64_t t=io->time_us(io->ctx);s->owner[a]=CPU_OWNED;
            const uint32_t *p=io->acquire(io->ctx,a); // invalidate AFTER completed DMA only.
            s->failed=check_packet(s,p);
            uint64_t dt=io->time_us(io->ctx)-t;
            if(dt>s->max_check_us)s->max_check_us=dt;
            if(s->failed)goto failed;
            s->owner[a]=FREE; // data may now be recycled, never before validation.
        }
        // Refresh status: draining can finish while CPU validates the final slot.
        s->last_source=io->source(io->ctx);
        if(s->last_source&(SOURCE_FATAL|SOURCE_REJECTED)){s->failed=SOURCE_ERROR;break;}
        if(s->stop_sent && (s->last_source&8U) && !(s->last_source&0xc1U) && s->active<0) {
            s->end_us=io->time_us(io->ctx);return OK;
        }
        if(s->stop_sent && now-s->stop_us>=TIMEOUT_US){s->failed=STOP_TIMEOUT;break;}
        if(s->active<0 && now-s->last_progress>=TIMEOUT_US){s->failed=PACKET_TIMEOUT;break;}
    }
failed:
    // Registers + owners + recent completion history remain intact for the caller.
    io->run(io->ctx,0);s->end_us=io->time_us(io->ctx);return s->failed;
}
